"""
The auditing functions.
"""

import datetime
import json
import os.path
import subprocess  # nosec
import sys
from argparse import Namespace
from typing import Any, Dict, List

import yaml

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
        diff_proc = subprocess.run(["git", "diff", "--quiet"])  # pylint: disable=subprocess-run-check
        if diff_proc.returncode != 0:
            print("::error::There is some changes to commit")
            print("::group::Diff")
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.run(["git", "diff"], check=True)
            print("::endgroup::")

            current_branch = c2cciutils.get_branch(args.branch)
            subprocess.run(["git", "checkout", "-b", f"snyk-fix/{current_branch}"], check=True)
            subprocess.run(["git", "add", "--all"], check=True)
            subprocess.run(["git", "commit", "--message=Snyk auto fix"], check=True)
            subprocess.run(
                ["git", "push", "--force", "origin", f"snyk-fix/{current_branch}"],
                check=True,
            )
            env = os.environ.copy()
            if "GH_TOKEN" not in env:
                if "GITHUB_TOKEN" in env:
                    env["GH_TOKEN"] = env["GITHUB_TOKEN"]
                else:
                    env["GH_TOKEN"] = str(c2cciutils.gopass("gs/ci/github/token/gopass"))
            fix_github_create_pull_request_arguments = config.get(
                "fix_github_create_pull_request_arguments",
                c2cciutils.configuration.AUDIT_SNYK_FIX_PULL_REQUEST_ARGUMENTS_DEFAULT,
            )
            subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    f"--base={current_branch}",
                    f"--body={snyk_fix_message}",
                    *fix_github_create_pull_request_arguments,
                ],
                check=True,
                env=env,
            )
            subprocess.run(["git", "checkout", current_branch], check=True)

    return install_success and test_success and diff_proc.returncode == 0


def get_global_npm_cve() -> List[int]:
    """
    Get the CVE which were installed globally by GitHub.
    """
    with open("/tmp/package.json", "w", encoding="utf-8") as package:
        package.write("{}")

    subprocess.check_call(["npm", "install", "--package-lock-only"], cwd="/tmp")
    audit = json.loads(
        # Don't use check=True because audit will return an error on any vulnerabilities found
        # and we want to manage that ourself.
        subprocess.run(  # pylint: disable=subprocess-run-check
            ["npm", "audit", "--json"], stdout=subprocess.PIPE, cwd="/tmp"
        ).stdout
    )

    if "error" in audit:
        print(yaml.dump(audit["error"], default_flow_style=False, Dumper=yaml.SafeDumper))
        return []

    return [
        vulnerability["id"]
        for vulnerability in audit.get("advisories", audit.get("vulnerabilities")).values()
    ]


def npm(
    config: c2cciutils.configuration.AuditNpmConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Audit all the `package.json` files.

    config is like:
      cwe_ignore: list of ignored CWE

    Arguments:
        config: The audit section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    global_cve = get_global_npm_cve()
    global_success = True
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        success = True
        if os.path.basename(file) != "package.json":
            continue
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess_kwargs: Dict[str, Any] = {} if directory == "" else {"cwd": directory}
        subprocess.check_call(["npm", "install", "--package-lock-only"], **subprocess_kwargs)

        cve_file = os.path.join(directory, "npm-cve-ignore")
        all_ignores = []
        unused_ignores = []
        if os.path.exists(cve_file):
            with open(cve_file, encoding="utf-8") as cve_file_open:
                all_ignores = [int(e) for e in cve_file_open.read().strip().split(",")]
                unused_ignores = list(all_ignores)

        cwe_ignores = config.get("cwe_ignore", [])
        package_ignore = config.get("package_ignore", [])

        audit = json.loads(
            # Don't use check_output because audit will return an error on any vulnerabilities found
            # and we want to manage that ourself.
            subprocess.run(  # pylint: disable=subprocess-run-check
                ["npm", "audit", "--audit-level=moderate", "--json"],
                stdout=subprocess.PIPE,
                **subprocess_kwargs,
            ).stdout
        )
        vulnerabilities = {}
        if "error" in audit:
            print(yaml.dump(audit["error"], default_flow_style=False, Dumper=yaml.SafeDumper))
            print("::endgroup::")
            print("::error::With error")
            return False

        for vulnerability in audit.get("advisories", audit.get("vulnerabilities")).values():
            cwe = vulnerability.get("cwe")
            if isinstance(cwe, str):
                if cwe in cwe_ignores:
                    continue
            else:
                ignored = True
                for cwe_elem in cwe:
                    if cwe_elem not in cwe_ignores:
                        ignored = False
                        break
                if ignored:
                    continue

            completely_ignored = True
            for find in vulnerability.get("findings", []):
                valid_splitted_path = []
                for path in find.get("paths", []):
                    path_splitted = path.split(">")
                    ignored = False
                    for package in package_ignore:
                        if package in path_splitted:
                            ignored = True
                    if not ignored:
                        valid_splitted_path.append(path_splitted)
                        completely_ignored = False
                find["paths"] = valid_splitted_path
            if completely_ignored:
                continue
            if vulnerability["id"] in global_cve:
                continue
            if "recommendation" not in vulnerability or vulnerability.get("recommendation") == "None":
                continue
            if vulnerability["id"] not in all_ignores:
                vulnerabilities[vulnerability["id"]] = vulnerability
            elif vulnerability["id"] in unused_ignores:
                unused_ignores.remove(vulnerability["id"])

        if vulnerabilities:
            first = True
            for vulnerability in vulnerabilities.values():
                cwe = vulnerability.get("cwe")
                if isinstance(cwe, list):
                    cwe = ", ".join(cwe)
                if not first:
                    print("=======================================================")
                print()
                print(f"Title: [{vulnerability.get('id')}] {vulnerability.get('title')}")
                print("Severity: " + vulnerability.get("severity"))
                print("CWE: " + cwe)
                print("Vulnerable versions: " + vulnerability.get("vulnerable_versions"))
                print("Patched versions: " + vulnerability.get("patched_versions"))
                print("Recommendation: " + vulnerability.get("recommendation"))
                for find in vulnerability.get("findings", []):
                    paths = find["paths"]
                    if paths:
                        print("Version: " + find["version"])
                        for path in paths:
                            print("Path: " + " > ".join(path))
                print("More info: " + vulnerability.get("url"))
                print()

            c2cciutils.error(
                "npm", "We have some vulnerabilities see logs", file=os.path.join(directory, "package.json")
            )
            success = False

        if len(unused_ignores) > 0:
            c2cciutils.error(
                "npm",
                "The following cve ignores are not present in the audit: "
                f"{', '.join([str(e) for e in unused_ignores])}",
                file=cve_file,
            )
            success = False

        print("::endgroup::")
        if not success:
            print("::error::With error")
        global_success = global_success and success
    return global_success


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

    version_index = security.headers.index("Version")
    date_index = security.headers.index("Supported Until")

    for row in security.data:
        str_date = row[date_index]
        if str_date not in ("Unsupported", "Best effort", "To be defined"):
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
