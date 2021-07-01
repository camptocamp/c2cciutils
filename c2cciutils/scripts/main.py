#!/usr/bin/env python3

"""
The main function of some utilities.
"""

import argparse

import pkg_resources
import yaml

import c2cciutils


def main() -> None:
    """
    Run the utilities.
    """
    parser = argparse.ArgumentParser(description="Some utils of c2cciutils.")
    parser.add_argument("--get-config", action="store_true", help="display the current config")
    parser.add_argument("--version", action="store_true", help="display the current version")
    parser.add_argument("--ls-files-mime", help="List all the files with the specified mime type")

    args = parser.parse_args()

    if args.get_config:
        print(yaml.dump(c2cciutils.get_config(), default_flow_style=False, Dumper=yaml.SafeDumper))

    if args.version:
        for pkg in ("c2cciutils", "black", "isort"):
            try:
                print(f"{pkg} {pkg_resources.get_distribution(pkg).version}")
            except pkg_resources.DistributionNotFound:
                print(f"{pkg} missing")

    if args.ls_files_mime:
        for file_name in c2cciutils.get_git_files_mime(args.ls_files_mime):
            print(file_name)


if __name__ == "__main__":
    main()
