#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys

import c2cciutils.audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the audit of c2cciutils.")
    parser.add_argument("--branch", required=True, help="The audited branch")

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    success = True
    for key, conf in config.items():
        if conf:
            audit = getattr(c2cciutils.audit, key)
            print("Run audit {}".format(key))
            success &= audit(conf, full_config, args)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
