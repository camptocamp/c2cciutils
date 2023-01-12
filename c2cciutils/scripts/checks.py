#!/usr/bin/env python3

"""
The checker main function.
"""

import argparse
import sys
import traceback

import c2cciutils.checks


def main() -> None:
    """
    Run the checks.
    """
    parser = argparse.ArgumentParser(description="Run the checks of c2cciutils.")
    parser.add_argument("--stop", action="store_true", help="stop on first error")
    parser.add_argument("--check", help="runs only the specified check")
    parser.add_argument("files", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    full_config = c2cciutils.get_config()
    config = full_config.get("checks", {})
    success = True
    for key, conf in config.items():
        if conf is not False and (args.check is None or args.check == key):
            check = getattr(c2cciutils.checks, key)
            print(f"::group::Run check {key}")
            try:
                if not check(
                    {} if conf is True else conf, full_config, args, args.files if args.files else None
                ):
                    success = False
                    print("::endgroup::")
                    if args.stop:
                        sys.exit(1)
                    print("::error::With error")
                else:
                    print("::endgroup::")
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()
                success = False
                print("::endgroup::")
                if args.stop:
                    sys.exit(1)
                print("::error::With error")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
