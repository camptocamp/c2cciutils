# -*- coding: utf-8 -*-

import json
import os.path
import pkgutil
import re
import subprocess
import sys
from typing import Any, Dict, List, Match, Optional, Pattern, Tuple, TypedDict, cast

import jsonschema_gentypes.validate
import magic
import requests
import ruamel.yaml

import c2cciutils.configuration


def get_repository() -> str:
    """
    Get the current GitHub repository like `organisation/project`
    """

    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]

    remote_lines = subprocess.check_output(["git", "remote", "--verbose"]).decode().split("\n")
    remote_match = (
        re.match(r".*git@github.com:(.*).git .*", remote_lines[0]) if len(remote_lines) >= 1 else None
    )

    if remote_match:
        return remote_match.group(1)

    print("WARNING: the GitHub repository isn't found, using 'camptocamp/project'")

    return "camptocamp/project"


def merge(default_config: Any, config: Any) -> Any:
    """
    Deep merge the dictionaries (on dictionaries only, not on arrays).
    """

    if not isinstance(default_config, dict) or not isinstance(config, dict):
        return config

    for key in default_config.keys():
        if key not in config:
            config[key] = default_config[key]
        else:
            merge(default_config[key], config[key])
    return config


def get_config() -> c2cciutils.configuration.Configuration:
    docker = False
    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(filename) == "Dockerfile":
            docker = True
            break

    config: c2cciutils.configuration.Configuration = {}
    if os.path.exists("ci/config.yaml"):
        with open("ci/config.yaml") as open_file:
            yaml_ = ruamel.yaml.YAML()  # type: ignore
            config = yaml_.load(open_file)

    editorconfig_properties = {
        "end_of_line": "lf",
        "insert_final_newline": "true",
        "charset": "utf-8",
        "indent_style": "space",
        "trim_trailing_whitespace": "true",
        "max_line_length": "110",
        "quote_type": "single",
    }
    editorconfig_properties_2 = dict(editorconfig_properties)
    editorconfig_properties_4 = dict(editorconfig_properties)
    editorconfig_properties_2["indent_size"] = "2"
    editorconfig_properties_4["indent_size"] = "4"
    editorconfig_properties_mk = dict(editorconfig_properties_4)
    editorconfig_properties_mk["indent_style"] = "tab"
    editorconfig_full_properties = {
        "*.py": editorconfig_properties_4,
        "*.yaml": editorconfig_properties_2,
        "*.yml": editorconfig_properties_2,
        "*.graphql": editorconfig_properties_2,
        "*.json": editorconfig_properties,
        "*.java": editorconfig_properties_4,
        "*.js": editorconfig_properties_2,
        "*.mk": editorconfig_properties_mk,
        "Makefile": editorconfig_properties_mk,
        "*.css": editorconfig_properties_2,
        "*.scss": editorconfig_properties_2,
        "*.html": editorconfig_properties_2,
    }

    repository = get_repository()
    repo = repository.split("/")
    default_branch_json = graphql(
        "default_branch.graphql", {"name": repo[1], "owner": repo[0]}, default=False
    )
    credentials = default_branch_json is not False
    master_branch = default_branch_json["repository"]["defaultBranchRef"]["name"] if credentials else "master"

    merge(
        {
            "version": {
                "tag_to_version_re": [
                    {"from": r"([0-9]+.[0-9]+.[0-9]+)", "to": r"\1"},
                ],
                "branch_to_version_re": [
                    {"from": r"([0-9]+.[0-9]+)", "to": r"\1"},
                    {"from": master_branch, "to": master_branch},
                ],
            }
        },
        config,
    )

    based_on_master = get_based_on_master(repo, master_branch, config) if credentials else False

    default_config = {
        "publish": {
            "print_versions": {
                "versions": [
                    {"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]},
                    {"name": "python", "cmd": ["python3", "--version"]},
                    {"name": "twine", "cmd": ["twine", "--version"]},
                    {"name": "docker", "cmd": ["docker", "--version"]},
                ]
            },
            "pypi": {"versions": ["version_tag"], "packages": [{"path": "."}]},
            "docker": {
                "images": [{"name": get_repository()}],
                "repository": {
                    "github": {
                        "server": "ghcr.io",
                        "versions": ["version_tag", "version_branch", "rebuild"],
                    },
                    "dockerhub": {"versions": ["version_tag", "version_branch", "rebuild", "feature_branch"]},
                },
            },
            "publish": {"google_calendar": {"on": ["version_branch", "version_tag", "rebuild"]}},
        },
        "checks": {
            "print_versions": {
                "versions": [
                    {"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]},
                    {"name": "codespell", "cmd": ["codespell", "--version"], "prefix": "codespell "},
                    {"name": "java", "cmd": ["java", "-version"]},
                    {"name": "python", "cmd": ["python3", "--version"]},
                    {"name": "pip", "cmd": ["python3", "-m", "pip", "--version"]},
                    {"name": "pipenv", "cmd": ["pipenv", "--version"]},
                    {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]},
                    {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]},
                    {"name": "docker", "cmd": ["docker", "--version"]},
                    {"name": "docker-compose", "cmd": ["docker-compose", "--version"]},
                ]
            },
            "print_config": True,
            "print_environment_variables": True,
            "print_github_event": True,
            "black_config": {"propertires": {"line-length": 110}},
            "editorconfig": {
                "properties": editorconfig_full_properties,
            },
            "gitattribute": True,
            "eof": True,
            "workflows": {"images_blacklist": ["ubuntu-latest"] if based_on_master else [], "timeout": True},
            "required_workflows": {
                "main.yaml": {"if": "!startsWith(github.event.head_commit.message, '[skip ci] ')"},
                "codeql.yaml": True,
                **(
                    {
                        "backport.yaml": True,
                        "dependabot-auto-merge.yaml": {"on": {"workflow_run": {"types": ["completed"]}}}
                        if config.get("checks", {}).get("dependabot_config", True)
                        else False,
                    }
                    if based_on_master
                    else {}
                ),
            },
            "versions": {
                "extra_versions": [master_branch],
                "backport_labels": True,
                "rebuild": {
                    "files": [f for f in os.listdir(".github/workflows") if re.match(r"rebuild.*\.yaml", f)]
                },
                "audit": True,
                "branches": True,
            }
            if based_on_master
            else False,
            "black": {"ignore_patterns_re": []},
            "isort": {"ignore_patterns_re": []},
            "codespell": {
                "ignore_re": [],
                "arguments": ["--quiet-level=2", "--check-filenames"],
            },
            "dependabot_config": {
                "ignore_version_files": [],
                "update_ignore": [],
                "types": [
                    {"filename": "Pipfile", "ecosystem": "pip"},
                    {"filename": "Dockerfile", "ecosystem": "docker"},
                    {"filename": "package.json", "ecosystem": "npm"},
                ],
            }
            if based_on_master
            else False,
            "setup": {
                "cfg": {
                    "mypy": {"warn_redundant_casts": "True", "warn_unused_ignores": "True", "strict": "True"}
                },
                "classifiers": ["Typing :: Typed"],
            },
        },
        "audit": {
            "print_versions": {
                "versions": [
                    {"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]},
                    {"name": "python", "cmd": ["python3", "--version"]},
                    {"name": "safety", "cmd": ["safety", "--version"]},
                    {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]},
                    {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]},
                ]
            },
            "pip": True,
            "pipfile": {"sections": ["default", "develop"]},
            "pipfile_lock": {"sections": ["default"]},
            "pipenv": False,
            "npm": {"cwe_ignore": []},
            "outdated_versions": True,
        },
    }
    merge(default_config, config)

    check_version_config = cast(
        c2cciutils.configuration.ChecksVersionsConfig,
        config["checks"]["versions"] if config["checks"].get("versions", False) else {},
    )
    check_version_config_rebuild = cast(
        c2cciutils.configuration.ChecksVersionsRebuild,
        check_version_config["rebuild"] if check_version_config.get("rebuild", False) else {},
    )

    if docker:
        if isinstance(config.get("checks", {}).get("required_workflows", {}), dict):
            merge(
                {
                    "clean.yaml": {"steps": [{"run_re": "c2cciutils-clean$"}]},
                    "audit.yaml": {
                        "steps": [{"run_re": "c2cciutils-audit --branch=.*$", "env": ["GITHUB_TOKEN"]}],
                        "strategy-fail-fast": False,
                    },
                },
                config.get("checks", {}).get("required_workflows", {}),
            )
    elif len(check_version_config_rebuild.get("files", [])) == 0:
        assert isinstance(config["checks"]["versions"], dict)
        config["checks"]["versions"]["rebuild"] = False
        check_version_config_rebuild = {}

    if check_version_config.get("rebuild", False):
        required_workflows = {
            rebuild: {
                "noif": True,
                "steps": [{"run_re": r"^c2cciutils-publish .*--type.*$"}],
                "strategy-fail-fast": False,
            }
            for rebuild in check_version_config_rebuild.get("files", ["rebuild.yaml"])
        }
        merge(required_workflows, config["checks"]["required_workflows"])

    if config["publish"].get("docker", False):
        assert isinstance(config["publish"]["docker"], dict)
        for image in config["publish"]["docker"]["images"]:
            merge(
                {
                    "tags": ["{version}"],
                    "group": "default",
                },
                image,
            )
    if config["publish"].get("pypi", False):
        assert isinstance(config["publish"]["pypi"], dict)
        for package in config["publish"]["pypi"]["packages"]:
            merge(
                {
                    "group": "default",
                },
                package,
            )

    return validate_config(config, "ci/config.yaml")


