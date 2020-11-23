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

import c2cciutils.security


def error(checker, message, file=None, line=None, col=None, error_type="error"):
    """
    Write a github error or warn message
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


def print_versions(config, full_config):
    """
    Print some tools version
    """
    del full_config
    for version in config.get("versions", []):
        try:
            current_version = subprocess.check_output(version.get("cmd", [])).decode()
            print("{}{}".format(version.get("prefix", ""), current_version))
        except PermissionError as exeption:
            print("{}: not allowd cmd: {}".format(version.get("name"), exeption))
        except subprocess.CalledProcessError as exeption:
            print("{}: no present: ".format(version.get("name")), exeption)


def print_config(_, full_config):
    """
    Print the config
    """
    print(yaml.dump(full_config, Dumper=yaml.SafeDumper))


def black_config(config, _):
    """
    Check the black configuration
    """
    python = False
    try:
        next(glob.iglob("**/.py", recursive=True))
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
            return True

        configp = configparser.ConfigParser()
        configp.read("pyproject.toml")
        if "tool.black" not in configp.sections():
            error(
                "black_config",
                "The 'tool.black' section is required in the 'pyproject.toml' file",
                "pyproject.toml",
            )
            return True

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
    return False


def editorconfig(config, _):
    """
    Check the right editorconfig configuration
    """
    result = False
    for patern, wanted_properties in config.get("properties", {}).items():
        try:
            file_ = next(glob.iglob("**/" + patern, recursive=True))
            properties = get_properties(os.path.abspath(file_))

            for key, value in wanted_properties.items():
                if value is not None and properties[key] != value:
                    error(
                        "editorconfig",
                        "For pattern: {} the property '{}' is '{}' but should be '{}'.".format(
                            patern, key, properties[key], value
                        ),
                        ".editorconfig",
                    )
                    result = True
        except StopIteration:
            pass
        except EditorConfigError:
            error(
                "editorconfig",
                "Error occurred while getting EditorConfig properties",
                ".editorconfig",
            )
            return True
    return result


def gitattribute(config, full_config):
    """
    Check that we don't have any error with the gitattributes
    """
    del config
    del full_config
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
        return False
    except subprocess.CalledProcessError:
        error(
            "gitattribute",
            "Error, see above",
        )
        return True


FNULL = open(os.devnull, "w")


def eof(config, full_config):
    """
    Check the files eof
    """
    del config
    del full_config
    try:
        result = False

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
                                error(
                                    "eof",
                                    "No new line at end of '{}' file.".format(filename),
                                    filename,
                                )
                                result = True

        return result
    except subprocess.CalledProcessError:
        error(
            "eof",
            "Error, see above",
        )
        return True


def workflows(config, _):
    """
    Do some generic check on the workflows
    """
    result = False
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
                result = True

            if job.get("timeout-minutes") is None:
                error(
                    "workflows",
                    "The workflow '{}', job '{}' runs on '{}' but it is blacklisted".format(
                        filename, name, job.get("runs-on")
                    ),
                    filename,
                )
                result = True

    return result


def required_workflows(config, _):
    """
    Test that we have the requred workflow with the required element
    """
    result = False
    for file_, conf in config.items():
        filename = os.path.join(".github/workflows", file_)
        if not os.path.exists(filename):
            error(
                "required_workflows",
                "The workflow '{}' is required".format(filename),
                filename,
            )
            result = True
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
                    result = True
            if "strategy-fail-fast" in conf:
                if job.get("strategy", {}).get("fail-fast") != conf["strategy-fail-fast"]:
                    error(
                        "required_workflows",
                        "The workflow '{}', job '{}' does not have the strategy/fail-fast as {}".format(
                            filename, name, conf["strategy-fail-fast"]
                        ),
                        filename,
                    )
                    result = True
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
                        result = True
    return result


def versions(config, full_config):
    """
    Check that all the versions corresponds
    """
    if not os.path.exists("SECURITY.md"):
        error(
            "versions",
            "The file 'SECURITY.md' does not exists",
            "SECURITY.md",
        )
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
            return True

    version_index = security.headers.index("Version")
    date_index = security.headers.index("Supported Until")

    result = False
    all_versions = {"master"}

    for row in security.data:
        str_date = row[date_index]
        if str_date != "Unsupported":
            all_versions.add(row[version_index])

    if config.get("audit", False):
        if _audit(all_versions, full_config):
            result = True
    if config.get("rebuild", False):
        if _rebuild(all_versions, config["rebuild"], full_config):
            result = True
    if config.get("backport_tags", False):
        if _backport_tags(all_versions, full_config):
            result = True
    if config.get("branches", False):
        if _branches(all_versions, full_config):
            result = True

    return result


def _get_branch_matrix(job, full_config):
    branch = job.get("strategy", {}).get("matrix").get("branch", [])
    return [
        "master"
        if av == "master"
        else c2cciutils.convert(av, full_config["version"].get("branch_to_version_re"))
        for av in branch
    ]


def _audit(all_versions, full_config):
    """
    Check that the audit branches corresponds to the version from the Security.md
    """
    result = False
    filename = ".github/workflows/audit.yaml"
    if not os.path.exists(filename):
        error(
            "versions",
            "The file '{}' does not exists".format(filename),
            filename,
        )
        result = True
    else:
        with open(filename) as open_file:
            workflow = yaml.load(open_file, yaml.SafeLoader)

        for name, job in workflow.get("jobs").items():
            audit_versions = _get_branch_matrix(job, full_config)

            if all_versions != set(audit_versions):
                error(
                    "versions",
                    "The workflow '{}', job '{}' does not have a branch matrix with the right list of "
                    "versions [{}]".format(filename, name, ", ".join(all_versions)),
                    filename,
                )
                result = True
    return result


def _rebuild(all_versions, config, full_config):
    """
    Check that the rebuild branches corresponds to the version from the Security.md
    """
    result = False
    rebuild_versions = []
    for filename_ in config.get("files", []):
        filename = os.path.join(".github/workflows", filename_)
        if not os.path.exists(filename):
            error(
                "versions",
                "The rebuild file '{}' does not exists".format(filename),
                filename,
            )
            result = True
        else:
            with open(filename) as open_file:
                workflow = yaml.load(open_file, yaml.SafeLoader)

            for _, job in workflow.get("jobs").items():
                rebuild_versions += _get_branch_matrix(job, full_config)

    if all_versions != set(rebuild_versions):
        error(
            "versions",
            "The rebuild workflows does not have the right list of versions in the branch matrix "
            "[{}] != [{}]".format(", ".join(rebuild_versions), ", ".join(all_versions)),
        )
        result = True
    return result


def _backport_tags(all_versions, full_config):
    """
    Check that the backport tags corresponds to the version from the Security.md
    """
    result = False
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

    label_re = full_config["version"]["branch_re"]
    if label_re[0] == "^":
        label_re = label_re[1:]
    if label_re[-1] != "$":
        label_re += "$"
    backport_prefix = "^backport "
    label_re = re.compile(backport_prefix + label_re)

    for json_label in labels_responce.json():
        if json_label["name"] == "backport master":
            label_versions.add("master")

        if label_re.match(json_label["name"]):
            label_versions.add(
                c2cciutils.convert(
                    json_label["name"][len(backport_prefix) - 1 :],
                    full_config["version"].get("branch_to_version_re"),
                )
            )

    if all_versions != label_versions:
        error(
            "versions",
            "The backport labels does not have the right list of versions [{}] != [{}]".format(
                ", ".join(label_versions), ", ".join(all_versions)
            ),
        )
        result = True

    return result


def _branches(all_versions, full_config):
    """
    Check that the branches corresponds to the version from the Security.md
    """
    result = False
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

    branches_re = full_config["version"]["branch_re"]
    if branches_re[0] != "^":
        branches_re = "^" + branches_re
    if branches_re[-1] != "$":
        branches_re += "$"
    branches_re = re.compile(branches_re)

    for branche in branches_responce.json():
        if branche["name"] == "master":
            branche_versions.add("master")
        if branches_re.match(branche["name"]):
            branche_versions.add(
                c2cciutils.convert(branche["name"], full_config["version"].get("branch_to_version_re"))
            )

    if all_versions != branche_versions:
        error(
            "versions",
            "The version from the branches does not corresponds with expected versions [{}] != [{}]".format(
                ", ".join(branche_versions), ", ".join(all_versions)
            ),
        )
        result = True

    return result


def black(config, full_config):
    """
    Do the black check
    """
    del config
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess.check_call(["black", "--color", "--diff", "."])
        return False
    except subprocess.CalledProcessError:
        error(
            "black",
            "Error, see above",
        )
        return True


def isort(config, full_config):
    """
    Do the isort check
    """
    del config
    del full_config

    try:
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess.check_call(["isort", "--check-only", "--diff", "--recursive", "."])
        return False
    except subprocess.CalledProcessError:
        error(
            "isort",
            "Error, see above",
        )
        return True
