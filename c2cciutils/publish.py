# -*- coding: utf-8 -*-

import datetime
import glob
import os
import subprocess
import sys


def pip(config, version, version_type):
    """
    Publish to pypi

    version_type: Describe the kind of release we do: custom (used by rebuild), version_tag, version_branch,
                  feature_branch, feature_tag (for pull request)
    config is like:
        packages:
          - path: . # the root foder of the package
    """

    print("::group::Publishing to pypi")
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        env = dict(os.environ)
        env["VERSION"] = version

        for pkg in config.get("packages", []):
            cwd = os.path.abspath(pkg.get("path", "."))
            if version_type == "version_branch":
                subprocess.check_call(
                    [
                        "python3",
                        "./setup.py",
                        "egg_info",
                        "--no-date",
                        "--tag-build=dev" + datetime.datetime.now().strftime("%Y%m%d%H%H%S"),
                        "bdist_wheel",
                    ],
                    cwd=cwd,
                    env=env,
                )
            else:
                subprocess.check_call(
                    ["python3", "./setup.py", "egg_info", "--no-date", "bdist_wheel"], cwd=cwd, env=env
                )
            subprocess.check_call(
                ["twine", "upload", "--verbose", "--disable-progress-bar"] + glob.glob("dist/*.whl"), cwd=cwd
            )
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print("Error: {}".format(exception))
        print("::endgroup::")
        print("With error")
        return False
    return True


def docker(config, name, image_config, tag_src, tag_dst):
    """
    Publish to a docker registry

    config is like:
        server: # The server fqdn

    image_config is like:
        name: # The image name
    """

    print("::group::Publishing {} to {}".format(image_config["name"], name))
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        if "server" in config:
            subprocess.check_call(
                [
                    "docker",
                    "tag",
                    "{}:{}".format(image_config["name"], tag_src),
                    "{}/{}:{}".format(config["server"], image_config["name"], tag_dst),
                ]
            )
            subprocess.check_call(
                [
                    "docker",
                    "push",
                    "{}/{}:{}".format(config["server"], image_config["name"], tag_dst),
                ]
            )
        else:
            if tag_src != tag_dst:
                subprocess.check_call(
                    [
                        "docker",
                        "tag",
                        "{}:{}".format(image_config["name"], tag_src),
                        "{}:{}".format(image_config["name"], tag_dst),
                    ]
                )
            subprocess.check_call(
                [
                    "docker",
                    "push",
                    "{}:{}".format(image_config["name"], tag_dst),
                ]
            )
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print("Error: {}".format(exception))
        print("::endgroup::")
        print("With error")
        return False
    return True
