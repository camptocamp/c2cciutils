"""c2cciutils shared utils function."""

import json
import os.path
import re
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Any, cast

import requests
import ruamel.yaml

import c2cciutils.configuration


def get_repository() -> str:
    """Get the current GitHub repository like `organization/project`."""
    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]

    remote_lines = subprocess.check_output(["git", "remote", "--verbose"]).decode().split("\n")  # noqa: S607
    remote_match = (
        re.match(r".*git@github.com:(.*).git .*", remote_lines[0]) if len(remote_lines) >= 1 else None
    )

    if remote_match:
        return remote_match.group(1)

    print("::warning::The GitHub repository isn't found, using 'camptocamp/project'")

    return "camptocamp/project"


def get_master_branch(repo: list[str]) -> tuple[str, bool]:
    """Get the name of the master branch."""
    master_branch = "master"
    success = False
    try:
        default_branch_json = graphql(
            "default_branch.graphql",
            {"name": repo[1], "owner": repo[0]},
            default=False,
        )
        success = default_branch_json is not False
        master_branch = default_branch_json["repository"]["defaultBranchRef"]["name"] if success else "master"
    except RuntimeError as runtime_error:
        print(runtime_error)
        print("::warning::Fallback to master")
    return master_branch, success


def get_config() -> c2cciutils.configuration.Configuration:
    """Get the configuration, with project and auto detections."""
    config: c2cciutils.configuration.Configuration = {}
    config_path = Path("ci/config.yaml")
    if config_path.exists():
        with config_path.open(encoding="utf-8") as open_file:
            yaml_ = ruamel.yaml.YAML()
            config = yaml_.load(open_file)

    return config


def error(
    checker: str,
    message: str,
    file: str | None = None,
    line: int | None = None,
    col: int | None = None,
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
            current_version = subprocess.check_output(version.get("cmd", [])).decode()  # noqa: S603
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


def gopass(key: str, default: str | None = None) -> str | None:
    """
    Get a value from gopass.

    Arguments:
        key: The key to get
        default: the value to return if gopass is not found

    Return the value

    """
    try:
        return subprocess.check_output(["gopass", "show", key]).strip().decode()  # noqa: S603,S607
    except FileNotFoundError:
        if default is not None:
            return default
        raise


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
    except FileNotFoundError:
        return headers
    else:
        return headers


def check_response(response: requests.Response, raise_for_status: bool = True) -> Any:
    """
    Check the response and raise an exception if it's not ok.

    Also print the X-Ratelimit- headers to get information about the rate limiting.
    """
    for header in response.headers:
        if header.lower().startswith("x-ratelimit-"):
            print(f"{header}: {response.headers[header]}")
    if raise_for_status:
        response.raise_for_status()


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
    with (Path(__file__).parent / query_file).open(encoding="utf-8") as query_open:
        query = query_open.read()

    http_response = requests.post(
        os.environ.get("GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"),
        data=json.dumps(
            {
                "query": query,
                "variables": variables,
            },
        ),
        headers=add_authorization_header(
            {
                "Content-Type": "application/json",
            },
        ),
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    )
    if http_response.status_code in (401, 403) and default is not None:
        print(f"::warning::GraphQL error: {http_response.status_code}, use default value")
        check_response(http_response, raise_for_status=False)
        return default
    check_response(http_response)
    json_response = http_response.json()

    if "errors" in json_response:
        message = f"GraphQL error: {json.dumps(json_response['errors'], indent=2)}"
        raise RuntimeError(message)
    if "data" not in json_response:
        message = f"GraphQL no data: {json.dumps(json_response, indent=2)}"
        raise RuntimeError(message)
    return cast("dict[str, Any]", json_response["data"])
