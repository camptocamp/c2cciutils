#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

import c2cciutils.checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the checks of c2cciutils.")
    parser.add_argument("--fix", action="store_true", help="fix black and isort issues")
    parser.add_argument("--stop", action="store_true", help="stop on first error")
    parser.add_argument("--check", help="runs only the specified check")

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("checks", {})
    success = True
    for key, conf in config.items():
        if conf and (args.check is None or args.check == key):
            check = getattr(c2cciutils.checks, key)
            print("::group::Run check {}".format(key))
            if not check(conf, full_config, args):  # type: ignore
                success = False
                print("::endgroup::")
                if args.stop:
                    sys.exit(1)
                print("With error")
            else:
                print("::endgroup::")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
