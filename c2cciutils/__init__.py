# -*- coding: utf-8 -*-

import json
import os.path
import re
import subprocess

import magic
import requests
import yaml


def get_repository():
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


def merge(default_config, config):
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


def get_config():
    docker = False
    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(filename) == "Dockerfile":
            docker = True
            break

    config = {}
    if os.path.exists("ci/config.yaml"):
        with open("ci/config.yaml") as open_file:
            config = yaml.load(open_file, yaml.SafeLoader)

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
    json_response = graphql("default_branch.graphql", {"name": repo[1], "owner": repo[0]}, default=False)
    master_branch = json_response["repository"]["defaultBranchRef"]["name"] if json_response else "master"

    default_config = {
        "version": {
            "tag_to_version_re": [
                {"from": r"([0-9]+.[0-9]+.[0-9]+)", "to": r"\1"},
            ],
            "branch_to_version_re": [
                {"from": r"([0-9]+.[0-9]+)", "to": r"\1"},
                {"from": master_branch, "to": master_branch},
            ],
        },
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
            "black_config": {"propertires": {"line-length": 110}},
            "editorconfig": {
                "properties": editorconfig_full_properties,
            },
            "gitattribute": True,
            "eof": True,
            "workflows": {"images_blacklist": ["ubuntu-latest"], "timeout": True},
            "required_workflows": {
                "main.yaml": {"if": "!startsWith(github.event.head_commit.message, '[skip ci] ')"},
                "backport.yaml": True,
                "codeql.yaml": True,
                "dependabot-auto-merge.yaml": {"on": {"workflow_run": {"types": ["completed"]}}}
                if config.get("dependabot_config", True)
                else False,
            },
            "versions": {
                "extra_versions": [master_branch],
                "backport_labels": True,
                "rebuild": {
                    "files": [f for f in os.listdir(".github/workflows") if re.match(r"rebuild.*\.yaml", f)]
                },
                "audit": True,
                "branches": True,
            },
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
            "pipenv": {"python_versions": []},
            "npm": {"cwe_ignore": []},
            "outdated_versions": True,
        },
    }
    merge(default_config, config)

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
    elif (
        config["checks"]["versions"]
        and config["checks"]["versions"].get("rebuild", False)
        and len(config["checks"]["versions"]["rebuild"].get("files", [])) == 0
    ):
        config["checks"]["versions"]["rebuild"] = False

    if config["checks"].get("versions", False) and config["checks"]["versions"].get("rebuild", False):
        required_workflows = {
            rebuild: {
                "noif": True,
                "steps": [{"run_re": r"^c2cciutils-publish .*--type.*$"}],
                "strategy-fail-fast": False,
            }
            for rebuild in config["checks"]["versions"]["rebuild"].get("files", ["rebuild.yaml"])
        }
        merge(required_workflows, config["checks"]["required_workflows"])

    for image in config["publish"]["docker"]["images"]:
        merge(
            {
                "tags": ["{version}"],
                "group": "default",
            },
            image,
        )
    for package in config["publish"]["pypi"]["packages"]:
        merge(
            {
                "group": "default",
            },
            package,
        )

    return config


def compile_re(config, prefix=""):
    """
    Compile the from as a regular expression of a dictionary of the config list.

    to be used with convert and match
    """
    result = []
    for conf in config:
        new_conf = dict(conf)

        from_re = conf.get("from", r"(.*)")
        if from_re[0] == "^":
            from_re = from_re[1:]
        if from_re[-1] != "$":
            from_re += "$"
        from_re = "^{}{}".format(re.escape(prefix), from_re)

        new_conf["from"] = re.compile(from_re)
        result.append(new_conf)
    return result


def match(value, config):
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


def get_value(matched, config, value):
    """
    Get the final value

    `match`, `config` and `value` are the result of `match`.

    The `config` should have a `to` ad a expand template.
    """
    return matched.expand(config.get("to", r"\1")) if matched is not None else value


def print_versions(config):
    """
    Print some tools version
    """

    for version in config.get("versions", []):
        try:
            current_version = subprocess.check_output(version.get("cmd", [])).decode()
            print("{}{}".format(version.get("prefix", ""), current_version))
        except PermissionError as exception:
            print("{}: not allowed cmd: {}".format(version.get("name"), exception))
        except subprocess.CalledProcessError as exception:
            print("{}: no present: ".format(version.get("name")), exception)

    return True


def gopass(key, default=None):
    try:
        return subprocess.check_output(["gopass", "show", key]).strip().decode()
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def gopass_put(secret, key):
    subprocess.check_output(["gopass", "insert", "--force", key], input=secret.encode())


def add_authorization_header(headers):
    try:
        headers["Authorization"] = "Bearer {}".format(
            os.environ["GITHUB_TOKEN"].strip()
            if "GITHUB_TOKEN" in os.environ
            else gopass("gs/ci/github/token/gopass")
        )
        return headers
    except FileNotFoundError:
        return headers


def graphql(query_file, variables, default=None):
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
    return json_response["data"]


def get_git_files_mime(mime_type="text/x-python", ignore_patterns_re=None):
    """
    Get all the files in git that have the specified mime type

    ignore_patterns_re: list of regular expression to be ignored
    """

    ignore_patterns_compiled = [re.compile(p) for p in ignore_patterns_re or []]
    result = []

    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.isfile(filename) and magic.from_file(filename, mime=True) == mime_type:
            accept = True
            for pattern in ignore_patterns_compiled:
                if pattern.search(filename):
                    accept = False
                    break
            if accept:
                result.append(filename)
    return result
