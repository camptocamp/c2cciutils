# -*- coding: utf-8 -*-

import datetime
import json
import os.path
import subprocess
import sys

import c2cciutils.checks


def print_versions(config, full_config, args):
    """
    Print the versions
    """
    del full_config, args

    print("::group::Versions")
    c2cciutils.print_versions(config)
    print("::endgroup::")
    return True


def pip(config, full_config, args):
    """
    Audit all the `requirements.txt` files
    """
    del config, full_config, args

    success = True
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(file) != "requirements.txt":
            continue
        print("::group::Audit {}".format(file))
        directory = os.path.dirname(os.path.abspath(file))
        cmd = ["safety", "check", "--full-report", "--file=requirements.txt"]
        cve_file = os.path.join(directory, "pip-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file:
                cmd += ["--ignore=" + e.strip() for e in cve_file.read().decode().strip().split(",")]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            if directory != "":
                subprocess.check_call(cmd, cwd=directory)
            else:
                subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            c2cciutils.checks.error("pip", "Audit issue, see above", file)
            success = False
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return success


def pipenv(config, full_config, args):
    """
    Audit all the `Pipfile`.

    config is like:
        `python_versions`: []  # Python version of asdf environment the we should setup to be able to do
            the check
    """
    del full_config, args

    success = True
    init = False
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(file) != "Pipfile":
            continue
        if not init:
            print("::group::Init python versions: {}".format(", ".join(config.get("python_versions", []))))
            sys.stdout.flush()
            sys.stderr.flush()
            for version in config.get("python_versions", []):
                subprocess.check_call(["asdf", "install", "python", version])
            init = True
            print("::endgroup::")
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        cmd = ["pipenv", "check"]
        cve_file = os.path.join(directory, "pipenv-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file:
                cmd += ["--ignore=" + cve_file.read().decode().strip()]
        try:
            c2cciutils.checks.error("pienv", "Audit issue, see above", file)
            sys.stdout.flush()
            sys.stderr.flush()
            if directory != "":
                subprocess.check_call(cmd, cwd=directory)
            else:
                subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            success = False
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return success


def npm(config, full_config, args):
    """
    Audit all the `package.json` files.
    """
    del config, full_config, args

    success = True
    init = False
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(file) != "package.json":
            continue
        if not init:
            print("::group::Init")
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.check_call(["sudo", "npm", "install", "-g", "better-npm-audit", "npm"])
            init = True
            print("::endgroup::")
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess_kwargs = {} if directory == "" else {"cwd": directory}
        subprocess.check_call(["npm", "install", "--package-lock"], **subprocess_kwargs)
        cmd = ["node", "/usr/local/lib/node_modules/better-npm-audit", "audit"]
        cve_file = os.path.join(directory, "npm-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file:
                cmd += ["--ignore=" + cve_file.read().decode().strip()]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.check_call(cmd, **subprocess_kwargs)
        except subprocess.CalledProcessError:
            c2cciutils.checks.error("npm", "Audit issue, see above", file)
            subprocess.call(["npm", "audit"], **subprocess_kwargs)
            subprocess.call(["npm", "audit", "fix", "--force"], **subprocess_kwargs)
            subprocess.call(["git", "diff"], **subprocess_kwargs)
            subprocess.call(["git", "diff-index", "--quiet", "HEAD"], **subprocess_kwargs)
            success = False
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return success


def outdated_versions(config, full_config, args):
    """
    Check that the versions from the SECURITY.md are not outdated
    """
    del config, full_config

    repo = c2cciutils.get_repository().split("/")
    json_response = c2cciutils.graphql(
        "default_branch.graphql",
        {"name": repo[1], "owner": repo[0]},
    )

    if "errors" in json_response:
        raise RuntimeError(json.dumps(json_response["errors"], indent=2))
    if json_response["repository"]["defaultBranchRef"]["name"] != args.branch:
        return True

    success = True

    if not os.path.exists("SECURITY.md"):
        return False

    with open("SECURITY.md") as security_file:
        security = c2cciutils.security.Security(security_file.read())

    version_index = security.headers.index("Version")
    date_index = security.headers.index("Supported Until")

    for row in security.data:
        str_date = row[date_index]
        if str_date not in ("Unsupported", "Best effort"):
            date = datetime.datetime.strptime(row[date_index], "%d/%m/%Y")
            if date < datetime.datetime.now():
                c2cciutils.checks.error(
                    "versions",
                    "The version '{}' is outdated, she can be set to 'Unsupported' or 'Best effort'".format(
                        row[version_index]
                    ),
                    "SECURITY.md",
                )
                success = False
    return success
