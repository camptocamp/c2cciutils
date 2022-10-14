"""
The checking functions.
"""

import glob
import os
import re
import subprocess  # nosec
import sys
from argparse import Namespace
from io import StringIO
from typing import Any, Dict, List, Optional, Set

import requests
import ruamel.yaml
import yaml
from ruamel.yaml.comments import CommentedMap

import c2cciutils
import c2cciutils.configuration
import c2cciutils.prettier
import c2cciutils.security


def print_config(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Print the configuration.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, args

    yaml_ = ruamel.yaml.YAML()
    yaml_.default_flow_style = False
    out = StringIO()
    yaml_.dump(full_config, out)
    print(out.getvalue())
    return True


def print_environment_variables(
    config: None, full_config: c2cciutils.configuration.Configuration, args: Namespace
) -> bool:
    """
    Print the environment variables.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config, args

    for name, value in sorted(os.environ.items()):
        print(f"{name}: {value}")
    return True


def print_github_event(
    config: None, full_config: c2cciutils.configuration.Configuration, args: Namespace
) -> bool:
    """
    Print the GitHub event.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config, args

    if "GITHUB_EVENT_PATH" in os.environ:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event:
            print(event.read())
    return True


def _check_properties(
    check: str, file: str, path: str, properties: CommentedMap, reference: Dict[str, Any]
) -> bool:
    if path:
        path += "."

    success = True

    for key, value in reference.items():
        if key not in properties:
            c2cciutils.error(
                check,
                f"The property '{path}{key}' should be defined",
                file,
                properties.lc.line + 1,
                properties.lc.col + 1,
            )
            success = False
        if isinstance(value, dict):
            if not isinstance(properties[key], dict):
                c2cciutils.error(
                    check,
                    f"The property '{path}{key}' should be a dictionary",
                    file,
                    properties.lc.line + 1,
                    properties.lc.col + 1,
                )
                success = False
            else:
                success &= _check_properties(check, file, path + key, properties[key], value)
        else:
            if properties.get(key) != value:
                c2cciutils.error(
                    check,
                    f"The property '{path}{key}' should have the value, '{value}', "
                    f"but is '{properties.get(key)}'",
                    file,
                    properties.lc.line + 1,
                    properties.lc.col + 1,
                )
                success = False
    return success


def gitattribute(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check that we don't have any error with the gitattributes.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config, args

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        git_ref = (
            subprocess.check_output(["git", "--no-pager", "log", "--oneline"])
            .decode()
            .strip()
            .split("\n", maxsplit=1)[-1]
            .split(" ")[0]
        )
        subprocess.check_call(["git", "--no-pager", "diff", "--no-renames", "--check", git_ref])
        return True
    except subprocess.CalledProcessError:
        c2cciutils.error(
            "gitattribute",
            "Error, see above",
        )
        return False


F_NULL = open(os.devnull, "w", encoding="utf-8")  # pylint: disable=consider-using-with


def eof(config: None, full_config: c2cciutils.configuration.Configuration, args: Namespace) -> bool:
    r"""
    Check the non empty text files end with "\n".

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config

    try:
        success = True

        sys.stdout.flush()
        sys.stderr.flush()
        for filename in subprocess.check_output(["git", "ls-files"]).decode().split("\n"):
            if os.path.isfile(filename):
                if (
                    subprocess.call(
                        f"git check-attr -a '{filename}' | grep ' text: set'",
                        shell=True,  # nosec
                        stdout=F_NULL,
                    )
                    == 0
                ):
                    size = os.stat(filename).st_size
                    if size != 0:
                        with open(filename, encoding="utf-8") as open_file:
                            open_file.seek(size - 1)
                            if ord(open_file.read()) != ord("\n"):
                                if not args.fix:
                                    with open(filename, "a", encoding="utf-8") as open_file_write:
                                        open_file_write.write("\n")
                                else:
                                    c2cciutils.error(
                                        "eof",
                                        f"No new line at end of '{filename}' file.",
                                        filename,
                                    )
                                    success = False

        return success
    except subprocess.CalledProcessError:
        c2cciutils.error(
            "eof",
            "Error, see above",
        )
        return False


def workflows(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check each workflow have a timeout and/or do not use blacklisted images.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del config, full_config, args

    success = True
    files = glob.glob(".github/workflows/*.yaml")
    files += glob.glob(".github/workflows/*.yml")
    for filename in files:
        with open(filename, encoding="utf-8") as open_file:
            workflow = yaml.load(open_file, Loader=yaml.SafeLoader)

        for name, job in workflow.get("jobs").items():
            if job.get("timeout-minutes") is None:
                c2cciutils.error(
                    "workflows",
                    f"The workflow '{filename}', job '{name}' has no timeout",
                    filename,
                )
                success = False

    return success


def versions(
    config: c2cciutils.configuration.ChecksVersionsConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Verify various GitHub / CI tools versions or branches configurations.

    Versions from audit workflow, protected branches and backport labels
    match with versions from `SECURITY.md` file.
    The columns `Version` and `Supported Until` should be present.
    The `Supported Until` should contains dates formatted as `dd/mm/yyyy`, or `Unsupported`
    (we ignore those lines), or `Best effort`, or `To be defined`.

    config is like:
        extra_versions: # versions that are not in the `SECURITY.md` but should still be consided
        audit: # if `True` check that the audit workflow run on the right branches
        backport_labels: # if `True` check the required backport labels exists
        branches: # if `True` check that the required branches exists

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """

    del args

    # If the `SECURITY.md` file is not present the check is disabled.
    if not os.path.exists("SECURITY.md"):
        c2cciutils.error(
            "versions", "The file 'SECURITY.md' does not exists", "SECURITY.md", error_type="warning"
        )
        return True

    with open("SECURITY.md", encoding="utf-8") as open_file:
        security = c2cciutils.security.Security(open_file.read())

    for col in ("Version", "Supported Until"):
        if col not in security.headers:
            c2cciutils.error(
                "versions",
                f"The file 'SECURITY.md' does not have the column required '{col}'",
                "SECURITY.md",
            )
            return False

    version_index = security.headers.index("Version")
    date_index = security.headers.index("Supported Until")

    success = True
    all_versions = set(config.get("extra_versions", []))

    for row in security.data:
        str_date = row[date_index]
        if str_date != "Unsupported":
            all_versions.add(row[version_index])

    if config.get("audit", False):
        if not _versions_audit(all_versions, full_config):
            success = False
    if config.get("backport_labels", False):
        if not _versions_backport_labels(all_versions, full_config):
            success = False
    if config.get("branches", False):
        if not _versions_branches(all_versions, full_config):
            success = False

    return success


def _get_branch_matrix(
    job: Dict[str, Any], branch_to_version_re: List[c2cciutils.VersionTransform]
) -> List[str]:
    """
    Get the branches from a `strategy` `matrix`, and return the corresponding version.

    Arguments:
        job: The job from the GitHub workflow
        branch_to_version_re: The transform configuration
    """

    matrix = job.get("strategy", {}).get("matrix", {})
    if "include" in matrix:
        branch = []
        for include in matrix["include"]:
            if "branch" in include:
                branch.append(include["branch"])
    else:
        branch = matrix.get("branch", [])
    return [c2cciutils.get_value(*c2cciutils.match(av, branch_to_version_re)) for av in branch]


def _versions_audit(all_versions: Set[str], full_config: c2cciutils.configuration.Configuration) -> bool:
    """
    Check the audit branches match with the versions from the Security.md.

    Arguments:
        all_versions: All the required versions
        full_config: All the CI configuration
    """
    success = True
    filename = ".github/workflows/audit.yaml"
    if not os.path.exists(filename):
        c2cciutils.error(
            "versions",
            f"The file '{filename}' does not exists",
            filename,
        )
        success = False
    else:
        with open(filename, encoding="utf-8") as open_file:
            workflow = yaml.load(open_file, Loader=yaml.SafeLoader)

        branch_to_version_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))

        for name, job in workflow.get("jobs").items():
            audit_versions = _get_branch_matrix(job, branch_to_version_re)

            if all_versions != set(audit_versions):
                c2cciutils.error(
                    "versions",
                    f"The workflow '{filename}', job '{name}' does not have a branch matrix with the "
                    "right list of versions "
                    f"[{', '.join(sorted(audit_versions))}] != [{', '.join(sorted(all_versions))}]",
                )
                success = False
    return success


