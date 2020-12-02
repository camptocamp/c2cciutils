#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys

import c2cciutils.publish


def match(tpe, base_re):
    """
    Return the match for `GITHUB_REF` basically like: `refs/<tpe>/<base_re>`
    """
    if base_re[0] == "^":
        base_re = base_re[1:]
    if base_re[-1] != "$":
        base_re += "$"
    return re.match("^refs/{}/{}".format(tpe, base_re), os.environ["GITHUB_REF"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish the project.")
    parser.add_argument("--group", default="default", help="The publishing group")
    parser.add_argument("--version", help="The version to publish to")

    args = parser.parse_args()

    config = c2cciutils.get_config()

    if config.get("publish").get("print_versions"):
        print("::group::Versions")
        c2cciutils.print_versions(config.get("publish", {}).get("print_versions", {}))
        print("::endgroup::")

    # Describe the kind of release we do: custom (used by rebuild), version_tag, version_branch,
    # feature_branch, feature_tag (for pull request)
    version_type = None
    version: str = ""
    ref = os.environ["GITHUB_REF"]

    tag_match = c2cciutils.match(
        os.environ["GITHUB_REF"],
        c2cciutils.compile_re(config["version"].get("tag_to_version_re", []), "refs/tags/"),
    )
    branch_match = c2cciutils.match(
        os.environ["GITHUB_REF"],
        c2cciutils.compile_re(config["version"].get("branch_to_version_re", []), "refs/heads/"),
    )
    if args.version is not None:
        version_type = "custom"
        version = args.version
    elif tag_match[0] is not None:
        version_type = "version_tag"
        version = c2cciutils.get_value(*tag_match)
    elif branch_match[0] is not None:
        version_type = "version_branch"
        version = c2cciutils.get_value(*branch_match)
    elif ref.startswith("refs/heads/"):
        version_type = "feature_branch"
        # By the way we replace '/' by '_' because it isn't supported by Docker
        version = "_".join(ref.split("/")[2:])
    elif ref.startswith("refs/tags/"):
        version_type = "feature_tag"
        # By the way we replace '/' by '_' because it isn't supported by Docker
        version = "_".join(ref.split("/")[2:])

    if version_type is not None:
        print("Create release type {}: {}".format(version_type, version))

    success = True
    pypi_config = config.get("publish", {}).get("pypi", {})
    if version_type in pypi_config.get("versions", []):
        success &= c2cciutils.publish.pip(pypi_config, version, version_type)

    docker_config = config.get("publish", {}).get("docker", {})

    for image_conf in docker_config.get("images", []):
        if image_conf.get("group") == args.group:
            for tag_config in image_conf.get("tags", []):
                tag_src = tag_config.format(version="latest")
                tag_dst = tag_config.format(version=version)
                for name, conf in docker_config.get("repository", {}).items():
                    if version_type in conf.get("versions", []):
                        success &= c2cciutils.publish.docker(conf, name, image_conf, tag_src, tag_dst)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
