# -*- coding: utf-8 -*-

import configparser
import glob
import os
import re
import subprocess
import sys

import magic
import requests
import yaml
from editorconfig import EditorConfigError, get_properties

import c2cciutils
import c2cciutils.security


def error(checker, message, file=None, line=None, col=None, error_type="error"):
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


def print_config(config, full_config, args):
    """
    Print the config
    """
    del config, args

    print(yaml.dump(full_config, default_flow_style=False, Dumper=yaml.SafeDumper))
    return True


def black_config(config, full_config, args):
    """
    Check the black configuration

    config is like:
        properties: # dictionary of properties to check
    """
    del full_config, args

    # If there is no python file the check is disabled
    python = False
    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.isfile(filename) and magic.from_file(filename, mime=True) == "text/x-python":
            python = True
            break

    if python:
        if not os.path.exists("pyproject.toml"):
            error(
                "black_config",
                "The file 'pyproject.toml' with a section tool.black is required",
                "pyproject.toml",
            )
            return False

        configp = configparser.ConfigParser()
        configp.read("pyproject.toml")
        if "tool.black" not in configp.sections():
            error(
                "black_config",
                "The 'tool.black' section is required in the 'pyproject.toml' file",
                "pyproject.toml",
            )
            return False

        if isinstance(config, dict):
            for key, value in config.get("properties", {}).items():
                if configp.get("tool.black", key) != value:
                    error(
                        "black_config",
                        "The property '{}' should have the value, '{}', but is '{}'".format(
                            key, value, configp.get("tool.black", key)
                        ),
                        "pyproject.toml",
                    )
    return True


def editorconfig(config, full_config, args):
    """
    Check the right editorconfig configuration

    config is like:
        properties:
          <file_pattern>: {} # dictionary of properties to check
    """
    del full_config, args

    success = True
    for pattern, wanted_properties in config.get("properties", {}).items():
        try:
            file_ = next(glob.iglob("**/" + pattern, recursive=True))
            properties = get_properties(os.path.abspath(file_))

            for key, value in wanted_properties.items():
                if value is not None and (key not in properties or properties[key] != value):
                    error(
                        "editorconfig",
                        "For pattern: {} the property '{}' is '{}' but should be '{}'.".format(
                            pattern, key, properties.get(key, ""), value
                        ),
                        ".editorconfig",
                    )
                    success = False
        except StopIteration:
            # If the pattern is not founf the check is disable for this pattern
            pass
        except EditorConfigError:
            error(
                "editorconfig",
                "Error occurred while getting EditorConfig properties",
                ".editorconfig",
            )
            return False
    return success


def gitattribute(config, full_config, args):
    """
    Check that we don't have any error with the gitattributes
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
        error(
            "gitattribute",
            "Error, see above",
        )
        return False


FNULL = open(os.devnull, "w")


def eof(config, full_config, args):
    """
    Check the files eof
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
                        "git check-attr -a '{}' | grep ' text: set'".format(filename),
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
                                    error(
                                        "eof",
                                        "No new line at end of '{}' file.".format(filename),
                                        filename,
                                    )
                                    success = False

        return success
    except subprocess.CalledProcessError:
        error(
            "eof",
            "Error, see above",
        )
        return False


