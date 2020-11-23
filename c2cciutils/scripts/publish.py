#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import subprocess
import sys

import c2cciutils


def match(tpe, base_re):
    if base_re[0] == "^":
        base_re = base_re[1:]
    if base_re[-1] != "$":
        base_re += "$"
    return re.match("^refs/{}/{}".format(tpe, base_re), os.environ["GITHUB_REF"])


def get_version(config):
    return c2cciutils.convert("/".join(os.environ["GITHUB_REF"].split("/")[2:]), config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish the project.")
    parser.add_argument("--group", default="default", help="The publishing group")
    parser.add_argument("--version", help="The version to publish to")

    args = parser.parse_args()

    config = c2cciutils.get_config()
    type = None
    version = None
    ref = os.environ["GITHUB_REF"]

    if args.version is not None:
        type = "specific"
        version = args.version
    elif os.environ["GITHUB_REF"] == "refs/heads/master":
        type = "master"
        version = "master"
    elif match("tags", config["version"]["tag_re"]):
        type = "minor"
        version = get_version(config["version"].get("tag_to_version_re"))
    elif match("heads", config["version"]["branch_re"]):
        type = "major"
        version = get_version(config["version"].get("branch_to_version_re"))
    elif os.environ["GITHUB_REF"].startswith("refs/heads/"):
        type = "branch"
        version = "_".join(os.environ["GITHUB_REF"].split("/")[2:])
    elif os.environ["GITHUB_REF"].startswith("refs/tags/"):
        type = "tag"
        version = "_".join(os.environ["GITHUB_REF"].split("/")[2:])

    if type is not None and version is not None:
        print("Create release {}: {}".format(type, version))

    if type in config.get("publish", {}).get("pypi", []):
        pass
        # TODO pypi

    docker_config = config.get("publish", {}).get("docker", {})
    for image, image_conf in docker_config.get("images").items():
        if image_conf.get("group") == args.group:
            ref = (
                image_conf["master_as"]
                if type == "master" and image_conf.get("master_as", False)
                else version
            )

            for tag in image_conf.get("tags", []):
                if image_conf.get("validate_tags", False):
                    # TODO validate the tags
                    pass
                for name, conf in docker_config.get("repository", {}).items():
                    if type in conf.get("versions", []):
                        print("Publishing {} to {}".format(image, name))
                        sys.stdout.flush()
                        sys.stderr.flush()

                        if "dns" in conf:
                            subprocess.check_call(
                                [
                                    "docker",
                                    "tag",
                                    "{}:{}".format(image, tag.format(version="latest")),
                                    "{}/{}:{}".format(conf["dns"], image, tag.format(version=ref)),
                                ]
                            )
                            subprocess.check_call(
                                [
                                    "docker",
                                    "push",
                                    "{}/{}:{}".format(conf["dns"], image, tag.format(version=ref)),
                                ]
                            )
                        else:
                            if ref != "latest":
                                subprocess.check_call(
                                    [
                                        "docker",
                                        "tag",
                                        "{}:{}".format(image, tag.format(version="latest")),
                                        "{}:{}".format(image, tag.format(version=ref)),
                                    ]
                                )
                            subprocess.check_call(
                                [
                                    "docker",
                                    "push",
                                    "{}:{}".format(image, tag.format(version=ref)),
                                ]
                            )


if __name__ == "__main__":
    main()