def _versions_backport_labels(
    all_versions: Set[str], full_config: c2cciutils.configuration.Configuration
) -> bool:
    """
    Check the backport labels match with the version from the Security.md.

    Arguments:
        all_versions: All the required versions
        full_config: All the CI configuration
    """
    success = True
    try:
        label_versions = set()

        sys.stdout.flush()
        sys.stderr.flush()
        labels_response = requests.get(
            f"https://api.github.com/repos/{c2cciutils.get_repository()}/labels",
            headers=c2cciutils.add_authorization_header({"Accept": "application/vnd.github.v3+json"}),
            timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
        )
        labels_response.raise_for_status()

        label_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []), "backport ")
        for json_label in labels_response.json():
            match = c2cciutils.match(json_label["name"], label_re)
            if match[0] is not None:
                label_versions.add(c2cciutils.get_value(*match))

        if all_versions != label_versions:
            c2cciutils.error(
                "versions backport labels",
                "The backport labels do not have the right list of versions "
                f"[{', '.join(sorted(label_versions))}] != [{', '.join(sorted(all_versions))}]",
            )
            success = False
    except FileNotFoundError as exception:
        c2cciutils.error(
            "versions backport labels",
            f"Unable to get credentials to run the check: {exception}",
            error_type="warning",
        )

    return success


