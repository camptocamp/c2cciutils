#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import subprocess
import sys
from typing import Dict, Set

import c2cciutils


def match(tpe, base_re):
    """
    Return the match for `GITHUB_REF` basically like: `refs/<tpe>/<base_re>`
    """
    if base_re[0] == "^":
        base_re = base_re[1:]
    if base_re[-1] != "$":
        base_re += "$"
    return re.match("^refs/{}/{}".format(tpe, base_re), os.environ["GITHUB_REF"])


def get_version(config):
    """
    Get the version (tag or branch) from the `GITHUB_REF`
    """
    return c2cciutils.convert("/".join(os.environ["GITHUB_REF"].split("/")[2:]), config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish the project.")
    parser.add_argument("--group", default="default", help="The publishing group")
    parser.add_argument("--version", help="The version to publish to")

    args = parser.parse_args()

    config = c2cciutils.get_config()

    if config.get("publish").get("print_versions"):
        print("::group::Versions")
        c2cciutils.print_versions(config.get("publish").get("print_versions"), config)
        print("::endgroup::")

    type = None
    version: str = ""
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

    if type is not None:
        print("Create release type {}: {}".format(type, version))

    error = False
    pypi_config = config.get("publish", {}).get("pypi", {})
    if type in pypi_config.get("versions", []):
        print("::group::Publishing to pypi")
        sys.stdout.flush()
        sys.stderr.flush()

        try:
            env = dict(os.environ)
            env["VERSION"] = version

            for pkg in pypi_config.get("packages", []):
                cwd = os.path.abspath(pkg.get("path", "."))
                if "major":
                    subprocess.check_call(["bump", "minor"], cwd=cwd)
                    subprocess.check_call(["git", "add", "setup.py"], cwd=cwd)

                if type == "master":
                    subprocess.check_call(
                        [
                            "python3",
                            "./setup.py",
                            "egg_info",
                            "--tag-date",
                            "--tag-build",
                            "dev",
                            "bdist_wheel",
                        ],
                        cwd=cwd,
                        env=env,
                    )
                else:
                    subprocess.check_call(
                        ["python3", "./setup.py", "egg_info", "--no-date", "bdist_wheel"], cwd=cwd, env=env
                    )
                subprocess.check_call(["twine", "upload", "/*.whl"], cwd=cwd)
            if type == "major":
                subprocess.call(["git", "commit", "--message=[skip ci] Bump Version"])
                subprocess.check_call(["git", "push"])
            print("::endgroup::")
        except subprocess.CalledProcessError as exception:
            print("Error: {}".format(exception))
            print("::endgroup::")
            print("With error")
            error = True

    docker_config = config.get("publish", {}).get("docker", {})
    available_images: Dict[str, Set[str]] = {}
    for image in (
        subprocess.check_output(["docker", "images", "--format={{.Repository}}:{{.Tag}}"])
        .decode()
        .strip()
        .split("\n")
    ):
        img, tag = image.split(":")
        available_images.setdefault(img, set()).add(tag)

    for image_conf in docker_config.get("images", []):
        if image_conf.get("group") == args.group:
            ref = (
                image_conf["master_as"]
                if type == "master" and image_conf.get("master_as", False)
                else version
            )
            if image_conf.get("validate_tags", False):
                expected_tags = {t.format(version="latest") for t in image_conf.get("tags", [])}
                if available_images.get(image_conf["name"], set()) != expected_tags:
                    print(
                        "ERROR: For the image '{}', the tags marked for publishing [{}] doesn't corresponds "
                        "with the available tags [{}]".format(
                            image_conf["name"],
                            ", ".join(expected_tags),
                            ", ".join(available_images.get(image_conf["name"], [])),
                        )
                    )
                    error = True

            for tag_config in image_conf.get("tags", []):
                sub_tags = []
                if isinstance(tag_config, dict):
                    from_re = re.compile(tag_config["from"])
                    for candidate_tag in available_images.get(image_conf["name"], set()):
                        if from_re.match(candidate_tag):
                            sub_tags.append(
                                (
                                    candidate_tag,
                                    c2cciutils.convert(candidate_tag, tag_config).format(version=ref),
                                )
                            )
                else:
                    sub_tags.append((tag_config.format(version="latest"), tag_config.format(version=ref)))
                for tag_src, tag_dst in sub_tags:
                    for name, conf in docker_config.get("repository", {}).items():
                        if type in conf.get("versions", []):
                            print("::group::Publishing {} to {}".format(image_conf["name"], name))
                            sys.stdout.flush()
                            sys.stderr.flush()

                            try:

                                if "dns" in conf:
                                    subprocess.check_call(
                                        [
                                            "docker",
                                            "tag",
                                            "{}:{}".format(image_conf["name"], tag_src),
                                            "{}/{}:{}".format(conf["dns"], image_conf["name"], tag_dst),
                                        ]
                                    )
                                    subprocess.check_call(
                                        [
                                            "docker",
                                            "push",
                                            "{}/{}:{}".format(conf["dns"], image_conf["name"], tag_dst),
                                        ]
                                    )
                                else:
                                    if ref != "latest":
                                        subprocess.check_call(
                                            [
                                                "docker",
                                                "tag",
                                                "{}:{}".format(image_conf["name"], tag_src),
                                                "{}:{}".format(image_conf["name"], tag_dst),
                                            ]
                                        )
                                    subprocess.check_call(
                                        [
                                            "docker",
                                            "push",
                                            "{}:{}".format(image_conf["name"], tag_dst),
                                        ]
                                    )
                                print("::endgroup::")
                            except subprocess.CalledProcessError as exception:
                                print("Error: {}".format(exception))
                                print("::endgroup::")
                                print("With error")
                                error = True

    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
