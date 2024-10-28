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

    args = parser.parse_args()

    if args.get_config:
        print(yaml.dump(c2cciutils.get_config(), default_flow_style=False, Dumper=yaml.SafeDumper))

    if args.version:
        version = pkg_resources.get_distribution("c2cciutils").version
        print(f"c2cciutils {version}")


if __name__ == "__main__":
    main()