def _versions_branches(all_versions: Set[str], full_config: c2cciutils.configuration.Configuration) -> bool:
    """
    Check the branches match with the versions from the Security.md.

    Arguments:
        all_versions: All the required versions
        full_config: All the CI configuration
    """
    success = True
    try:
        branch_versions: Set[str] = set()

        sys.stdout.flush()
        sys.stderr.flush()
        url: Optional[str] = f"https://api.github.com/repos/{c2cciutils.get_repository()}/branches"
        while url:
            branches_response = requests.get(
                url,
                params={"protected": "true"},
                headers=c2cciutils.add_authorization_header({"Accept": "application/vnd.github.v3+json"}),
                timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
            )
            branches_response.raise_for_status()
            url = None
            try:
                links = requests.utils.parse_header_links(branches_response.headers.get("Link", ""))
                if isinstance(links, list):
                    next_links = [link["url"] for link in links if link["rel"] == "next"]
                    if len(next_links) >= 1:
                        url = next_links[0]
            except Exception as exception:  # pylint: disable=broad-except
                c2cciutils.error(
                    "versions branches",
                    f"error on reading Link header '{branches_response.headers.get('Link')}': {exception}",
                    error_type="warning",
                )

            branch_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))
            for branch in branches_response.json():
                match = c2cciutils.match(branch["name"], branch_re)
                if match[0] is not None:
                    branch_versions.add(c2cciutils.get_value(*match))

        if len([v for v in all_versions if v not in branch_versions]) > 0:
            c2cciutils.error(
                "versions branches",
                "The version from the protected branches does not correspond with "
                f"expected versions [{', '.join(sorted(branch_versions))}] != "
                f"[{', '.join(sorted(all_versions))}]",
            )
            success = False
    except FileNotFoundError as exception:
        c2cciutils.error(
            "versions branches",
            f"Unable to get credentials to run the check: {exception}",
            error_type="warning",
        )

    return success


