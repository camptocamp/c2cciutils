#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import glob
import os.path
import subprocess
import sys

import c2cciutils.checks


def pip(_):
    error = False
    for file in glob.glob("**/requirements.txt", recursive=True):
        print("::group::Audit {}".format(file))
        directory = os.path.dirname(os.path.abspath(file))
        cmd = ["/usr/local/bin/safety", "check", "--full-report", "--file=requirements.txt"]
        cve_file = os.path.join(directory, "pip-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as f:
                cmd += ["--ignore=" + e.strip() for e in f.read().decode().strip().split(",")]
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


def pipenv(config):
    error = False
    init = False
    for file in glob.glob("**/Pipfile", recursive=True):
        if not init:
            sys.stdout.flush()
            sys.stderr.flush()
            for version in config.get("python_version", []):
                subprocess.check_call(["asdf", "install", "python", version])
            init = True
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        cmd = ["pipenv", "check"]
        cve_file = os.path.join(directory, "pipenv-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as f:
                cmd += ["--ignore=" + f.read().decode().strip()]
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


def npm(_):
    error = False
    init = False
    for file in glob.glob("**/package.json", recursive=True):
        if not init:
            sys.stdout.flush()
            sys.stderr.flush()
            subprocess.check_call(["sudo", "npm", "install", "-g", "better-npm-audit", "npm"])
            init = True
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess.check_call(["npm", "install", "--package-lock"], cwd=directory)
        cmd = ["node", "/usr/local/lib/node_modules/better-npm-audit", "audit"]
        cve_file = os.path.join(directory, "npm-cve-ignore")
        if os.path.exists(cve_file):
            with open(cve_file) as f:
                cmd += ["--ignore=" + f.read().decode().strip()]
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


def outdated_versions(_):
    """
    Check that the versions are not outdated
    """
    error = False

    if not os.path.exists("SECURITY.md"):
        return

    with open("SECURITY.md") as f_:
        security = c2cciutils.security.Security(f_.read())

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


def main() -> None:
    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    error = False
    for key, check in (
        ("pip", pip),
        ("pipenv", pipenv),
        ("npm", npm),
        ("outdated_versions", outdated_versions),
    ):
        conf = config.get(key, False)
        if conf:
            print("Run audit {}".format(key))
            if check(conf) is True:
                error = True
    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
