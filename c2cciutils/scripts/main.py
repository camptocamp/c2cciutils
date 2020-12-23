#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

import pkg_resources
import yaml

import c2cciutils


def main() -> None:
    parser = argparse.ArgumentParser(description="Some utils of c2cciutils.")
    parser.add_argument("--get-config", action="store_true", help="display the current config")
    parser.add_argument("--version", action="store_true", help="display the current version")

    args = parser.parse_args()

    if args.get_config:
        print(yaml.dump(c2cciutils.get_config(), default_flow_style=False, Dumper=yaml.SafeDumper))

    if args.version:
        for pkg in ("c2cciutils", "black", "isort"):
            try:
                print("{} {}".format(pkg, pkg_resources.get_distribution(pkg).version))
            except pkg_resources.DistributionNotFound:
                print("{} missing".format(pkg))


if __name__ == "__main__":
    main()
