"""
c2cciutils shared utils function.
"""

import glob
import json
import os.path
import re
import subprocess  # nosec
import sys
from re import Match, Pattern
from typing import Any, Optional, TypedDict, cast

import magic
import requests
import ruamel.yaml

import c2cciutils.configuration


def get_repository() -> str:
    """
    Get the current GitHub repository like `organization/project`.
    """

    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]

    remote_lines = subprocess.check_output(["git", "remote", "--verbose"]).decode().split("\n")
    remote_match = (
        re.match(r".*git@github.com:(.*).git .*", remote_lines[0]) if len(remote_lines) >= 1 else None
    )

    if remote_match:
        return remote_match.group(1)

    print("::warning::The GitHub repository isn't found, using 'camptocamp/project'")

    return "camptocamp/project"


def merge(default_config: Any, config: Any) -> Any:
    """
    Deep merge the dictionaries (on dictionaries only, not on arrays).

    Arguments:
        default_config: The default config that will be applied
        config: The base config, will be modified
    """

    if not isinstance(default_config, dict) or not isinstance(config, dict):
        return config

    for key in default_config.keys():
        if key not in config:
            config[key] = default_config[key]
        else:
            merge(default_config[key], config[key])
    return config


def get_master_branch(repo: list[str]) -> tuple[str, bool]:
    """Get the name of the master branch."""
    master_branch = "master"
    success = False
    try:
        default_branch_json = graphql(
            "default_branch.graphql", {"name": repo[1], "owner": repo[0]}, default=False
        )
        success = default_branch_json is not False
        master_branch = default_branch_json["repository"]["defaultBranchRef"]["name"] if success else "master"
    except RuntimeError as runtime_error:
        print(runtime_error)
        print("::warning::Fallback to master")
    return master_branch, success


def get_config() -> c2cciutils.configuration.Configuration:
    """
    Get the configuration, with project and auto detections.
    """

    config: c2cciutils.configuration.Configuration = {}
    if os.path.exists("ci/config.yaml"):
        with open("ci/config.yaml", encoding="utf-8") as open_file:
            yaml_ = ruamel.yaml.YAML()
            config = yaml_.load(open_file)

    repository = get_repository()
    repo = repository.split("/")
    master_branch, _ = get_master_branch(repo)

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

    has_docker_files = bool(
        subprocess.run(
            ["git", "ls-files", "*/Dockerfile*", "Dockerfile*"], stdout=subprocess.PIPE, check=True
        ).stdout
    )
    has_python_package = bool(
        subprocess.run(
            ["git", "ls-files", "setup.py", "*/setup.py"], stdout=subprocess.PIPE, check=True
        ).stdout
    ) or bool(
        subprocess.run(
            ["git", "ls-files", "pyproject.toml", "*/pyproject.toml"], stdout=subprocess.PIPE, check=True
        ).stdout
    )

    publish_config = merge(c2cciutils.configuration.PUBLISH_DEFAULT, {})
    publish_config["pypi"]["packages"] = [{"path": "."}] if has_python_package else []
    publish_config["docker"]["images"] = [{"name": get_repository()}] if has_docker_files else []
    publish_config["helm"]["folders"] = [
        os.path.dirname(f) for f in glob.glob("./**/Chart.yaml", recursive=True)
    ]

    default_config = {
        "publish": publish_config,
        "pr-checks": c2cciutils.configuration.PULL_REQUEST_CHECKS_DEFAULT,
        "audit": c2cciutils.configuration.AUDIT_DEFAULT,
    }
    merge(default_config, config)

    return config


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

    Arguments:
        checker: The check name, used to prefix the message
        message: The message
        file: The file where the error happens
        line: The line number of the error
        col: The column number of the error
        error_type: The kind of error (error or warning)
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
        print(f"::{error_type} {result}")
    else:
        print(f"[{error_type}] {result}")


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


def compile_re(config: c2cciutils.configuration.VersionTransform, prefix: str = "") -> list[VersionTransform]:
    """
    Compile the from as a regular expression of a dictionary of the config list.

    to be used with convert and match

    Arguments:
        config: The transform config
        prefix: The version prefix

    Return the compiled transform config.
    """
    result = []
    for conf in config:
        new_conf = cast(VersionTransform, dict(conf))

        from_re = conf.get("from", r"(.*)")
        if from_re[0] == "^":
            from_re = from_re[1:]
        if from_re[-1] != "$":
            from_re += "$"
        from_re = f"^{re.escape(prefix)}{from_re}"

        new_conf["from"] = re.compile(from_re)
        result.append(new_conf)
    return result


