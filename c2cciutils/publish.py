# -*- coding: utf-8 -*-

import datetime
import glob
import os
import subprocess
import sys


def pip(package, version, version_type, publish):
    """
    Publish to pypi

    version_type: Describe the kind of release we do: rebuild (specified using --type), version_tag,
                  version_branch, feature_branch, feature_tag (for pull request)
    publish: If False only check the package
    package is like:
        path: . # the root folder of the package
    """

    print("::group::{} '{}' to pypi".format("Publishing" if publish else "Checking", package.get("path")))
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        env = dict(os.environ)
        env["VERSION"] = version

        cwd = os.path.abspath(package.get("path", "."))
        cmd = ["python3", "./setup.py", "egg_info", "--no-date"]
        cmd += (
            ["--tag-build=dev" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")]
            if version_type == "version_branch"
            else []
        )
        cmd.append("bdist_wheel")
        subprocess.check_call(cmd, cwd=cwd, env=env)
        cmd = ["twine"]
        cmd += ["upload", "--verbose", "--disable-progress-bar"] if publish else ["check"]
        cmd += glob.glob(os.path.join(cwd, "dist/*.whl"))
        subprocess.check_call(cmd)
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
