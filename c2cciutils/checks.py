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
    Write a GitHub error or warn message

    See: https://docs.github.com/en/free-pro-team@latest/actions/reference/ \
        workflow-commands-for-github-actions#setting-an-error-message
    """
    result = "::{}".format(error_type)
    if file is not None:
        result += " file={}".format(file)
        if line is not None:
            result += ",line={}".format(line)
            if col is not None:
                result += ",col={}".format(col)
    result += ":: {}: {}".format(checker, message)
    print(result)


def print_config(config, full_config, args):
    """
    Print the config
    """
    del config, args

    print(yaml.dump(full_config, Dumper=yaml.SafeDumper))
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
    try:
        next(glob.iglob("**/*.py", recursive=True))
        python = True
    except StopIteration:
        pass

    try:
        for file_ in glob.iglob("**/*[0-9a-zA-z_-][0-9a-zA-z_-][0-9a-zA-z_-]", recursive=True):
            if os.path.isfile(file_):
                if magic.from_file(file_, mime=True) == "text/x-python":
                    python = True
                    break
    except StopIteration:
        pass

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
                if value is not None and properties[key] != value:
                    error(
                        "editorconfig",
                        "For pattern: {} the property '{}' is '{}' but should be '{}'.".format(
                            pattern, key, properties[key], value
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
        subprocess.check_call(["git", "--no-pager", "diff", "--check", git_ref])
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
        result = True

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
                                    result = False

        return result
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

    result = True
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
                result = False

            if job.get("timeout-minutes") is None:
                error(
                    "workflows",
                    "The workflow '{}', job '{}' runs on '{}' but it is blacklisted".format(
                        filename, name, job.get("runs-on")
                    ),
                    filename,
                )
                result = False

    return result


def required_workflows(config, full_config, args):
    """
    Test that we have the required workflow with the required element

    config is like:
        <filename>: # if set directly to `True` just check that the file is present, to `False`
                check nothing.
            runs_re: # rebular expresiion that we should have in a run, on one of the jobs.
            strategy-fail-fast: False # If present check the value of the `fail-fast`, on all the jobs.
            if: # if present check the value of the `if`, on all the jobs.
            noif: # if `True` theck that we don't have an `if`.
    """
    del full_config, args

    result = True
    for file_, conf in config.items():
        filename = os.path.join(".github/workflows", file_)
        if not os.path.exists(filename):
            error(
                "required_workflows",
                "The workflow '{}' is required".format(filename),
                filename,
            )
            result = False
            continue

        if isinstance(config, dict):
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
                    result = False
            if conf.get("noif", False):
                if "if" in job:
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' should not have a if".format(filename, name),
                        filename,
                    )
                    result = False
            if "strategy-fail-fast" in conf:
                if job.get("strategy", {}).get("fail-fast") != conf["strategy-fail-fast"]:
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' does not have the strategy/fail-fast as {}".format(
                            filename, name, conf["strategy-fail-fast"]
                        ),
                        filename,
                    )
                    result = False
            if "runs_re" in conf:
                for run in conf["runs_re"]:
                    corresponding_steps = [
                        step for step in job["steps"] if re.match(step.get("run"), run) is not None
                    ]
                    if len(corresponding_steps) == 0:
                        error(
                            "required_workflows",
                            "The workflow '{}', job '{}' doesn't have the step that runs '{}'.".format(
                                filename, name, run
                            ),
                            filename,
                        )
                        result = False
    return result


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
          file: [] # list of workflow files to run to rebuild all the required branches
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

    result = True
    all_versions = set(config.get("extra_versions", []))

    for row in security.data:
        str_date = row[date_index]
        if str_date != "Unsupported":
            all_versions.add(row[version_index])

    if config.get("audit", False):
        if not _versions_audit(all_versions, full_config):
            result = False
    if config.get("rebuild", False):
        if not _versions_rebuild(all_versions, config["rebuild"], full_config):
            result = False
    if config.get("backport_labels", False):
        if not _versions_backport_labels(all_versions, full_config):
            result = False
    if config.get("branches", False):
        if not _versions_branches(all_versions, full_config):
            result = False

    return result


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
    result = True
    filename = ".github/workflows/audit.yaml"
    if not os.path.exists(filename):
        error(
            "versions",
            "The file '{}' does not exists".format(filename),
            filename,
        )
        result = False
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
                        filename, name, ", ".join(all_versions), ", ".join(audit_versions)
                    ),
                    filename,
                )
                result = False
    return result


def _versions_rebuild(all_versions, config, full_config):
    """
    Check that the rebuild branches correspond to the version from the Security.md
    """
    result = True
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
            result = False
        else:
            with open(filename) as open_file:
                workflow = yaml.load(open_file, yaml.SafeLoader)

            for _, job in workflow.get("jobs").items():
                rebuild_versions += _get_branch_matrix(job, branch_to_version_re)

    if all_versions != set(rebuild_versions):
        error(
            "versions",
            "The rebuild workflows does not have the right list of versions in the branch matrix "
            "[{}] != [{}]".format(", ".join(rebuild_versions), ", ".join(all_versions)),
        )
        result = False
    return result


def _versions_backport_labels(all_versions, full_config):
    """
    Check that the backport labels correspond to the version from the Security.md
    """
    result = True
    label_versions = set()

    sys.stdout.flush()
    sys.stderr.flush()
    labels_responce = requests.get(
        "https://api.github.com/repos/{repo}/labels".format(repo=os.environ["GITHUB_REPOSITORY"]),
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer {}".format(
                os.environ["GITHUB_TOKEN"].strip()
                if "GITHUB_TOKEN" in os.environ
                else subprocess.check_output(["gopass", "show", "gs/ci/github/token/gopass"]).strip().decode()
            ),
        },
    )
    labels_responce.raise_for_status()

    label_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []), "backport ")
    for json_label in labels_responce.json():
        match = c2cciutils.match(json_label["name"], label_re)
        if match[0] is not None:
            label_versions.add(c2cciutils.get_value(*match))

    if all_versions != label_versions:
        error(
            "versions",
            "The backport labels do not have the right list of versions [{}] != [{}]".format(
                ", ".join(label_versions), ", ".join(all_versions)
            ),
        )
        result = False

    return result


def _versions_branches(all_versions, full_config):
    """
    Check that the branches correspond to the version from the Security.md
    """
    result = True
    branche_versions = set()

    sys.stdout.flush()
    sys.stderr.flush()
    branches_responce = requests.get(
        "https://api.github.com/repos/{repo}/branches".format(repo=os.environ["GITHUB_REPOSITORY"]),
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer {}".format(
                os.environ["GITHUB_TOKEN"].strip()
                if "GITHUB_TOKEN" in os.environ
                else subprocess.check_output(["gopass", "show", "gs/ci/github/token/gopass"]).strip().decode()
            ),
        },
    )
    branches_responce.raise_for_status()

    branche_re = c2cciutils.compile_re(full_config["version"].get("branch_to_version_re", []))
    for branche in branches_responce.json():
        match = c2cciutils.match(branche["name"], branche_re)
        if match[0] is not None:
            branche_versions.add(c2cciutils.get_value(*match))

    if len([v for v in all_versions if v not in branche_versions]) > 0:
        error(
            "versions",
            "The version from the branches does not correspond with expected versions [{}] != [{}]".format(
                ", ".join(branche_versions), ", ".join(all_versions)
            ),
        )
        result = False

    return result


def _get_python_files(ignore_patterns_re):
    """
    Get all the files in git that have the mime type text/x-python

    ignore_patterns_re: list of regular expression to be ignored
    """

    ignore_patterns_compiled = [re.compile(p) for p in ignore_patterns_re]
    result = []

    for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if magic.from_file(filename, mime=True) == "text/x-python":
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
            cmd += ["--color", "--diff"]
        cmd += _get_python_files(config.get("ignore_patterns_re", []))
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
        cmd += _get_python_files(config.get("ignore_patterns_re", []))
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
    del full_config, args

    try:
        cmd = ["codespell"]
        if os.path.exists("spell-ignore-words.txt"):
            cmd.append("--ignore-words=spell-ignore-words.txt")
        cmd += config.get("arguments", [])
        ignore_res = [re.compile(r) for r in config.get("ignore_re", [])]
        for filename in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
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
