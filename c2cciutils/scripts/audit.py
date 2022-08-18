#!/usr/bin/env python3

"""
The audit main function.
"""

import argparse
import sys

import c2cciutils.audit


def main() -> None:
    """
    Run the audit.
    """
    parser = argparse.ArgumentParser(description="Run the audit of c2cciutils.")
    parser.add_argument("--branch", help="The branch to audit, not defined means autodetect")

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    success = True
    for key, conf in config.items():
        if conf is not False:
            audit = getattr(c2cciutils.audit, key)
            print(f"Run audit {key}")
            success &= audit({} if conf is True else conf, full_config, args)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
