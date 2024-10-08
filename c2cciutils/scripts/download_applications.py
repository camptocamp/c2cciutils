#!/usr/bin/env python3

import argparse
import os
import subprocess  # nosec
import tarfile
import urllib
from glob import glob
from io import BytesIO
from typing import Optional, cast

import requests
import yaml

from c2cciutils import applications_definition


def main() -> None:
    """Download applications from GitHub releases or any other URLs to the ~/.local/bin folder."""
    argparser = argparse.ArgumentParser(
        description="""Download applications from GitHub releases or any other URLs to the ~/.local/bin folder.
            Based on tow files, the first contains the information about from where to download the applications,
            how to extract the application from the archive, and the executable name.
            The second file contains the versions of the applications to download,
            this file is usually updated by Renovate."""
    )
    argparser.add_argument("--applications-file", required=True)
    argparser.add_argument("--versions-file", required=True)
    args = argparser.parse_args()

    with open(args.versions_file, encoding="utf-8") as config_file:
        versions = cast(dict[str, str], yaml.load(config_file, Loader=yaml.SafeLoader))
    with open(args.applications_file, encoding="utf-8") as config_file:
        applications = cast(
            applications_definition.ApplicationsConfiguration, yaml.load(config_file, Loader=yaml.SafeLoader)
        )
    download_applications(applications, versions)


def download_c2cciutils_applications(name: Optional[str] = None) -> None:
    """Download the applications defined in the c2cciutils package."""
    with open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "applications-versions.yaml"),
        encoding="utf-8",
    ) as config_file:
        versions = cast(dict[str, str], yaml.load(config_file, Loader=yaml.SafeLoader))
    with open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "applications.yaml"), encoding="utf-8"
    ) as config_file:
        applications = cast(
            applications_definition.ApplicationsConfiguration, yaml.load(config_file, Loader=yaml.SafeLoader)
        )
    if name is not None:
        applications = {name: applications[name]}
    download_applications(applications, versions)


def download_applications(
    applications: applications_definition.ApplicationsConfiguration, versions: dict[str, str]
) -> None:
    """Download the versions of applications specified in the configuration."""
    bin_path = os.path.join(os.environ["HOME"], ".local", "bin")
    if not os.path.exists(bin_path):
        os.makedirs(bin_path)

    for key, app in applications.items():
        # The versions file is used to don't re-download an already downloaded application
        version_file = os.path.join(bin_path, f"{app['to-file-name']}-version-{versions[key]}")
        if not os.path.exists(version_file):
            print(f"Download {app['to-file-name']} version {versions[key]}")
            version = versions[key]
            version_quote = urllib.parse.quote_plus(version)
            params = {
                "version": version,
                "version_quote": version_quote,
                "short_version": version.lstrip("v"),
            }
            response = requests.get(
                app.get(
                    "url-pattern",
                    f"https://github.com/{key}/releases/download/{version_quote}/{app.get('get-file-name', '')}",
                ).format(**params),
                timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
            )
            response.raise_for_status()

            if app.get("type") == "tar":
                with tarfile.open(fileobj=BytesIO(response.content)) as tar:
                    extracted_file = tar.extractfile(app["tar-file-name"])
                    assert extracted_file is not None
                    content = extracted_file.read()
            else:
                content = response.content

            with open(os.path.join(bin_path, app["to-file-name"]), "wb") as destination_file:
                destination_file.write(content)

            for command in app.get("finish-commands", []):
                subprocess.run(command, check=True, cwd=bin_path)

            for file_name in glob(f"{app['to-file-name']}-version-*"):
                os.remove(file_name)
            with open(version_file, "w", encoding="utf-8") as _:
                pass


if __name__ == "__main__":
    main()