def workflows(config, full_config, args):
    """
    Do some generic check on the workflows

    config is like:
        images_blacklist: [] # list of `runs-on` images to blacklist
        timeout: True # check that all the workflow have a timeout
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
                error(
                    "workflows",
                    "The workflow '{}', job '{}' runs on '{}' but it is blacklisted".format(
                        filename, name, job.get("runs-on")
                    ),
                    filename,
                )
                success = False

            if job.get("timeout-minutes") is None:
                error(
                    "workflows",
                    "The workflow '{}', job '{}' has no timeout".format(filename, name),
                    filename,
                )
                success = False

    return success


def required_workflows(config, full_config, args):
    """
    Test that we have the required workflow with the required element

    config is like:
        <filename>: # if set directly to `True` just check that the file is present, to `False`
                check nothing.
            steps:
              - run_re: # rebular expresiion that we should have in a run, on one of the jobs.
                env: # the list or required environment variable for this step
            strategy-fail-fast: False # If present check the value of the `fail-fast`, on all the jobs.
            if: # if present check the value of the `if`, on all the jobs.
            noif: # if `True` theck that we don't have an `if`.
    """
    del full_config, args

    success = True
    for file_, conf in config.items():
        if conf is False:
            continue

        filename = os.path.join(".github/workflows", file_)
        if not os.path.exists(filename):
            error(
                "required_workflows",
                "The workflow '{}' is required".format(filename),
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
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' does not have the following if '{}'".format(
                            filename, name, conf["if"]
                        ),
                        filename,
                    )
                    success = False
            if conf.get("noif", False):
                if "if" in job:
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' should not have a if".format(filename, name),
                        filename,
                    )
                    success = False
            if "strategy-fail-fast" in conf:
                if job.get("strategy", {}).get("fail-fast") != conf["strategy-fail-fast"]:
                    error(
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
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' doesn't have the step for:\n{}".format(
                            filename,
                            name,
                            yaml.dump(step_conf, default_flow_style=False, Dumper=yaml.SafeDumper).strip(),
                        ),
                        filename,
                    )
                    success = False
    return success


def versions(config, full_config, _):
    """
    Verify that various GitHub / CI tools versions or branches configuration match with versions
    from `SECURITY.md` file.
    The columns `Version` and `Supported Until` should be present.
    The `Supported Until` should contains dates formatted as `dd/mm/yyyy`, or `Unsupported`
    (we ignore those lines), or `Best effort`.

    config is like:
        extra_versions: # versions that are not in the `SECURITY.md` but should still be consided
        audit: # if `True` check that the audit workflow run on the right branches
        backport_labels: # if `True` check the required backport labels exists
        branches: # if `True` check that the required branches exists
        rebuild: # if `False` not runs this check
          files: [] # list of workflow files to run to rebuild all the required branches
    """

    # If the `SECURITY.md` file is not present the check is disabled.
    if not os.path.exists("SECURITY.md"):
        error("versions", "The file 'SECURITY.md' does not exists", "SECURITY.md", error_type="warning")
        return True

    with open("SECURITY.md") as open_file:
        security = c2cciutils.security.Security(open_file.read())

    for col in ("Version", "Supported Until"):
        if col not in security.headers:
            error(
                "versions",
                "The file 'SECURITY.md' does not have the column required '{}'".format(col),
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
        if not _versions_rebuild(all_versions, config["rebuild"], full_config):
            success = False
    if config.get("backport_labels", False):
        if not _versions_backport_labels(all_versions, full_config):
            success = False
    if config.get("branches", False):
        if not _versions_branches(all_versions, full_config):
            success = False

    return success


def _get_branch_matrix(job, branch_to_version_re):
    """
    Get the branches from a `strategy` `matrix`, and return the corresponding version.
    """

    branch = job.get("strategy", {}).get("matrix", {}).get("branch", [])
    return [c2cciutils.get_value(*c2cciutils.match(av, branch_to_version_re)) for av in branch]


def _versions_audit(all_versions, full_config):
    """
    Check that the audit branches correspond to the version from the Security.md
    """
    success = True
    filename = ".github/workflows/audit.yaml"
    if not os.path.exists(filename):
        error(
            "versions",
            "The file '{}' does not exists".format(filename),
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
                error(
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


def _versions_rebuild(all_versions, config, full_config):
    """
    Check that the rebuild branches correspond to the version from the Security.md
    """
    success = True
    rebuild_versions = []
    branch_to_version_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))

    for filename_ in config.get("files", []):
        filename = os.path.join(".github/workflows", filename_)
        if not os.path.exists(filename):
            error(
                "versions",
                "The rebuild file '{}' does not exists".format(filename),
                filename,
            )
            success = False
        else:
            with open(filename) as open_file:
                workflow = yaml.load(open_file, yaml.SafeLoader)

            for _, job in workflow.get("jobs").items():
                rebuild_versions += _get_branch_matrix(job, branch_to_version_re)

    if all_versions != set(rebuild_versions):
        error(
            "versions",
            "The rebuild workflows does not have the right list of versions in the branch matrix "
            "[{}] != [{}]".format(", ".join(sorted(rebuild_versions)), ", ".join(sorted(all_versions))),
        )
        success = False
    return success


def _versions_backport_labels(all_versions, full_config):
    """
    Check that the backport labels correspond to the version from the Security.md
    """
    success = True
    label_versions = set()

    sys.stdout.flush()
    sys.stderr.flush()
    labels_response = requests.get(
        "https://api.github.com/repos/{repo}/labels".format(repo=c2cciutils.get_repository()),
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer {}".format(
                os.environ["GITHUB_TOKEN"].strip()
                if "GITHUB_TOKEN" in os.environ
                else subprocess.check_output(["gopass", "show", "gs/ci/github/token/gopass"]).strip().decode()
            ),
        },
    )
    labels_response.raise_for_status()

    label_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []), "backport ")
    for json_label in labels_response.json():
        match = c2cciutils.match(json_label["name"], label_re)
        if match[0] is not None:
            label_versions.add(c2cciutils.get_value(*match))

    if all_versions != label_versions:
        error(
            "versions",
            "The backport labels do not have the right list of versions [{}] != [{}]".format(
                ", ".join(sorted(label_versions)), ", ".join(sorted(all_versions))
            ),
        )
        success = False

    return success


def _versions_branches(all_versions, full_config):
    """
    Check that the branches correspond to the version from the Security.md
    """
    success = True
    branch_versions = set()

    sys.stdout.flush()
    sys.stderr.flush()
    url = "https://api.github.com/repos/{repo}/branches".format(repo=c2cciutils.get_repository())
    while url:
        branches_response = requests.get(
            url,
            params={"protected": "true"},
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": "Bearer {}".format(
                    os.environ["GITHUB_TOKEN"].strip()
                    if "GITHUB_TOKEN" in os.environ
                    else subprocess.check_output(["gopass", "show", "gs/ci/github/token/gopass"])
                    .strip()
                    .decode()
                ),
            },
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
            print(
                "WARNING: error on reading Link header '{}': {}".format(
                    branches_response.headers.get("Link"), exception
                )
            )

        branch_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))
        for branch in branches_response.json():
            match = c2cciutils.match(branch["name"], branch_re)
            if match[0] is not None:
                branch_versions.add(c2cciutils.get_value(*match))

    if len([v for v in all_versions if v not in branch_versions]) > 0:
        error(
            "versions",
            "The version from the protected branches does not correspond with "
            "expected versions [{}] != [{}]".format(
                ", ".join(sorted(branch_versions)), ", ".join(sorted(all_versions))
            ),
        )
        success = False

    return success


def _get_python_files(ignore_patterns_re):
    """
    Get all the files in git that have the mime type text/x-python

    ignore_patterns_re: list of regular expression to be ignored
    """

    ignore_patterns_compiled = [re.compile(p) for p in ignore_patterns_re]
    result = []

    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.isfile(filename) and magic.from_file(filename, mime=True) == "text/x-python":
            accept = True
            for pattern in ignore_patterns_compiled:
                if pattern.search(filename):
                    accept = False
                    break
            if accept:
                result.append(filename)
    return result


def black(config, full_config, args):
    """
    Run black check on all files including Python files without .py extension

    config is like:
      ignore_patterns_re: [] # list of regular expression we should ignore
    """
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        cmd = ["black"]
        if not args.fix:
            cmd += ["--color", "--diff", "--check"]
        cmd.append("--")
        python_files = _get_python_files(config.get("ignore_patterns_re", []))
        cmd += python_files
        if len(python_files) > 0:
            subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        error(
            "black",
            "Error, see above",
        )
        return False


def isort(config, full_config, args):
    """
    Run isort check on all files including Python files without .py extension

    config is like:
      ignore_patterns_re: [] # list of regular expression we should ignore
    """
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        cmd = ["isort"]
        if args.fix:
            cmd.append("--apply")
        else:
            cmd += ["--check-only", "--diff"]
        cmd.append("--")
        python_files = _get_python_files(config.get("ignore_patterns_re", []))
        cmd += python_files
        if len(python_files) > 0:
            subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError:
        error(
            "isort",
            "Error, see above",
        )
        return False


def codespell(config, full_config, args):
    """
    Run codespell check on all files

    If therer is an `spell-ignore-words.txt` file we consider it with ignore word

    config is like:
        ignore_re: [] # list of patterns to be ignored
        arguments: [] # codespell arguments
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
        error(
            "codespell",
            "Error, see above",
        )
        return False


def print_versions(config, full_config, args):
    """
    Print some tools version
    """
    del full_config, args

    return c2cciutils.print_versions(config)
