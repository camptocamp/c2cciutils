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
    for key, check in (
        ("print_versions", c2cciutils.print_versions),
        ("print_config", c2cciutils.checks.print_config),
        ("black_config", c2cciutils.checks.black_config),
        ("editorconfig", c2cciutils.checks.editorconfig),
        ("gitattribute", c2cciutils.checks.gitattribute),
        ("eof", c2cciutils.checks.eof),
        ("workflows", c2cciutils.checks.workflows),
        ("required_workflows", c2cciutils.checks.required_workflows),
        ("versions", c2cciutils.checks.versions),
        ("black", c2cciutils.checks.black),
        ("isort", c2cciutils.checks.isort),
        ("codespell", c2cciutils.checks.codespell),
    ):
        conf = config.get(key, False)
        if conf:
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