def match(
    value: str, config: list[VersionTransform]
) -> tuple[Optional[Match[str]], Optional[VersionTransform], str]:
    """
    Get the matched version.

    Arguments:
        value: That we want to match with
        config: The result of `compile`

    Returns the re match object, the matched config and the value as a tuple
    On no match it returns None, value
    """
    for conf in config:
        matched = conf["from"].match(value)
        if matched is not None:
            return matched, conf, value
    return None, None, value


def does_match(value: str, config: list[VersionTransform]) -> bool:
    """
    Check if the version match with the config patterns.

    Arguments:
        value: That we want to match with
        config: The result of `compile`

    Returns True it it does match else False
    """
    matched, _, _ = match(value, config)
    return matched is not None


def get_value(matched: Optional[Match[str]], config: Optional[VersionTransform], value: str) -> str:
    """
    Get the final value.

    `match`, `config` and `value` are the result of `match`.

    The `config` should have a `to` key with an expand template.

    Arguments:
        matched: The matched object to a regular expression
        config: The result of `compile`
        value: The default value on returned no match

    Return the value
    """
    return matched.expand(config.get("to", r"\1")) if matched is not None and config is not None else value


def print_versions(config: c2cciutils.configuration.PrintVersions) -> bool:
    """
    Print some tools version.

    Arguments:
        config: The print configuration
    """

    for version in config.get("versions", c2cciutils.configuration.PRINT_VERSIONS_VERSIONS_DEFAULT):
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            current_version = subprocess.check_output(version.get("cmd", [])).decode()
            print(f"{version.get('prefix', '')}{current_version}")
        except PermissionError as exception:
            error(
                "print_version",
                f"{version.get('name')}: not allowed cmd: {exception}",
                error_type="warning",
            )
        except subprocess.CalledProcessError as exception:
            error(
                "print_version",
                f"{version.get('name')}: no present: {exception}",
                error_type="warning",
            )
        except FileNotFoundError as exception:
            error(
                "print_version",
                f"{version.get('name')}: no present: {exception}",
                error_type="warning",
            )

    return True


