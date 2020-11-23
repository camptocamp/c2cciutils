#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import c2cciutils.checks


def main() -> None:
    full_config = c2cciutils.get_config()
    config = full_config.get("checks", {})
    error = False
    for key, check in (
        ("print_versions", c2cciutils.checks.print_versions),
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
    ):
        conf = config.get(key, False)
        if conf:
            print("::group::Run check {}".format(key))
            if check(conf, full_config) is True:
                error = True
                print("::endgroup::")
                print("With error")
            else:
                print("::endgroup::")
    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
