# -*- coding: utf-8 -*-

import datetime
import glob
import os.path
import subprocess
import sys

import c2cciutils.checks


def print_versions(config, _):
    print("::group::Versions")
    c2cciutils.print_versions(config)
    print("::endgroup::")


def pip(config, full_config):
    """
    Audit all the `requirements.txt` files
    """
    del config, full_config

    error = False
    for file in glob.glob("**/requirements.txt", recursive=True):
        print("::group::Audit {}".format(file))
        directory = os.path.dirname(os.path.abspath(file))
        cmd = ["/usr/local/bin/safety", "check", "--full-report", "--file=requirements.txt"]
        cve_file = os.path.join(directory, "pip-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file:
                cmd += ["--ignore=" + e.strip() for e in cve_file.read().decode().strip().split(",")]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.check_call(cmd, cwd=directory)
        except subprocess.CalledProcessError:
            c2cciutils.checks.error("pip", "Audit issue, see above", file)
            error = True
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return error


def pipenv(config, _):
    """
    Audit all the `Pipfile`.

    config is like:
        `python_versions`: []  # Python version of asdf environment the we should setup to be able to do
            the check
    """
    error = False
    init = False
    for file in glob.glob("**/Pipfile", recursive=True):
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
            subprocess.check_call(cmd, cwd=directory)
        except subprocess.CalledProcessError:
            error = True
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return error


def npm(config, full_config):
    """
    Audit all the `package.json` files.
    """
    del config, full_config

    error = False
    init = False
    for file in glob.glob("**/package.json", recursive=True):
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
        subprocess.check_call(["npm", "install", "--package-lock"], cwd=directory)
        cmd = ["node", "/usr/local/lib/node_modules/better-npm-audit", "audit"]
        cve_file = os.path.join(directory, "npm-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file:
                cmd += ["--ignore=" + cve_file.read().decode().strip()]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.check_call(cmd, cwd=directory)
        except subprocess.CalledProcessError:
            c2cciutils.checks.error("npm", "Audit issue, see above", file)
            subprocess.call(["npm", "audit"], cwd=directory)
            subprocess.call(["npm", "audit", "fix", "--force"], cwd=directory)
            subprocess.call(["git", "diff"], cwd=directory)
            subprocess.call(["git", "diff-index", "--quiet", "HEAD"], cwd=directory)
            error = True
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return error


def outdated_versions(config, full_config):
    """
    Check that the versions from the SECURITY.md are not outdated
    """
    del config, full_config

    error = False

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
                error = True
    return error
