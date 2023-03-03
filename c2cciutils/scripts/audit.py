#!/usr/bin/env python3

"""
The audit main function.
"""

import argparse
import os
import sys

import c2cciutils.audit


def main() -> None:
    """
    Run the audit.
    """
    parser = argparse.ArgumentParser(description="Run the audit of c2cciutils.")
    parser.add_argument("--branch", help="The branch to audit, not defined means autodetect")
    parser.add_argument("--check", help="Runs only the specified check")
    parser.add_argument("--fix", action="store_true", help="Fix issues")

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    success = True
    for key, conf in config.items():
        if conf is not False and (args.check is None or args.check == key):
            audit = getattr(c2cciutils.audit, key)
            print(f"Run audit {key}")
            success &= audit({} if conf is True else conf, full_config, args)
    if not success and os.environ.get("TEST") != "TRUE":
        sys.exit(1)


if __name__ == "__main__":
    main()
