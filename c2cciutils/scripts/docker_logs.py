#!/usr/bin/env python3

import argparse
import os
import subprocess  # nosec
import sys
from datetime import datetime


def _print(message: str) -> None:
    print(message)
    sys.stdout.flush()


def main() -> None:
    """Print the list of running docker containers and their logs formatted for GitHub CI."""
    parser = argparse.ArgumentParser(
        description=("Print the list of running docker containers and their logs formatted for GitHub CI.")
    )
    parser.parse_args()

    if os.path.exists("docker-compose.yaml"):
        _print("::group::Docker Compose ps")
        subprocess.run(["docker-compose", "ps"], check=False)
        _print("::endgroup::")

    _print("::group::Docker ps")
    subprocess.run(["docker", "ps"], check=False)
    _print("::endgroup::")

    # Store in /tmp/docker-logs-timestamp the current timestamp to avoid printing same logs multiple times.
    timestamp_args = []
    if os.path.exists("/tmp/docker-logs-timestamp"):
        with open("/tmp/docker-logs-timestamp", encoding="utf-8") as timestamp_file:
            timestamp_args = [f"--since={timestamp_file.read().strip()}Z"]

    with open("/tmp/docker-logs-timestamp", "w", encoding="utf-8") as timestamp_file:
        timestamp_file.write(datetime.utcnow().isoformat())

    for name in (
        subprocess.run(
            ["docker", "ps", "--all", "--format", "{{ .Names }}"], check=True, stdout=subprocess.PIPE
        )
        .stdout.decode()
        .split("\n")
    ):
        if name:
            _print(f"::group::{name}: New logs")
            subprocess.run(["docker", "logs"] + timestamp_args + [name], check=False)
            _print("::endgroup::")


if __name__ == "__main__":
    main()
