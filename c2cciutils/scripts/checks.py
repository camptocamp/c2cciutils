#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

import c2cciutils.checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the checks of c2cciutils.")
    parser.add_argument("--fix", action="store_true", help="fix black and isort issues")

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("checks", {})
    error = False
    for key, conf in config.items():
        if conf:
            check = getattr(c2cciutils.checks, key)
            print("::group::Run check {}".format(key))
            if check(conf, full_config, args) is True:  # type: ignore
                error = True
                print("::endgroup::")
                print("With error")
            else:
                print("::endgroup::")
    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
