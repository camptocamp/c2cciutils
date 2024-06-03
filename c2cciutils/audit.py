"""
The auditing functions.
"""

import datetime
import json
import os.path
import subprocess  # nosec
import sys
from argparse import Namespace

import c2cciutils
import c2cciutils.configuration
import c2cciutils.security


def print_versions(
    config: c2cciutils.configuration.PrintVersions,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Print the versions.

    Arguments:
        config: The audit section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    print("::group::Versions")
    c2cciutils.print_versions(config)
    print("::endgroup::")

    return True


def snyk(
    config: c2cciutils.configuration.AuditSnykConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Audit the code with Snyk.
    """
    del full_config

    one_done = False
    install_success = True
    test_success = True

    for file in (
        subprocess.run(
            ["git", "ls-files", "requirements.txt", "*/requirements.txt"], stdout=subprocess.PIPE, check=True
        )
        .stdout.decode()
        .strip()
        .split("\n")
    ):
        if not file:
            continue
        if file in config.get(
            "files_no_install", c2cciutils.configuration.AUDIT_SNYK_FILES_NO_INSTALL_DEFAULT
        ):
            continue
        print(f"::notice::Install from: {file}")
        if not one_done:
            print("::group::Install dependencies")
            one_done = True
        sys.stdout.flush()
        sys.stderr.flush()
        proc = subprocess.run(  # pylint: disable=subprocess-run-check
            [
                "pip",
                "install",
                *config.get(
                    "pip_install_arguments", c2cciutils.configuration.AUDIT_SNYK_PIP_INSTALL_ARGUMENTS_DEFAULT
                ),
                f"--requirement={file}",
            ]
        )
        if proc.returncode != 0:
            print(f"::error::With error from: {file}")
        install_success &= proc.returncode == 0

    for file in (
        subprocess.run(["git", "ls-files", "Pipfile", "*/Pipfile"], stdout=subprocess.PIPE, check=True)
        .stdout.decode()
        .strip()
        .split("\n")
    ):
        if not file:
            continue
        if file in config.get(
            "files_no_install", c2cciutils.configuration.AUDIT_SNYK_FILES_NO_INSTALL_DEFAULT
        ):
            continue
        if not one_done:
            print("::group::Install dependencies")
            one_done = True
        print(f"::notice::Install from: {file}")
        directory = os.path.dirname(os.path.abspath(file))

        sys.stdout.flush()
        sys.stderr.flush()
        proc = subprocess.run(  # pylint: disable=subprocess-run-check
            [
                "pipenv",
                "sync",
                *config.get(
                    "pipenv_sync_arguments", c2cciutils.configuration.AUDIT_SNYK_PIPENV_SYNC_ARGUMENTS_DEFAULT
                ),
            ],
            cwd=directory,
        )
        if proc.returncode != 0:
            print(f"::error::With error from: {file}")
        install_success &= proc.returncode == 0

    if one_done:
        print("::endgroup::")
    if not install_success:
        print("::error::Error while installing the dependencies")

    snyk_exec, env = c2cciutils.snyk_exec()
    if not args.fix:
        command = [snyk_exec, "monitor", f"--target-reference={args.branch}"] + config.get(
            "monitor_arguments", c2cciutils.configuration.AUDIT_SNYK_MONITOR_ARGUMENTS_DEFAULT
        )
        print(f"::group::Run: {' '.join(command)}")
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
        print("::endgroup::")

        command = [snyk_exec, "test"] + config.get(
            "test_arguments", c2cciutils.configuration.AUDIT_SNYK_TEST_ARGUMENTS_DEFAULT
        )
        print(f"::group::Run: {' '.join(command)}")
        sys.stdout.flush()
        sys.stderr.flush()
        test_proc = subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
        print("::endgroup::")
        if test_proc.returncode != 0:
            test_success = False
            print("::error::With error")

        # Clean all the changes to isolate the fix diff
        subprocess.run(["git", "reset", "--hard"], check=True)

    command = [snyk_exec, "fix"] + config.get(
        "fix_arguments", c2cciutils.configuration.AUDIT_SNYK_FIX_ARGUMENTS_DEFAULT
    )
    print(f"::group::Run: {' '.join(command)}")
    sys.stdout.flush()
    sys.stderr.flush()
    snyk_fix_proc = subprocess.run(  # pylint: disable=subprocess-run-check
        command, env={**env, "FORCE_COLOR": "false"}, stdout=subprocess.PIPE, encoding="utf-8"
    )
    snyk_fix_message = snyk_fix_proc.stdout.strip()
    print("::endgroup::")

    if not args.fix:
        current_branch = c2cciutils.get_branch(args.branch)
        fix_github_create_pull_request_arguments = config.get(
            "fix_github_create_pull_request_arguments",
            c2cciutils.configuration.AUDIT_SNYK_FIX_PULL_REQUEST_ARGUMENTS_DEFAULT,
        )
        has_diff = c2cciutils.create_pull_request_if_needed(
            current_branch,
            f"snyk-fix/{current_branch}",
            "Snyk auto fix",
            [f"--body={snyk_fix_message}", *fix_github_create_pull_request_arguments],
        )

    return install_success and test_success and not has_diff


def outdated_versions(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check that the versions from the SECURITY.md are not outdated.

    Arguments:
        config: The audit section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config

    repo = c2cciutils.get_repository().split("/")
    json_response = c2cciutils.graphql(
        "default_branch.graphql",
        {"name": repo[1], "owner": repo[0]},
    )

    if "errors" in json_response:
        raise RuntimeError(json.dumps(json_response["errors"], indent=2))
    if json_response["repository"]["defaultBranchRef"]["name"] != c2cciutils.get_branch(args.branch):
        return True

    success = True

    if not os.path.exists("SECURITY.md"):
        return True

    with open("SECURITY.md", encoding="utf-8") as security_file:
        security = c2cciutils.security.Security(security_file.read())

    version_index = security.version_index
    date_index = security.support_until_index

    for row in security.data:
        str_date = row[date_index]
        if str_date not in (
            c2cciutils.security.SUPPORT_TO_BE_DEFINED,
            c2cciutils.security.SUPPORT_BEST_EFFORT,
            c2cciutils.security.SUPPORT_UNSUPPORTED,
        ):
            date = datetime.datetime.strptime(row[date_index], "%d/%m/%Y")
            if date < datetime.datetime.now():
                c2cciutils.error(
                    "versions",
                    f"The version '{row[version_index]}' is outdated, it can be set to "
                    "'Unsupported', 'Best effort' or 'To be defined'",
                    "SECURITY.md",
                )
                success = False
    return success
