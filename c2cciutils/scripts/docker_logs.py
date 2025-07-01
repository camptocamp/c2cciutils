#!/usr/bin/env python3

import argparse
import datetime
import subprocess  # nosec
import sys
from pathlib import Path


def _print(message: str) -> None:
    print(message)
    sys.stdout.flush()


def main() -> None:
    """Print the list of running docker containers and their logs formatted for GitHub CI."""
    parser = argparse.ArgumentParser(
        description=("Print the list of running docker containers and their logs formatted for GitHub CI."),
    )
    parser.parse_args()

    if Path("docker-compose.yaml").exists():
        _print("::group::Docker Compose ps")
        subprocess.run(["docker", "compose", "ps", "--all"], check=False)  # noqa: S607
        _print("::endgroup::")

    _print("::group::Docker ps")
    subprocess.run(["docker", "ps"], check=False)  # noqa: S607
    _print("::endgroup::")

    # Store in /tmp/docker-logs-timestamp the current timestamp to avoid printing same logs multiple times.
    timestamp_args = []
    timestamp_file_path = Path("/tmp/docker-logs-timestamp")  # noqa: S108 # nosec
    if timestamp_file_path.exists():  # nosec
        with timestamp_file_path.open(encoding="utf-8") as timestamp_file:  # nosec
            timestamp_args = [f"--since={timestamp_file.read().strip()}Z"]

    with timestamp_file_path.open("w", encoding="utf-8") as timestamp_file:  # nosec
        timestamp_file.write(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())

    for name in (
        subprocess.run(  # noqa: S603,S607,RUF100
            ["docker", "ps", "--all", "--format", "{{ .Names }}"],  # noqa: S607
            check=True,
            stdout=subprocess.PIPE,
        )
        .stdout.decode()
        .split("\n")
    ):
        if name:
            _print(f"::group::{name}: New logs")
            subprocess.run(["docker", "logs", *timestamp_args, name], check=False)  # noqa: S603,S607
            _print("::endgroup::")


if __name__ == "__main__":
    main()
