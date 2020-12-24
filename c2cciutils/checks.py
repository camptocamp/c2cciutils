"""
The checking functions.
"""

import configparser
import glob
import os
import re
import subprocess
import sys
from argparse import Namespace
from io import StringIO
from typing import Any, Dict, List, Optional, Set

import magic
import requests
import ruamel.yaml
import yaml
from editorconfig import EditorConfigError, get_properties

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

    yaml_ = ruamel.yaml.YAML()  # type: ignore
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
        with open(os.environ["GITHUB_EVENT_PATH"]) as event:
            print(event.read())
    return True


def black_config(
    config: c2cciutils.configuration.ChecksBlackConfigurationConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check the black configuration.

    config is like:
        properties: # dictionary of properties to check

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    # If there is no python file the check is disabled
    python = False
    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if (
            os.path.isfile(filename)
            and magic.from_file(filename, mime=True) == "text/x-python"  # type: ignore
        ):
            python = True
            break

    if python:
        if not os.path.exists("pyproject.toml"):
            c2cciutils.error(
                "black_config",
                "The file 'pyproject.toml' with a section tool.black is required",
                "pyproject.toml",
            )
            return False

        configp = configparser.ConfigParser()
        configp.read("pyproject.toml")
        if "tool.black" not in configp.sections():
            c2cciutils.error(
                "black_config",
                "The 'tool.black' section is required in the 'pyproject.toml' file",
                "pyproject.toml",
            )
            return False

        if isinstance(config, dict):
            for key, value in config.get("properties", {}).items():
                if configp.get("tool.black", key) != value:
                    c2cciutils.error(
                        "black_config",
                        "The property '{}' should have the value, '{}', but is '{}'".format(
                            key, value, configp.get("tool.black", key)
                        ),
                        "pyproject.toml",
                    )
    return True


def editorconfig(
    config: c2cciutils.configuration.ChecksEditorconfigConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check the editorconfig configuration.

    config is like:
        properties:
          <file_pattern>: {} # dictionary of properties to check

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    success = True
    for pattern, wanted_properties in config.get("properties", {}).items():
        try:
            for filename in subprocess.check_output(["git", "ls-files", pattern]).decode().split("\n"):
                if os.path.isfile(filename):
                    properties = get_properties(os.path.abspath(filename))

                    for key, value in wanted_properties.items():
                        if value is not None and (key not in properties or properties[key] != value):
                            c2cciutils.error(
                                "editorconfig",
                                "For pattern: {} the property '{}' is '{}' but should be '{}'.".format(
                                    pattern, key, properties.get(key, ""), value
                                ),
                                ".editorconfig",
                            )
                            success = False
                    break
        except EditorConfigError:
            c2cciutils.error(
                "editorconfig",
                "Error occurred while getting EditorConfig properties",
                ".editorconfig",
            )
            return False
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
            .split("\n")[-1]
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


FNULL = open(os.devnull, "w")


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
                        shell=True,
                        stdout=FNULL,
                    )
                    == 0
                ):
                    size = os.stat(filename).st_size
                    if size != 0:
                        with open(filename) as open_file:
                            open_file.seek(size - 1)
                            if ord(open_file.read()) != ord("\n"):
                                if not args.fix:
                                    with open(filename, "a") as open_file_write:
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
    config: c2cciutils.configuration.ChecksWorkflowsConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check each workflow have a timeout and/or do not use blacklisted images.

    config is like:
        images_blacklist: [] # list of `runs-on` images to blacklist
        timeout: True # check that all the workflow have a timeout

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    success = True
    files = glob.glob(".github/workflows/*.yaml")
    files += glob.glob(".github/workflows/*.yml")
    for filename in files:
        with open(filename) as open_file:
            workflow = yaml.load(open_file, yaml.SafeLoader)

        for name, job in workflow.get("jobs").items():
            if job.get("runs-on") in config.get("images_blacklist", []):
                c2cciutils.error(
                    "workflows",
                    "The workflow '{}', job '{}' runs on '{}' but it is blacklisted".format(
                        filename, name, job.get("runs-on")
                    ),
                    filename,
                )
                success = False

            if job.get("timeout-minutes") is None:
                c2cciutils.error(
                    "workflows",
                    f"The workflow '{filename}', job '{name}' has no timeout",
                    filename,
                )
                success = False

    return success