def validate_config(
    config: c2cciutils.configuration.Configuration, config_file: str
) -> c2cciutils.configuration.Configuration:
    schema_data = pkgutil.get_data("c2cciutils", "schema.json")
    assert schema_data is not None

    errors, data = jsonschema_gentypes.validate.validate(
        config_file, cast(Dict[str, Any], config), json.loads(schema_data)
    )

    if errors:
        print("The config file is invalid:\n{}".format("\n".join(errors)))
        if os.environ.get("IGNORE_CONFIG_ERROR", "FALSE").lower() != "true":
            sys.exit(1)

    return cast(c2cciutils.configuration.Configuration, data)


def error(
    checker: str,
    message: str,
    file: Optional[str] = None,
    line: Optional[int] = None,
    col: Optional[int] = None,
    error_type: str = "error",
) -> None:
    """
    Write an error or warn message formatted for GitHub if the CI environment variable is true else for IDE.

    GitHub: ::(error|warning) file=<file>,line=<line>,col=<col>:: <checker>: <message>
    IDE: [(error|warning)] <file>:<line>:<col>: <checker>: <message>

    See: https://docs.github.com/en/free-pro-team@latest/actions/reference/ \
        workflow-commands-for-github-actions#setting-an-error-message
    """
    result = ""
    on_ci = os.environ.get("CI", "false").lower() == "true"
    if file is not None:
        result += ("file={}" if on_ci else "{}").format(file)
        if line is not None:
            result += (",line={}" if on_ci else ":{}").format(line)
            if col is not None:
                result += (",col={}" if on_ci else ":{}").format(col)
    result += (":: {}: {}" if on_ci else ": {}: {}").format(checker, message)
    if on_ci:
        # Make the error visible on GitHub workflow logs
        print(result)
        # Make the error visible as annotation
        print("::{} {}".format(error_type, result))
    else:
        print("[{}] {}".format(error_type, result))


