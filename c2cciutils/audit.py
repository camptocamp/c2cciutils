# -*- coding: utf-8 -*-

import datetime
import json
import os.path
import re
import subprocess
import sys

import yaml

import c2cciutils.checks


def print_versions(config, full_config, args):
    """
    Print the versions
    """
    del full_config, args

    print("::group::Versions")
    c2cciutils.print_versions(config)
    print("::endgroup::")
    print("::group::Simplified list of available python for asdf")
    all_versions = {}
    version_re = re.compile(r"^([0-9]+)\.([0-9]+)\.([0-9]+)$")
    for version in subprocess.check_output(["asdf", "list", "all", "python"]).decode().strip().split("\n"):
        version_match = version_re.match(version)
        if version_match is not None:
            full_minor_version = "{}.{}".format(version_match.group(1), version_match.group(2))
            all_versions.setdefault(full_minor_version, []).append(int(version_match.group(3)))
    for full_minor in sorted(all_versions.keys()):
        print("{}.{}".format(full_minor, max(all_versions[full_minor])))
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
                cmd += ["--ignore=" + e.strip() for e in cve_file.read().strip().split(",")]
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
                cmd += ["--ignore=" + cve_file.read().strip()]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            if directory != "":
                subprocess.check_call(cmd, cwd=directory)
            else:
                subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            c2cciutils.checks.error("pipenv", "Audit issue, see above", file)
            success = False
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return success


def npm(config, full_config, args):
    """
    Audit all the `package.json` files.

    config:
      cwe_ignore: list of ignored CWE
    """
    del full_config, args

    global_success = True
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        success = True
        if os.path.basename(file) != "package.json":
            continue
        print("::group::Audit " + file)
        directory = os.path.dirname(file)
        sys.stdout.flush()
        sys.stderr.flush()
        subprocess_kwargs = {} if directory == "" else {"cwd": directory}
        subprocess.check_call(["npm", "install", "--package-lock"], **subprocess_kwargs)

        cve_file = os.path.join(directory, "npm-cve-ignore")
        all_ignores = config.get("cve-ignore", [])
        unused_ignores = []
        if os.path.exists(cve_file):
            with open(cve_file) as cve_file_open:
                all_ignores = [int(e) for e in cve_file_open.read().strip().split(",")]
                unused_ignores = list(all_ignores)

        cwe_ignores = config.get("cwe_ignore", [])

        audit = json.loads(
            # Don't use check_output because audit will return an error on any vulnerabilities found
            # and we want to manage that ourself.
            subprocess.run(  # pylint: disable=subprocess-run-check
                ["npm", "audit", "--json"], stdout=subprocess.PIPE, **subprocess_kwargs
            ).stdout
        )
        vulnerabilities = {}
        if "error" in audit:
            print(yaml.dump(audit["error"], default_flow_style=False, Dumper=yaml.SafeDumper))
            print("::endgroup::")
            print("With error")
            return False

        for vunerability in audit["advisories"].values():
            if vunerability["cwe"] in cwe_ignores:
                continue
            if vunerability["id"] not in all_ignores:
                vulnerabilities[vunerability["id"]] = vunerability
            elif vunerability["id"] in unused_ignores:
                unused_ignores.remove(vunerability["id"])

        if vulnerabilities:
            first = True
            for vunerability in vulnerabilities.values():
                if not first:
                    print("=======================================================")
                print()
                print("Title: [{}] {}".format(vunerability.get("id"), vunerability.get("title")))
                print("Severity: " + vunerability.get("severity"))
                print("CWE: " + vunerability.get("cwe"))
                print("Vulnarable versions: " + vunerability.get("vulnerable_versions"))
                print("Patched versions: " + vunerability.get("patched_versions"))
                print("Recommendation: " + vunerability.get("recommendation"))
                for find in vunerability.get("findings", []):
                    print("Version: " + find["version"])
                    for path in find.get("paths", []):
                        print("Path: " + " > ".join(path.split(">")[2:]))
                print("More info: " + vunerability.get("url"))
                print()

            c2cciutils.checks.error(
                "npm", "We have some vulnerabilities see logs", file=os.path.join(directory, "package.json")
            )
            success = False

        if len(unused_ignores) > 0:
            c2cciutils.checks.error(
                "npm",
                "The following cve ignores are not present in the audit: {}".format(
                    ", ".join([str(e) for e in unused_ignores])
                ),
                file=cve_file,
            )
            success = False

        print("::endgroup::")
        if not success:
            print("With error")
        global_success = global_success and success
    return global_success


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
        if str_date not in ("Unsupported", "Best effort", "To be defined"):
            date = datetime.datetime.strptime(row[date_index], "%d/%m/%Y")
            if date < datetime.datetime.now():
                c2cciutils.checks.error(
                    "versions",
                    "The version '{}' is outdated, it can be set to "
                    "'Unsupported', 'Best effort' or 'To be defined'".format(row[version_index]),
                    "SECURITY.md",
                )
                success = False
    return success