def required_workflows(
    config: c2cciutils.configuration.ChecksRequiredWorkflowsConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Test we have the required workflow with the required properties.

    config is like:
        <filename>: # if set directly to `True` just check that the file is present, to `False`
                check nothing.
            steps:
              - run_re: # rebular expresiion that we should have in a run, on one of the jobs.
                env: # the list or required environment variable for this step
            strategy-fail-fast: False # If present check the value of the `fail-fast`, on all the jobs.
            if: # if present check the value of the `if`, on all the jobs.
            noif: # if `True` theck that we don't have an `if`.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    success = True
    for file_, conf in config.items():
        if conf is False:
            continue

        filename = os.path.join(".github/workflows", file_)
        if not os.path.exists(filename):
            c2cciutils.error(
                "required_workflows",
                f"The workflow '{filename}' is required",
                filename,
            )
            success = False
            continue

        if not isinstance(conf, dict):
            continue

        with open(filename) as open_file:
            workflow = yaml.load(open_file, yaml.SafeLoader)

        for name, job in workflow.get("jobs").items():
            if "if" in conf:
                if job.get("if") != conf["if"]:
                    c2cciutils.error(
                        "required_workflows",
                        "The workflow '{}', job '{}' does not have the following if '{}'".format(
                            filename, name, conf["if"]
                        ),
                        filename,
                    )
                    success = False
            if conf.get("noif", False):
                if "if" in job:
                    c2cciutils.error(
                        "required_workflows",
                        f"The workflow '{filename}', job '{name}' should not have a if",
                        filename,
                    )
                    success = False
            if "strategy-fail-fast" in conf:
                if job.get("strategy", {}).get("fail-fast") != conf["strategy-fail-fast"]:
                    c2cciutils.error(
                        "required_workflows",
                        "The workflow '{}', job '{}' does not have the strategy/fail-fast as {}".format(
                            filename, name, conf["strategy-fail-fast"]
                        ),
                        filename,
                    )
                    success = False
            for step_conf in conf.get("steps", []):
                run_re = re.compile(step_conf["run_re"]) if "run_re" in step_conf else None
                found = False
                for step in job["steps"]:
                    current_ok = True
                    if run_re is not None and run_re.match(step.get("run", "")) is None:
                        current_ok = False
                    elif "env" in step_conf:
                        # Verify that all the env specified in the config is present in the step of
                        # the workflow
                        conf_env = set(step_conf["env"])
                        for env in step.get("env", {}).keys():
                            if env in conf_env:
                                conf_env.remove(env)
                        if len(conf_env) != 0:
                            current_ok = False
                    if current_ok:
                        found = True
                        break
                if not found:
                    c2cciutils.error(
                        "required_workflows",
                        "The workflow '{}', job '{}' doesn't have the step for:\n{}".format(
                            filename,
                            name,
                            yaml.dump(step_conf, default_flow_style=False, Dumper=yaml.SafeDumper).strip(),
                        ),
                        filename,
                    )
                    success = False
        if conf.get("on", False):
            for workflow_on, on_config in conf["on"].items():
                # 'on' become True
                if workflow_on not in workflow.get(True, {}):
                    c2cciutils.error(
                        "required_workflows",
                        f"The workflow '{filename}', does not have the 'on' as '{workflow_on}'",
                        filename,
                    )
                    success = False
                elif isinstance(on_config, dict) and "types" in on_config:
                    for on_type in on_config["types"]:
                        if on_type not in workflow.get(True, {})[workflow_on].get("types", []):
                            c2cciutils.error(
                                "required_workflows",
                                f"The workflow '{filename}', does not have the on '{workflow_on}' should "
                                f"have the type '{on_type}'",
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

    Versions from audit workflow, rebuild workdlow(s), protected branches and backport labels
    match with versions from `SECURITY.md` file.
    The columns `Version` and `Supported Until` should be present.
    The `Supported Until` should contains dates formatted as `dd/mm/yyyy`, or `Unsupported`
    (we ignore those lines), or `Best effort`, or `To be defined`.

    config is like:
        extra_versions: # versions that are not in the `SECURITY.md` but should still be consided
        audit: # if `True` check that the audit workflow run on the right branches
        backport_labels: # if `True` check the required backport labels exists
        branches: # if `True` check that the required branches exists
        rebuild: # if `False` not runs this check
          files: [] # list of workflow files to run to rebuild all the required branches

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

    with open("SECURITY.md") as open_file:
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
    if config.get("rebuild", False):
        assert isinstance(config["rebuild"], dict)
        if not _versions_rebuild(all_versions, config["rebuild"], full_config):
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

    branch = job.get("strategy", {}).get("matrix", {}).get("branch", [])
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
        with open(filename) as open_file:
            workflow = yaml.load(open_file, yaml.SafeLoader)

        branch_to_version_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))

        for name, job in workflow.get("jobs").items():
            audit_versions = _get_branch_matrix(job, branch_to_version_re)

            if all_versions != set(audit_versions):
                c2cciutils.error(
                    "versions",
                    "The workflow '{}', job '{}' does not have a branch matrix with the right list of "
                    "versions [{}] != [{}]".format(
                        filename,
                        name,
                        ", ".join(sorted(audit_versions)),
                        ", ".join(sorted(all_versions)),
                    ),
                )
                success = False
    return success


