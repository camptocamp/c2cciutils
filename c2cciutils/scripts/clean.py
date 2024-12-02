#!/usr/bin/env python3

"""The clean main function."""

import argparse
import json
import os
import sys
from typing import cast

import requests
import yaml

import c2cciutils


def clean(image: str, tag: str, token: str) -> None:
    """
    Delete an image from Docker hub.

    Arguments:
        image: The image name that should be deleted (<organization>/<name>)
        tag: The tag that should be deleted
        token: The token used to be authenticated on Docker hub

    """
    print(f"Delete image '{image}:{tag}'.")

    response = requests.head(
        f"https://hub.docker.com/v2/repositories/{image}/tags/{tag}/",
        headers={"Authorization": "JWT " + token},
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    )
    if response.status_code == 404:
        return
    if not response.ok:
        print(f"Error checking image '{image}:{tag}' status.")
        print(response.text)
        sys.exit(1)

    response = requests.delete(
        f"https://hub.docker.com/v2/repositories/{image}/tags/{tag}/",
        headers={"Authorization": "JWT " + token},
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    )
    if not response.ok:
        print("::error::Error on deleting tag: " + tag)
        print(response.text)
        sys.exit(1)


def main() -> None:
    """Run the main function."""
    parser = argparse.ArgumentParser(
        description=(
            "Clean the Docker images on Docker Hub for the branch we delete "
            "(get from the GitHub event information)."
        )
    )
    parser.parse_args()

    username = (
        os.environ["DOCKERHUB_USERNAME"]
        if "DOCKERHUB_USERNAME" in os.environ
        else c2cciutils.gopass("gs/ci/dockerhub/username")
    )
    password = (
        os.environ["DOCKERHUB_PASSWORD"]
        if "DOCKERHUB_PASSWORD" in os.environ
        else c2cciutils.gopass("gs/ci/dockerhub/password")
    )
    token = requests.post(
        "https://hub.docker.com/v2/users/login/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "username": username,
                "password": password,
            }
        ),
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    ).json()["token"]

    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event_file:
        event = json.loads(event_file.read())
        print(yaml.dump(event))
        ref = str(event["number"]) if "pull_request" in event else event["ref"]

    ref = ref.replace("/", "_")

    config = c2cciutils.get_config()

    docker_config = cast(
        c2cciutils.configuration.PublishDockerConfig,
        config.get("publish", {}).get("docker", {}) if config.get("publish", {}).get("docker", False) else {},
    )
    for image in docker_config.get("images", []):
        for tag in image.get("tags", []):
            clean(image["name"], tag.format(version=ref), token)


if __name__ == "__main__":
    main()