def gopass(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a value from gopass.

    Arguments:
        key: The key to get
        default: the value to return if gopass is not found

    Return the value
    """
    try:
        return subprocess.check_output(["gopass", "show", key]).strip().decode()
    except FileNotFoundError:
        if default is not None:
            return default
        raise


def gopass_put(secret: str, key: str) -> None:
    """
    Put an entry in gopass.

    Arguments:
        secret: The secret value
        key: The key
    """
    subprocess.check_output(["gopass", "insert", "--force", key], input=secret.encode())


def add_authorization_header(headers: dict[str, str]) -> dict[str, str]:
    """
    Add the Authorization header needed to be authenticated on GitHub.

    Arguments:
        headers: The headers

    Return the headers (to be chained)
    """
    try:
        token = (
            os.environ["GITHUB_TOKEN"].strip()
            if "GITHUB_TOKEN" in os.environ
            else gopass("gs/ci/github/token/gopass")
        )
        headers["Authorization"] = f"Bearer {token}"
        return headers
    except FileNotFoundError:
        return headers


def graphql(query_file: str, variables: dict[str, Any], default: Any = None) -> Any:
    """
    Get a graphql result from GitHub.

    Arguments:
        query_file: Relative path from this file to the GraphQL query file.
        variables: The query variables
        default:  The return result if we are not authorized to get the resource

    Return the data result
    In case of error it throw an exception
    """

    with open(os.path.join(os.path.dirname(__file__), query_file), encoding="utf-8") as query_open:
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
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    )
    if http_response.status_code == 401 and default is not None:
        return default
    http_response.raise_for_status()
    json_response = http_response.json()

    if "errors" in json_response:
        raise RuntimeError(f"GraphQL error: {json.dumps(json_response['errors'], indent=2)}")
    if "data" not in json_response:
        raise RuntimeError(f"GraphQL no data: {json.dumps(json_response, indent=2)}")
    return cast(dict[str, Any], json_response["data"])


def get_git_files_mime(
    mime_type: Optional[list[str]] = None,
    extensions: Optional[list[str]] = None,
    ignore_patterns_re: Optional[list[str]] = None,
) -> list[str]:
    """
    Get list of paths from git with all the files that have the specified mime type.

    Arguments:
        mime_type: The considered MIME type
        extensions: The considered extensions
        ignore_patterns_re: A list of regular expressions of files that we should ignore
    """
    if mime_type is None:
        mime_type = ["text/x-python", "text/x-script.python"]
    if extensions is None:
        extensions = [".py"]
    ignore_patterns_compiled = [re.compile(p) for p in ignore_patterns_re or []]
    result = []

    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.isfile(filename) and (
            os.path.splitext(filename)[1] in extensions or magic.from_file(filename, mime=True) in mime_type
        ):
            accept = True
            for pattern in ignore_patterns_compiled:
                if pattern.search(filename):
                    accept = False
                    break
            if accept:
                result.append(filename)
    return result


def get_branch(branch: Optional[str], master_branch: str = "master") -> str:
    """
    Get the branch name.

    Arguments:
        branch: The forced to use branch name
        master_branch: The master branch name, can be used as default value

    Return the branch name
    """

    if branch is not None:
        return branch
    try:
        branch = (
            subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=True, stdout=subprocess.PIPE)
            .stdout.decode()
            .strip()
        )
    except subprocess.CalledProcessError as exception:
        print(f"Error getting branch: {exception}")
        branch = "HEAD"

    if branch == "HEAD":
        branch = os.environ.get("GITHUB_HEAD_REF", master_branch)
        assert branch is not None
    return branch


def get_based_on_master(
    repo: list[str],
    override_current_branch: Optional[str],
    master_branch: str,
    config: c2cciutils.configuration.Configuration,
) -> bool:
    """
    Check that we are not on a release branch (to avoid errors in versions check).

    This function will check the last 20 commits in current branch,
    and for each other branch (max 50) check if any commit in last 10 commits is the current one.

    Arguments:
        repo: The repository [<organization>, <name>]
        override_current_branch: The branch to use instead of the current one
        master_branch: The master branch name
        config: The full configuration
    """
    if os.environ.get("GITHUB_REF", "").startswith("refs/tags/"):
        # The tags are never consider as based on master
        return False
    current_branch = get_branch(override_current_branch, master_branch)
    if current_branch == master_branch:
        return True
    branches_re = compile_re(config["version"].get("branch_to_version_re", []))
    if does_match(current_branch, branches_re):
        return False
    if os.environ.get("GITHUB_BASE_REF"):
        return os.environ.get("GITHUB_BASE_REF") == master_branch
    commits_repository_json = graphql(
        "commits.graphql", {"name": repo[1], "owner": repo[0], "branch": current_branch}
    ).get("repository", {})
    commits_json = (
        commits_repository_json.get("ref", {}).get("target", {}).get("history", {}).get("nodes", [])
        if commits_repository_json.get("ref")
        else []
    )
    branches_json = [
        branch
        for branch in (
            graphql("branches.graphql", {"name": repo[1], "owner": repo[0]})["repository"]["refs"]["nodes"]
        )
        if branch["name"] != current_branch and does_match(branch["name"], branches_re)
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


def get_codespell_command(config: c2cciutils.configuration.Configuration, fix: bool = False) -> list[str]:
    """
    Get the codespell command.

    Arguments:
        config: The full configuration
        fix: If we should fix the errors
    """
    codespell_config = config.get("codespell", {})
    codespell_config = codespell_config if isinstance(codespell_config, dict) else {}
    command = ["codespell"]
    if fix:
        command.append("--write-changes")
    for spell_ignore_file in (
        ".github/spell-ignore-words.txt",
        "spell-ignore-words.txt",
        ".spell-ignore-words.txt",
    ):
        if os.path.exists(spell_ignore_file):
            command.append(f"--ignore-words={spell_ignore_file}")
            break
    dictionaries = codespell_config.get(
        "internal_dictionaries", c2cciutils.configuration.CODESPELL_DICTIONARIES_DEFAULT
    )
    if dictionaries:
        command.append("--builtin=" + ",".join(dictionaries))
    command += codespell_config.get("arguments", c2cciutils.configuration.CODESPELL_ARGUMENTS_DEFAULT)
    return command


def snyk_exec() -> tuple[str, dict[str, str]]:
    """Get the Snyk cli executable path."""

    if not os.path.exists(os.path.join(os.path.dirname(__file__), "node_modules")):
        subprocess.run(["npm", "install"], cwd=os.path.dirname(__file__), check=True)  # nosec

    env = {**os.environ}
    env["FORCE_COLOR"] = "true"
    if "SNYK_TOKEN" not in env:
        token = gopass("gs/ci/snyk/token")
        if token is not None:
            env["SNYK_TOKEN"] = token
    if "SNYK_ORG" in env:
        subprocess.run(["snyk", "config", "set", f"org={env['SNYK_ORG']}"], check=True, env=env)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules/snyk/bin/snyk"), env