def _versions_rebuild(
    all_versions: Set[str],
    config: c2cciutils.configuration.ChecksVersionsRebuild,
    full_config: c2cciutils.configuration.Configuration,
) -> bool:
    """
    Check the rebuild branches match with the versions from the Security.md.

    Arguments:
        all_versions: All the required versions
        config: The check section configuration
        full_config: All the CI configuration
    """
    success = True
    rebuild_versions = []
    branch_to_version_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))

    for filename_ in config.get("files", []):
        filename = os.path.join(".github/workflows", filename_)
        if not os.path.exists(filename):
            c2cciutils.error(
                "versions",
                f"The rebuild file '{filename}' does not exists",
                filename,
            )
            success = False
        else:
            with open(filename) as open_file:
                workflow = yaml.load(open_file, yaml.SafeLoader)

            for _, job in workflow.get("jobs").items():
                rebuild_versions += _get_branch_matrix(job, branch_to_version_re)

    if all_versions != set(rebuild_versions):
        c2cciutils.error(
            "versions",
            "The rebuild workflows does not have the right list of versions in the branch matrix "
            "[{}] != [{}]".format(", ".join(sorted(rebuild_versions)), ", ".join(sorted(all_versions))),
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
                "The backport labels do not have the right list of versions [{}] != [{}]".format(
                    ", ".join(sorted(label_versions)), ", ".join(sorted(all_versions))
                ),
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
        url: Optional[str] = "https://api.github.com/repos/{repo}/branches".format(
            repo=c2cciutils.get_repository()
        )
        while url:
            branches_response = requests.get(
                url,
                params={"protected": "true"},
                headers=c2cciutils.add_authorization_header({"Accept": "application/vnd.github.v3+json"}),
            )
            branches_response.raise_for_status()
            url = None
            try:
                links = requests.utils.parse_header_links(  # type: ignore
                    branches_response.headers.get("Link", "")
                )
                if isinstance(links, list):
                    next_links = [link["url"] for link in links if link["rel"] == "next"]
                    if len(next_links) >= 1:
                        url = next_links[0]
            except Exception as exception:  # pylint: disable=broad-except
                c2cciutils.error(
                    "versions branches",
                    (
                        "error on reading Link header '{}': {}".format(
                            branches_response.headers.get("Link"), exception
                        )
                    ),
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
                "expected versions [{}] != [{}]".format(
                    ", ".join(sorted(branch_versions)), ", ".join(sorted(all_versions))
                ),
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
    del full_config

    try:
        cmd = ["codespell"]
        if args.fix:
            cmd.append("--write-changes")
        if os.path.exists("spell-ignore-words.txt"):
            cmd.append("--ignore-words=spell-ignore-words.txt")
        cmd += config.get("arguments", [])
        cmd.append("--")
        ignore_res = [re.compile(r) for r in config.get("ignore_re", [])]
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


def dependabot_config(
    config: c2cciutils.configuration.ChecksDependabotConfigurationConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check the Dependabot configuration.

    config can be False or dict, with:
        types:
          - filename: the filename to be checked
            echosystem: the dependabot package echosystem
        ignore_version_files: [...] # list of version files with path (Pipenv, Dockerfile, package.json)
            that shouldn't be checked.
        update_ignore: # ignore the rule for ignore used to ignore all the `@dependabot ignore`
          - directory: # The directory
            ecosystem: # The dependabot package echosystem

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    if not config:
        return True

    if not os.path.exists(".github/dependabot.yaml"):
        c2cciutils.error(
            "dependabot_config",
            "Missing Dependabot config file",
            ".github/dependabot.yaml",
        )
        return False

    success = True
    with open(".github/dependabot.yaml") as dependabot_file:
        dependabot = ruamel.yaml.round_trip_load(dependabot_file)  # type: ignore

    # Check that c2cciutils has update rule
    found = False
    for folder in ("/", "/ci"):
        for update in dependabot["updates"]:
            if update["package-ecosystem"] == "pip" and update["directory"] == folder:
                found = True
                break
    if not found:
        c2cciutils.error(
            "dependabot_config",
            "Missing configuration for c2cciutils",
            ".github/dependabot.yaml",
        )
        success = False

    # Check that we have have the rules for the files
    for depends_type in config.get("types", []):
        for version_file in (
            subprocess.check_output(
                ["git", "ls-files", depends_type["filename"], f"**/{depends_type['filename']}"]
            )
            .strip()
            .decode()
            .split("\n")
        ):
            if version_file == "":
                continue
            if version_file in config.get("ignore_version_files", []):
                continue
            folder = "/"
            if len(version_file) > len(depends_type["filename"]):
                folder += version_file[: -len(depends_type["filename"]) - 1]

            found = False
            for update in dependabot["updates"]:
                if update["package-ecosystem"] == depends_type["ecosystem"] and update["directory"] == folder:
                    found = True
                    break
            if not found:
                c2cciutils.error(
                    "dependabot_config",
                    f"Missing configuration for {version_file}, can be like:\n"
                    f'  - package-ecosystem: {depends_type["ecosystem"]}\n'
                    f'    directory: "{folder}"\n'
                    "    schedule:\n"
                    "      interval: daily\n"
                    "    ignore:\n"
                    "      - dependency-name: none",
                    ".github/dependabot.yaml",
                )
                success = False

    # update_ignore: True/False # Do a check that we ignoe everything on each rules to ignore all the
    # `@dependabot ignore`.
    if config.get("update_ignore", True) is not False:
        update_ignores = [] if config.get("update_ignore", True) is True else config.get("update_ignore")
        assert isinstance(update_ignores, list)

        for update in dependabot["updates"]:
            ignored = False
            for update_ignore in update_ignores:
                if (
                    update["package-ecosystem"] == update_ignore["package-ecosystem"]
                    and update["directory"] == update_ignore["directory"]
                ):
                    ignored = True
            if ignored:
                continue
            current_error = (
                f"The 'ignore' of '{update['package-ecosystem']}' in "
                f"'{update.get('directory', '/')}' should be:\n"
                "    ignore:\n"
                "      - dependency-name: none"
            )
            if "ignore" not in update:
                c2cciutils.error(
                    "dependabot_config",
                    current_error,
                    ".github/dependabot.yaml",
                    update.lc.line + 1,
                    update.lc.col + 1,
                )
                success = False
                continue
            if len(update["ignore"]) != 1:
                c2cciutils.error(
                    "dependabot_config",
                    current_error,
                    ".github/dependabot.yaml",
                    update["ignore"].lc.line + 1,
                    update["ignore"].lc.col + 1,
                )
                success = False
            if update["ignore"][0] != {"dependency-name": "none"}:
                c2cciutils.error(
                    "dependabot_config3",
                    current_error,
                    update["ignore"][0].lc.line + 1,
                    update["ignore"][0].lc.col + 1,
                )
                success = False

    return success


def setup(
    config: c2cciutils.configuration.ChecksSetupConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Check the typing options.

    in setup.cfg:
    [mypy]
    warn_redundant_casts = True
    warn_unused_ignores = True
    strict = True

    in setup.py:
    has the classifier Typing :: Typed

    config is like:
      ignore_file: [] # The files to ignore
      cfg: # what's required in the setup.cfg
        mypy:
            warn_redundant_casts: True
            warn_unused_ignores: True
            strict: True
      classifiers: # list of required classifiers
        - Typing :: Typed

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
    """
    del full_config, args

    success = True
    for filename in subprocess.check_output(["git", "ls-files", "setup.cfg"]).decode().split("\n"):
        if not filename or filename in config.get("ignore_file", []):
            continue
        setup_config = configparser.ConfigParser()
        setup_config.read(filename)
        for section, values in config.get("cfg", {}).items():
            if section not in setup_config:
                c2cciutils.error("setup", f"The section '{section}' is missing in {filename}", filename)
                success = False
                continue
            for key, value in values.items():
                if key not in setup_config[section]:
                    c2cciutils.error(
                        "setup", f"The key '{key}' in section '{section}' is missing in {filename}", filename
                    )
                    success = False
                    continue
                try:
                    if isinstance(value, bool):
                        if setup_config.getboolean(section, key) != value:
                            c2cciutils.error(
                                "setup",
                                f"The key '{key}' in section '{section}' in {filename} should have "
                                f"the value '{value}', instead of '{setup_config.getboolean(section, key)}'",
                                filename,
                            )
                            success = False
                    elif isinstance(value, int):
                        if setup_config.getint(section, key) != value:
                            c2cciutils.error(
                                "setup",
                                f"The key '{key}' in section '{section}' in {filename} should have "
                                f"the value '{value}', instead of '{setup_config.getint(section, key)}'",
                                filename,
                            )
                            success = False
                    elif isinstance(value, float):
                        if setup_config.getfloat(section, key) != value:
                            c2cciutils.error(
                                "setup",
                                f"The key '{key}' in section '{section}' in {filename} should have "
                                f"the value '{value}', instead of '{setup_config.getfloat(section, key)}'",
                                filename,
                            )
                            success = False
                    else:
                        if setup_config.get(section, key) != value:
                            c2cciutils.error(
                                "setup",
                                f"The key '{key}' in section '{section}' in {filename} should have "
                                f"the value '{value}', instead of '{setup_config.get(section, key)}'",
                                filename,
                            )
                            success = False
                except AttributeError as excepted_error:
                    c2cciutils.error(
                        "setup",
                        f"The key '{key}' in section '{section}' in {filename} has the wrong type: "
                        f"'{excepted_error}'",
                        filename,
                    )
                    success = False

            # TODO prospector

    for filename in subprocess.check_output(["git", "ls-files", "setup.py"]).decode().split("\n"):
        if not filename or filename in config.get("ignore_file", []):
            continue
        classifiers = subprocess.check_output(["python3", filename, "--classifiers"]).decode().split("\n")
        for classifier in config["classifiers"]:
            if classifier not in classifiers:
                c2cciutils.error(
                    "setup", f"The classifier '{classifier}' is required in {filename}", filename
                )
                success = False

    return success


def prettier(
    config: c2cciutils.configuration.ChecksPrettierConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Run prettier check on all the supported files.

    config is like:
      ignore_patterns_re: [] # list of regular expression we should ignore

    Arguments:
        config: The config
        full_config: The full config
        args: The parsed command arguments
    """
    del full_config

    ignore_patterns_compiled = [re.compile(p) for p in config.get("ignore_patterns_re", [])]
    success = True

    with c2cciutils.prettier.Prettier() as prettier_lib:
        for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
            if os.path.isfile(filename):
                accept = True
                for pattern in ignore_patterns_compiled:
                    if pattern.search(filename):
                        accept = False
                        break
                if accept:
                    info = prettier_lib.get_info(filename)
                    if info.get("info", {}).get("ignored", False):
                        continue
                    if not info.get("info", {}).get("inferredParser"):
                        continue
                    prettier_config = info["config"]
                    prettier_config["parser"] = info["info"]["inferredParser"]

                    if args.fix:
                        if not prettier_lib.format(filename, prettier_config):
                            success = False
                    else:
                        if not prettier_lib.check(filename, prettier_config):
                            success = False
    return success


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
