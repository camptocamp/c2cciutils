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
    parser.add_argument("--fix", action="store_true", help="fix black and isort issues")
    parser.add_argument("--stop", action="store_true", help="stop on first error")
    parser.add_argument("--check", help="runs only the specified check")
    parser.add_argument("--branch", help="The branch to check, not defined means autodetect")

    args = parser.parse_args()

    full_config = c2cciutils.get_config(args.branch)
    config = full_config.get("checks", {})
    success = True
    for key, conf in config.items():
        if conf is not False and (args.check is None or args.check == key):
            check = getattr(c2cciutils.checks, key)
            print(f"::group::Run check {key}")
            try:
                if not check({} if conf is True else conf, full_config, args):
                    success = False
                    print("::endgroup::")
                    if args.stop:
                        sys.exit(1)
                    print("With error")
                    if key in ("black", "isort", "prettier", "codespell"):
                        print("Can be fixed with:")
                        print("python3 -m pip install --requirement=ci/requirements.txt")
                        print(f"c2cciutils-checks --fix --check={key}")
                    if key in ("black", "isort", "prettier"):
                        print("See also documentation for IDE: https://github.com/camptocamp/c2cciutils#ide")
                else:
                    print("::endgroup::")
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()
                success = False
                print("::endgroup::")
                if args.stop:
                    sys.exit(1)
                print("With error")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
