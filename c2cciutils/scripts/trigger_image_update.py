#!/usr/bin/env python3

"""
Trigger an image update on the argocd repository.
"""

import argparse
import os.path
import random
import subprocess  # nosec
import sys
from typing import List

import requests
import yaml


def main() -> None:
    """
    Trigger an image update on the argocd repository.

    Only the branch present in the HELM_RELEASE_NAMES environment variable will be considered.
    """
    parser = argparse.ArgumentParser(
        description="""Trigger an image update on the argocd repository.

    Only the branch present in the HELM_RELEASE_NAMES environment variable will be considered."""
    )
    parser.add_argument("--version", help="The version to be exported")
    parser.add_argument("--event-type", default="image-update", help="The event name to be triggered")
    parser.add_argument(
        "--repository",
        default="camptocamp/argocd-gs-gmf-apps",
        help="The repository name to be triggered",
    )

    args = parser.parse_args()

    if args.version:
        version = args.version
    else:
        ref = os.environ["GITHUB_REF"].split("/")

        if ref[1] != "heads":
            print("Not a branch")
            sys.exit(0)

        version = "/".join(ref[2:])

        if version not in os.environ.get("HELM_RELEASE_NAMES", "").split(","):
            print("Not a release branch")
            sys.exit(0)

    images_full = []
    with open("ci/config.yaml", encoding="utf-8") as config_file:
        ci_config = yaml.load(config_file, Loader=yaml.SafeLoader)
        for image_config in ci_config.get("publish", {}).get("docker", {}).get("images", []):
            images_full.append(image_config["name"])

    dispatch(args.repository, args.event_type, [f"{image}:{version}" for image in images_full])


def dispatch(repository: str, event_type: str, images_full: List[str]) -> None:
    """
    Trigger an image update on the argocd repository.
    """

    id_ = random.randint(1, 100000)  # nosec
    print(f"Triggering {event_type}:{id_} on {repository} with {','.join(images_full)}")

    response = requests.post(
        f"https://api.github.com/repos/{repository}/dispatches",
        headers={
            "Content-Type": "application/json2",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token "
            + subprocess.run(
                ["gopass", "show", "gs/ci/github/token/gopass"], check=True, stdout=subprocess.PIPE
            )
            .stdout.decode()
            .strip(),
        },
        json={"event_type": event_type, "client_payload": {"name": " ".join(images_full), "id": id_}},
    )
    response.raise_for_status()


if __name__ == "__main__":
    main()