VersionTransform = TypedDict(
    "VersionTransform",
    {
        # The from regular expression
        "from": Pattern[str],
        # The expand regular expression: https://docs.python.org/3/library/re.html#re.Match.expand
        "to": str,
    },
    total=False,
)


def compile_re(config: c2cciutils.configuration.VersionTransform, prefix: str = "") -> List[VersionTransform]:
    """
    Compile the from as a regular expression of a dictionary of the config list.

    to be used with convert and match
    """
    result = []
    for conf in config:
        new_conf = cast(VersionTransform, dict(conf))

        from_re = conf.get("from", r"(.*)")
        if from_re[0] == "^":
            from_re = from_re[1:]
        if from_re[-1] != "$":
            from_re += "$"
        from_re = "^{}{}".format(re.escape(prefix), from_re)

        new_conf["from"] = re.compile(from_re)
        result.append(new_conf)
    return result


def match(
    value: str, config: List[VersionTransform]
) -> Tuple[Optional[Match[str]], Optional[VersionTransform], str]:
    """
    `value` is what we want to match with
    `config` is the result of `compile`

    Returns the re match object, the matched config and the value as a tuple
    On no match it returns None, value
    """
    for conf in config:
        matched = conf["from"].match(value)
        if matched is not None:
            return matched, conf, value
    return None, None, value


def get_value(matched: Optional[Match[str]], config: Optional[VersionTransform], value: str) -> str:
    """
    Get the final value

    `match`, `config` and `value` are the result of `match`.

    The `config` should have a `to` ad a expand template.
    """
    assert config
    return matched.expand(config.get("to", r"\1")) if matched is not None else value


