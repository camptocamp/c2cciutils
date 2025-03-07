#!/usr/bin/env python3

import argparse
import subprocess  # nosec
import sys

import applications_download

import c2cciutils
import c2cciutils.configuration


def _print(message: str) -> None:
    print(message)
    sys.stdout.flush()


def main() -> None:
    """Get some logs to from k8s."""
    parser = argparse.ArgumentParser(description="Install k3d/k3s and create a cluster.")
    _ = parser.parse_args()

    config = c2cciutils.get_config()

    _print("::group::Install")
    apps = applications_download.Applications()
    apps.install("k3d-io/k3d")
    _print("::endgroup::")

    _print("::group::Create cluster")
    for cmd in (
        config.get("k8s", {})
        .get("k3d", {})
        .get("install-commands", c2cciutils.configuration.K3D_INSTALL_COMMANDS_DEFAULT)
    ):
        subprocess.run(cmd, check=True)  # noqa: S603
    _print("::endgroup::")


if __name__ == "__main__":
    main()
