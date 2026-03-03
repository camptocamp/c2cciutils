#!/usr/bin/env python3

"""
The main function of some utilities.
"""

import argparse
from importlib.metadata import version

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
        print(f"c2cciutils {version('c2cciutils')}")


if __name__ == "__main__":
    main()