def print_versions(config: c2cciutils.configuration.PrintVersions) -> bool:
    """
    Print some tools version
    """

    for version in config.get("versions", []):
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            current_version = subprocess.check_output(version.get("cmd", [])).decode()
            print("{}{}".format(version.get("prefix", ""), current_version))
        except PermissionError as exception:
            print("{}: not allowed cmd: {}".format(version.get("name"), exception))
        except subprocess.CalledProcessError as exception:
            print("{}: no present: ".format(version.get("name")), exception)

    return True


def gopass(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        return subprocess.check_output(["gopass", "show", key]).strip().decode()
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def gopass_put(secret: str, key: str) -> None:
    subprocess.check_output(["gopass", "insert", "--force", key], input=secret.encode())


def add_authorization_header(headers: Dict[str, str]) -> Dict[str, str]:
    try:
        headers["Authorization"] = "Bearer {}".format(
            os.environ["GITHUB_TOKEN"].strip()
            if "GITHUB_TOKEN" in os.environ
            else gopass("gs/ci/github/token/gopass")
        )
        return headers
    except FileNotFoundError:
        return headers


def graphql(query_file: str, variables: Dict[str, Any], default: Any = None) -> Any:
    """
    Get the result a a graphql on GitHub

    query_file: the file related this module contains the GraphQL querry
    variables: the query variables

    Return the data result
    In case of error it throw an exception
    """

    with open(os.path.join(os.path.dirname(__file__), query_file)) as query_open:
        query = query_open.read()

    http_response = requests.post(
        os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"),
        data=json.dumps(
            {
                "query": query,
                "variables": variables,
            }
        ),
        headers=add_authorization_header(
            {
                "Content-Type": "application/json",
            }
        ),
    )
    if http_response.status_code == 401 and default is not None:
        return default
    http_response.raise_for_status()
    json_response = http_response.json()

    if "errors" in json_response:
        raise RuntimeError("GraphQL error: {}".format(json.dumps(json_response["errors"], indent=2)))
    if "data" not in json_response:
        raise RuntimeError("GraphQL no data: {}".format(json.dumps(json_response, indent=2)))
    return cast(Dict[str, Any], json_response["data"])


def get_git_files_mime(
    mime_type: str = "text/x-python", ignore_patterns_re: Optional[List[str]] = None
) -> List[str]:
    """
    Get all the files in git that have the specified mime type

    ignore_patterns_re: list of regular expression to be ignored
    """

    ignore_patterns_compiled = [re.compile(p) for p in ignore_patterns_re or []]
    result = []

    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.isfile(filename) and magic.from_file(filename, mime=True) == mime_type:  # type: ignore
            accept = True
            for pattern in ignore_patterns_compiled:
                if pattern.search(filename):
                    accept = False
                    break
            if accept:
                result.append(filename)
    return result


def get_based_on_master(
    repo: List[str], master_branch: str, config: c2cciutils.configuration.Configuration
) -> bool:
    """
    Check that we are not on a release branch (to avoid errors in versions check).

    This function will check the last 20 commits in current branch,
    and for each other branch (max 50) check if any commit in last 10 commits is the current one.
    """

    if os.environ.get("GITHUB_REF", "").startswith("refs/tags/"):
        # The tags are never consider as based on master
        return False
    if os.environ.get("GITHUB_REF", "").startswith("refs/heads/"):
        current_branch = os.environ["GITHUB_REF"][len("refs/heads/") :]
        if current_branch == master_branch:
            return True
        branches_re = compile_re(config["version"].get("branch_to_version_re", []), "refs/heads/")
        if match(current_branch, branches_re):
            return False
        commits_json = graphql(
            "commits.graphql", {"name": repo[1], "owner": repo[0], "branch": current_branch}
        )["repository"]["ref"]["target"]["history"]["nodes"]
        branches_json = [
            branch
            for branch in (
                graphql("branches.graphql", {"name": repo[1], "owner": repo[0]})["repository"]["refs"][
                    "nodes"
                ]
            )
            if branch["name"] != current_branch and match(branch["name"], branches_re)
        ]
        based_branch = master_branch
        found = False
        for commit in commits_json:
            for branch in branches_json:
                commits = [
                    branch_commit
                    for branch_commit in branch["target"]["history"]["nodes"]
                    if commit["oid"] == branch_commit["oid"]
                ]
                if commits:
                    based_branch = branch["name"]
                    found = True
                    break
            if found:
                break
        return based_branch == master_branch
    return True
