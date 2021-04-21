# -*- coding: utf-8 -*-

import datetime
import json
import os.path
import re
import subprocess
import sys
from argparse import Namespace
from typing import Any, Callable, Dict, List

import safety.errors
import safety.formatter
import safety.safety
import safety.util
import yaml
from pipenv.patched import pipfile as pipfile_lib

import c2cciutils.checks


def print_versions(
    config: c2cciutils.configuration.PrintVersions,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Print the versions
    """
    del full_config, args

    print("::group::Versions")
    c2cciutils.print_versions(config)
    print("::endgroup::")
    print("::group::Simplified list of available python for asdf")
    all_versions: Dict[str, List[int]] = {}
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


def _python_ignores(directory: str) -> List[str]:
    ignores = []
    for filename in ("pip-cve-ignore", "pipenv-cve-ignore"):
        cve_filename = os.path.join(directory, filename)
        if os.path.exists(cve_filename):
            with open(cve_filename) as cve_file:
                ignores += [e.strip() for e in re.split(",|\n", cve_file.read()) if e.strip()]
    return ignores


def _safely(filename: str, read_packages: Callable[[str], List[str]]) -> bool:
    """
    Audit Python packages from `filename` using the `read_packages` to read it.
    """

    success = True
    for file in subprocess.check_output(["git", "ls-files"]).decode().strip().split("\n"):
        if os.path.basename(file) != filename:
            continue
        print("::group::Audit {}".format(file))
        directory = os.path.dirname(os.path.abspath(file))

        ignores = _python_ignores(directory)
        packages = read_packages(file)
        try:
            vulns = safety.safety.check(
                packages=packages,
                key="",
                db_mirror="",
                cached=True,
                ignore_ids=ignores,
                proxy={},
            )
            if vulns:
                success = False
                output_report = safety.formatter.report(
                    vulns=vulns,
                    full=True,
                    checked_packages=len(packages),
                )
                print(output_report)
                print("::endgroup::")
                print("With error")
            else:
                print("::endgroup::")
        except safety.errors.DatabaseFetchError:
            c2cciutils.error("pip", "Audit issue, see above", file)
            success = False
            print("::endgroup::")
            print("With error")
    return success


def pip(
    config: c2cciutils.configuration.AuditPip,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Audit all the `requirements.txt` files
    """
    del config, full_config, args

    def read_packages(filename: str) -> List[str]:
        with open(filename) as file_:
            return list(safety.util.read_requirements(file_, resolve=True))

    return _safely("requirements.txt", read_packages)


def pipfile(
    config: c2cciutils.configuration.AuditPipfileConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Audit all the `Pipfile`.

    config is like:
        sections: [...] # to select withch section we want to check
    """
    del full_config, args

    def read_packages(filename: str) -> List[str]:
        packages = []
        project = pipfile_lib.Pipfile.load(filename)
        for section in config["sections"]:
            for package, version in project.data[section].items():
                if isinstance(version, dict):
                    # We can have an path without any version
                    if "version" in version:
                        packages.append(
                            safety.util.Package(key=package, version=version["version"].lstrip("="))
                        )
                else:
                    packages.append(safety.util.Package(key=package, version=version.lstrip("=")))
        return packages

    return _safely("Pipfile", read_packages)


def pipfile_lock(
    config: c2cciutils.configuration.AuditPipfileLockConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
    """
    Audit all the `Pipfile.lock` files

    config is like:
        sections: [...] # to select withch section we want to check
    """
    del full_config, args

    def read_packages(filename: str) -> List[str]:
        packages = []
        with open(filename) as file_:
            data = json.load(file_)
            for section in config["sections"]:
                for package, package_data in data[section].items():
                    packages.append(
                        safety.util.Package(key=package, version=package_data["version"].lstrip("="))
                    )
        return packages

    return _safely("Pipfile.lock", read_packages)


def pipenv(
    config: c2cciutils.configuration.AuditPipenvConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
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
        ignores = _python_ignores(directory)
        if ignores:
            cmd += ["--ignore=" + ",".join(ignores)]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            if directory != "":
                subprocess.check_call(cmd, cwd=directory)
            else:
                subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            c2cciutils.error("pipenv", "Audit issue, see above", file)
            success = False
            print("::endgroup::")
            print("With error")
        print("::endgroup::")
    return success


def npm(
    config: c2cciutils.configuration.AuditNpmConfig,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
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
        subprocess_kwargs: Dict[str, Any] = {} if directory == "" else {"cwd": directory}
        subprocess.check_call(["npm", "install", "--package-lock-only"], **subprocess_kwargs)

        cve_file = os.path.join(directory, "npm-cve-ignore")
        all_ignores = []
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

        for vunerability in audit.get("advisories", audit.get("vulnerabilities")).values():
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
                        print("Path: " + " > ".join(path.split(">")))
                print("More info: " + vunerability.get("url"))
                print()

            c2cciutils.error(
                "npm", "We have some vulnerabilities see logs", file=os.path.join(directory, "package.json")
            )
            success = False

        if len(unused_ignores) > 0:
            c2cciutils.error(
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


def outdated_versions(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
) -> bool:
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
                c2cciutils.error(
                    "versions",
                    "The version '{}' is outdated, it can be set to "
                    "'Unsupported', 'Best effort' or 'To be defined'".format(row[version_index]),
                    "SECURITY.md",
                )
                success = False
    return success
