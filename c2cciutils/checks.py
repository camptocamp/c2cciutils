"""
The checking functions.
"""

import glob
from argparse import Namespace
from typing import List

import yaml

import c2cciutils
import c2cciutils.configuration


def workflows(
    config: None,
    full_config: c2cciutils.configuration.Configuration,
    args: Namespace,
    files: List[str],
) -> bool:
    """
    Check each workflow have a timeout and/or do not use blacklisted images.

    Arguments:
        config: The check section config
        full_config: All the CI config
        args: The parsed command arguments
        files: The files to check
    """
    del config, full_config, args

    success = True
    if files is None:
        files = glob.glob(".github/workflows/*.yaml")
        files += glob.glob(".github/workflows/*.yml")
    for filename in files:
        with open(filename, encoding="utf-8") as open_file:
            workflow = yaml.load(open_file, Loader=yaml.SafeLoader)

        for name, job in workflow.get("jobs").items():
            if job.get("timeout-minutes") is None:
                c2cciutils.error(
                    "workflows",
                    f"The workflow '{filename}', job '{name}' has no timeout",
                    filename,
                )
                success = False

    return success
