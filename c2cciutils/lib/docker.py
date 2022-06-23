"""
Some utility functions for Docker images
"""
import os
import subprocess
from typing import Dict, Optional, Union

import yaml
from debian_inspector.version import Version


def get_dpkg_packages_versions(
    image: str, default_distribution: Optional[str] = None, default_release: Optional[str] = None
) -> Union[bool, Dict[str, Version]]:
    """
    Get the versions of the dpkg packages installed in the image
    """

    os_release_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/os-release"],
        stdout=subprocess.PIPE,
    )
    os_release = dict([e.split("=") for e in os_release_process.stdout.decode().split("\n") if e])

    lsb_release_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/lsb-release"],
        stdout=subprocess.PIPE,
    )
    lsb_release = dict([e.split("=") for e in lsb_release_process.stdout.decode().split("\n") if e])

    distribution = os_release.get("ID", lsb_release.get("DISTRIB_ID", default_distribution))
    release = os_release.get("VERSION_ID", lsb_release.get("DISTRIB_RELEASE", default_release))
    if distribution is None:
        print("Could not get the distribution of the image, you should provide a default distribution")
        return False, {}
    if release is None:
        print("Could not get the release of the image, you should provide a default release")
        return False, {}

    prefix = distribution.strip('"').lower() + "_" + release.strip('"').replace(".", "_") + "/"

    result: Dict[str, Version] = {}
    list_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "dpkg", "--list"],
        stdout=subprocess.PIPE,
    )
    for line in list_process.stdout.decode().split("\n"):
        ls = line.split()
        if len(ls) < 3 or ls[0] != "ii":
            continue
        name = ls[1]
        if name.endswith(":amd64"):
            name = name[:-6]
        result[f"{prefix}{name}"] = Version.from_string(ls[2])
    return True, result


def get_versions_config() -> Dict[str, Dict[str, str]]:
    """
    Get the versions from the config file
    """
    if os.path.exists("ci/dpkg-versions.yaml"):
        with open("ci/dpkg-versions.yaml", "r", encoding="utf-8") as versions_file:
            return yaml.load(versions_file.read(), Loader=yaml.SafeLoader)
    return {}


def check_version(
    version_config_full: Dict[str, Dict[str, str]],
    image: str,
    check: bool = True,
    default_distribution: Optional[str] = None,
    default_release: Optional[str] = None,
) -> bool:
    """
    Check if the versions are correct.

    The version of the image should be present in the config file.
    The version of the image shouldn't be older than the versions of the config file.

    This will also fill the config to be able to reuse it.
    """
    version_config = version_config_full.setdefault(image, {})
    result, version_image = get_dpkg_packages_versions(image, default_distribution, default_release)

    for package, version in version_image.items():
        if package not in version_config:
            if check:
                print(f"Package {package} is not in the config file for the image {image}")
                result = False
            version_config[package] = str(version)

        if Version.from_string(version_config[package]) > version:
            if check:
                print(
                    f"Package {package} is older than the config file for the image {image}: "
                    f"{version_config[package]} > {version}."
                )
                result = False
            version_config[package] = str(version)

    # Remove the old packages
    for package, version in list(version_config.items()):
        if package not in version_image:
            del version_config[package]

    return result
