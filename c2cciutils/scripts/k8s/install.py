#!/usr/bin/env python3

import argparse
import subprocess  # nosec
import sys

import requests


def _print(message: str) -> None:
    print(message)
    sys.stdout.flush()


def main() -> None:
    """Get some logs to from k8s."""
    parser = argparse.ArgumentParser(description="Install k3d/k3s and create a cluster.")
    _ = parser.parse_args()

    _print("::group::Install")
    response = requests.get("https://raw.githubusercontent.com/rancher/k3d/main/install.sh", timeout=30)
    subprocess.run(["bash"], env={"TAG": "v4.4.8"}, check=True, input=response.content)
    _print("::endgroup::")

    _print("::group::Create cluster")
    subprocess.run(
        [
            "k3d",
            "cluster",
            "create",
            "test-cluster",
            "--no-lb",
            "--no-hostip",
            "--no-rollback",
            "--k3s-server-arg",
            "--no-deploy=traefik,servicelb,metrics-server",
        ],
        check=True,
    )
    _print("::endgroup::")


if __name__ == "__main__":
    main()
