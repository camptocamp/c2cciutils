"""
Some utility functions for Docker images.
"""

import os
import subprocess  # nosec: B404
from typing import Optional, cast

import yaml
from debian_inspector.version import Version

import c2cciutils.configuration


def get_dpkg_packages_versions(
    image: str,
    default_distribution: Optional[str] = None,
    default_release: Optional[str] = None,
) -> tuple[bool, dict[str, Version]]:
    """
    Get the versions of the dpkg packages installed in the image.

    `get_dpkg_packages_versions("org/image:tag")` will return something like:
    (true, {"debian_11/api": "2.2.0", ...})

    Where `debian_11` corresponds on last path element for 'Debian 11'
    from https://repology.org/repositories/statistics
    """

    dpkg_configuration = c2cciutils.get_config().get("dpkg", {})

    os_release = {}
    try:
        os_release_process = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/os-release"],
            stdout=subprocess.PIPE,
            check=True,
        )
        os_release = dict([e.split("=") for e in os_release_process.stdout.decode().split("\n") if e])
    except subprocess.CalledProcessError:
        print("Info: /etc/os-release not found in the image")

    lsb_release = {}
    try:
        lsb_release_process = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/lsb-release"],
            stdout=subprocess.PIPE,
            check=True,
        )
        lsb_release = dict([e.split("=") for e in lsb_release_process.stdout.decode().split("\n") if e])
    except subprocess.CalledProcessError:
        print("Info: /etc/lsb-release not found in the image")

    distribution = os_release.get("ID", lsb_release.get("DISTRIB_ID", default_distribution))
    release = os_release.get("VERSION_ID", lsb_release.get("DISTRIB_RELEASE", default_release))
    if distribution is None:
        print("Could not get the distribution of the image, you should provide a default distribution")
        return False, {}
    if release is None:
        print("Could not get the release of the image, you should provide a default release")
        return False, {}

    distribution_final = distribution.strip('"').lower()
    release_final = release.strip('"').replace(".", "_")
    prefix = f"{distribution_final}_{release_final}/"
    print(f"Found distribution '{distribution_final}', release '{release_final}'.")

    if distribution_final == "ubuntu" and release_final == "18_04":
        print("Warning: Ubuntu 18.04 is not supported")
        return False, {}

    package_version: dict[str, Version] = {}
    packages_status_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "dpkg", "--status"],
        stdout=subprocess.PIPE,
        check=True,
    )
    packages_status_1 = packages_status_process.stdout.decode().split("\n")
    packages_status_2 = [e.split(": ", maxsplit=1) for e in packages_status_1]
    packages_status = [e for e in packages_status_2 if len(e) == 2]
    package = None
    version = None
    for name, value in packages_status:
        if name == "Package":
            if package is not None:
                if version is None:
                    print(f"Error: Missing version for package {package}")
                else:
                    if package not in dpkg_configuration.get("ignored_packages", []):
                        package = dpkg_configuration.get("packages_mapping", {}).get(package, package)
                        if package in package_version and version != package_version[package]:
                            print(
                                f"The package {package} has different version ({package_version[package]} != {version})"
                            )
                        if package not in ("base-files",):
                            package_version[package] = version
            package = value
            version = None
        if name == "Version" and version is None:
            version = Version.from_string(value)

    return True, {f"{prefix}{k}": v for k, v in package_version.items()}


def get_versions_config() -> tuple[dict[str, dict[str, str]], bool]:
    """
    Get the versions from the config file.
    """
    if os.path.exists("ci/dpkg-versions.yaml"):
        with open("ci/dpkg-versions.yaml", encoding="utf-8") as versions_file:
            return (
                cast(dict[str, dict[str, str]], yaml.load(versions_file.read(), Loader=yaml.SafeLoader)),
                True,
            )
    return {}, False


def check_versions(
    versions_config: dict[str, str],
    image: str,
    default_distribution: Optional[str] = None,
    default_release: Optional[str] = None,
) -> bool:
    """
    Check if the versions are correct.

    The versions of packages in the image should be present in the config file.
    The versions of packages in the image shouldn't be older than the versions of the config file.
    """

    result, versions_image = get_dpkg_packages_versions(image, default_distribution, default_release)
    if not result:
        return False

    success = True
    for package, version in versions_image.items():
        if package not in versions_config:
            print(f"Package {package} with version {version} is not in the config file for the image {image}")
            success = False
        elif Version.from_string(versions_config[package]) > version:
            print(
                f"Package {package} is older than the config file for the image {image}: "
                f"{versions_config[package]} > {version}."
            )
            success = False

    return success