def black(
    config: c2cciutils.configuration.ChecksBlackConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run black check on all files including Python files without .py extension.

    config is like:
      ignore_patterns_re: [] # list of regular expression we should ignore

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        cmd = ["black"]
        if not args.fix:
            cmd += ["--color", "--diff", "--check"]
        cmd.append("--")
        python_files = c2cciutils.get_git_files_mime(ignore_patterns_re=config.get("ignore_patterns_re", []))
        cmd += python_files
        if len(python_files) > 0:
            subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        c2cciutils.error(
            "black",
            "Error, see above",
        )
        return False


def isort(
    config: c2cciutils.configuration.ChecksIsortConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run isort check on all files including Python files without .py extension.

    config is like:
      ignore_patterns_re: [] # list of regular expression we should ignore

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        cmd = ["isort"]
        if not args.fix:
            cmd += ["--check-only", "--diff"]
        cmd.append("--")
        python_files = c2cciutils.get_git_files_mime(ignore_patterns_re=config.get("ignore_patterns_re", []))
        cmd += python_files
        if len(python_files) > 0:
            subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        c2cciutils.error(
            "isort",
            "Error, see above",
        )
        return False


def codespell(
    config: c2cciutils.configuration.ChecksCodespellConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run codespell check on all files.

    If there is an `spell-ignore-words.txt` file we consider it with ignore word

    config is like:
        ignore_re: [] # list of patterns to be ignored
        arguments: [] # codespell arguments

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """

    try:
        cmd = c2cciutils.get_codespell_command(full_config, args.fix)
        cmd.append("--")
        ignore_res = [
            re.compile(r)
            for r in config.get(
                "ignore_re", c2cciutils.configuration.CODESPELL_IGNORE_REGULAR_EXPRESSION_DEFAULT
            )
        ]
        for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
            if os.path.isfile(filename):
                include = True
                for ignore_re in ignore_res:
                    if ignore_re.match(filename):
                        include = False
                        continue
                if include:
                    cmd.append(filename)
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        c2cciutils.error(
            "codespell",
            "Error, see above",
        )
        return False


def prettier(
    config: c2cciutils.configuration.ChecksPrettierConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run prettier check on all the supported files.

    config is like:
      # Currently empty

    Arguments:
        config: The config
        full_config: The full config
        args: The parsed command arguments
    """
    del config, full_config

    success = True

    with c2cciutils.prettier.Prettier() as prettier_lib:
        for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
            if os.path.isfile(filename):
                info = prettier_lib.get_info(filename)
                if info.get("info", {}).get("ignored", False):
                    continue
                if not info.get("info", {}).get("inferredParser"):
                    continue

                print(f"Checking {filename}")

                prettier_config = info["config"]
                if not prettier_config:
                    prettier_config = {}
                prettier_config["parser"] = info["info"]["inferredParser"]

                if args.fix:
                    if not prettier_lib.format(filename, prettier_config):
                        success = False
                else:
                    if not prettier_lib.check(filename, prettier_config):
                        success = False
    return success


def snyk(
    config: c2cciutils.configuration.ChecksSnykConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run Snyk check.
    """
    del full_config, args

    snyk_exec, env = c2cciutils.snyk_exec()
    command = [snyk_exec, "test"] + config.get(
        "arguments", c2cciutils.configuration.CHECKS_SNYK_ARGUMENTS_DEFAULT
    )

    print(f"Running Snyk: {' '.join(command)}")
    sys.stdout.flush()
    sys.stderr.flush()
    test_proc = subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
    print(f"Snyk exit code: {test_proc.returncode}")
    # For the moment we don't return an error
    # return test_proc.returncode == 0
    return True


def snyk_code(
    config: c2cciutils.configuration.ChecksSnykCodeConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run Snyk code check.
    """
    del full_config, args

    snyk_exec, env = c2cciutils.snyk_exec()
    command = [snyk_exec, "code", "test"] + config.get(
        "arguments", c2cciutils.configuration.CHECKS_SNYK_CODE_ARGUMENTS_DEFAULT
    )
    print(f"Running Snyk: {' '.join(command)}")
    sys.stdout.flush()
    sys.stderr.flush()
    test_proc = subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
    print(f"Snyk exit code: {test_proc.returncode}")
    # For the moment we don't return an error
    # return test_proc.returncode == 0
    return True


def snyk_iac(
    config: c2cciutils.configuration.ChecksSnykIacConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run Snyk iac check.
    """
    del full_config, args

    snyk_exec, env = c2cciutils.snyk_exec()
    command = [snyk_exec, "iac", "test"] + config.get(
        "arguments", c2cciutils.configuration.CHECKS_SNYK_IAC_ARGUMENTS_DEFAULT
    )
    print(f"Running Snyk: {' '.join(command)}")
    sys.stdout.flush()
    sys.stderr.flush()
    test_proc = subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
    print(f"Snyk exit code: {test_proc.returncode}")
    return test_proc.returncode == 0


def snyk_fix(
    config: c2cciutils.configuration.ChecksSnykFixConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run Snyk fix.
    """
    del full_config, args

    snyk_exec, env = c2cciutils.snyk_exec()
    command = [snyk_exec, "fix"] + config.get(
        "arguments", c2cciutils.configuration.CHECKS_SNYK_FIX_ARGUMENTS_DEFAULT
    )
    print(f"Running Snyk: {' '.join(command)}")
    sys.stdout.flush()
    sys.stderr.flush()
    test_proc = subprocess.run(command, env=env)  # pylint: disable=subprocess-run-check
    print(f"Snyk exit code: {test_proc.returncode}")
    sys.stdout.flush()
    sys.stderr.flush()
    test_proc = subprocess.run(["git", "diff"])  # pylint: disable=subprocess-run-check
    return True


def print_versions(
    config: c2cciutils.configuration.PrintVersions,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Print some tools versions.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    return c2cciutils.print_versions(config)
