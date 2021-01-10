#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys

import c2cciutils.publish
from c2cciutils.publish import GoogleCalendar


def match(tpe, base_re):
    """
    Return the match for `GITHUB_REF` basically like: `refs/<tpe>/<base_re>`
    """
    if base_re[0] == "^":
        base_re = base_re[1:]
    if base_re[-1] != "$":
        base_re += "$"
    return re.match("^refs/{}/{}".format(tpe, base_re), os.environ["GITHUB_REF"])


def to_version(full_config, value, kind):
    """
    Compute publish version from branch name or tag
    """
    item_re = c2cciutils.compile_re(full_config["version"].get(kind + "_to_version_re", []))
    value_match = c2cciutils.match(value, item_re)
    if value_match[0] is not None:
        return c2cciutils.get_value(*value_match)
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish the project.")
    parser.add_argument("--group", default="default", help="The publishing group")
    parser.add_argument("--version", help="The version to publish to")
    parser.add_argument("--branch", help="The branch from which to compute the version")
    parser.add_argument("--tag", help="The tag from which to compute the version")
    parser.add_argument("--dry-run", action="store_true", help="Don't do the publish")
    parser.add_argument(
        "--type",
        help="The type of version, if no argument provided autodeterminated, can be: "
        "rebuild (in case of rebuild), version_tag, version_branch, feature_branch, feature_tag "
        "(for pull request)",
    )
    args = parser.parse_args()

    config = c2cciutils.get_config()

    if config.get("publish").get("print_versions"):
        print("::group::Versions")
        c2cciutils.print_versions(config.get("publish", {}).get("print_versions", {}))
        print("::endgroup::")

    # Describe the kind of release we do: rebuild (specified with --type), version_tag, version_branch,
    # feature_branch, feature_tag (for pull request)
    version_type = None
    version: str = ""
    ref = os.environ["GITHUB_REF"]

    if len([e for e in [args.version, args.branch, args.tag] if e is not None]) > 1:
        print("ERROR: you specified more than one of the arguments --version, --branch or --tag")
        sys.exit(1)

    tag_match = c2cciutils.match(
        ref,
        c2cciutils.compile_re(config["version"].get("tag_to_version_re", []), "refs/tags/"),
    )
    branch_match = c2cciutils.match(
        ref,
        c2cciutils.compile_re(config["version"].get("branch_to_version_re", []), "refs/heads/"),
    )
    if args.type is not None:
        version_type = args.type
    if args.version is not None:
        version = args.version
    elif args.branch is not None:
        version = to_version(config, args.branch, "branch")
    elif args.tag is not None:
        version = to_version(config, args.tag, "tag")
    elif tag_match[0] is not None:
        if version_type is None:
            version_type = "version_tag"
        else:
            print("WARNING: you specified the argument --type but not one of --version, --branch or --tag")
        version = c2cciutils.get_value(*tag_match)
    elif branch_match[0] is not None:
        if version_type is None:
            version_type = "version_branch"
        else:
            print("WARNING: you specified the argument --type but not one of --version, --branch or --tag")
        version = c2cciutils.get_value(*branch_match)
    elif ref.startswith("refs/heads/"):
        if version_type is None:
            version_type = "feature_branch"
        else:
            print("WARNING: you specified the argument --type but not one of --version, --branch or --tag")
        # By the way we replace '/' by '_' because it isn't supported by Docker
        version = "_".join(ref.split("/")[2:])
    elif ref.startswith("refs/tags/"):
        if version_type is None:
            version_type = "feature_tag"
        else:
            print("WARNING: you specified the argument --type but not one of --version, --branch or --tag")
        # By the way we replace '/' by '_' because it isn't supported by Docker
        version = "_".join(ref.split("/")[2:])

    if version_type is None:
        print("ERROR: you specified one of the arguments --version, --branch or --tag but not the --type")
        sys.exit(1)

    if version_type is not None:
        print("Create release type {}: {}".format(version_type, version))

    success = True
    pypi_config = config.get("publish", {}).get("pypi", {})
    for package in pypi_config["packages"]:
        if package.get("group") == args.group:
            publish = version_type in pypi_config.get("versions", [])
            if args.dry_run:

                print(
                    "{} '{}' to pypi, skipping (dry run)".format(
                        "Publishing" if publish else "Checking", package.get("path")
                    )
                )
            else:
                success &= c2cciutils.publish.pip(package, version, version_type, publish)

    docker_config = config.get("publish", {}).get("docker", {})

    google_calendar = None
    for image_conf in docker_config.get("images", []):
        if image_conf.get("group", "") == args.group:
            for tag_config in image_conf.get("tags", []):
                tag_src = tag_config.format(version="latest")
                tag_dst = tag_config.format(version=version)
                for name, conf in docker_config.get("repository", {}).items():
                    if version_type in conf.get("versions", []):
                        if args.dry_run:
                            print(
                                "Publishing {}:{} to {}, skipping (dry run)".format(
                                    image_conf["name"], tag_dst, name
                                )
                            )
                        else:
                            success &= c2cciutils.publish.docker(conf, name, image_conf, tag_src, tag_dst)
                if version_type in config.get("publish", {}).get("google_calendar", {}).get("on", []):
                    if not google_calendar:
                        google_calendar = GoogleCalendar()
                    summary = "{}:{}".format(image_conf["name"], tag_dst)
                    description = "Published on: {}\nFor version type: {}".format(
                        ", ".join(docker_config["repository"].keys()), version_type
                    )
                    google_calendar.create_event(summary, description)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
