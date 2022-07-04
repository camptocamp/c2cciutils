"""
Some utility functions for Docker images.
"""
import os
import subprocess  # nosec: B404
from typing import Dict, Optional, Tuple, cast

import yaml
from debian_inspector.version import Version


def get_dpkg_packages_versions(
    image: str, default_distribution: Optional[str] = None, default_release: Optional[str] = None
) -> Tuple[bool, Dict[str, Version]]:
    """
    Get the versions of the dpkg packages installed in the image.

    `get_dpkg_packages_versions("org/image:tag")` will return something like:
    (true, {"debian_11/api": "2.2.0", ...})

    Where `debian_11` corresponds on last path element for 'Debian 11'
    from https://repology.org/repositories/statistics
    """

    os_release_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/os-release"],
        stdout=subprocess.PIPE,
        check=True,
    )
    os_release = dict([e.split("=") for e in os_release_process.stdout.decode().split("\n") if e])

    lsb_release_process = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint=", image, "cat", "/etc/lsb-release"],
        stdout=subprocess.PIPE,
        check=True,
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
        check=True,
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
    Get the versions from the config file.
    """
    if os.path.exists("ci/dpkg-versions.yaml"):
        with open("ci/dpkg-versions.yaml", "r", encoding="utf-8") as versions_file:
            return cast(Dict[str, Dict[str, str]], yaml.load(versions_file.read(), Loader=yaml.SafeLoader))
    return {}


def check_versions(
    versions_config: Dict[str, str],
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

    for package, version in versions_image.items():
        if package not in versions_config:
            print(f"Package {package} is not in the config file for the image {image}")
            return False

        if Version.from_string(versions_config[package]) > version:
            print(
                f"Package {package} is older than the config file for the image {image}: "
                f"{versions_config[package]} > {version}."
            )
            return False

    return True
