#!/usr/bin/env python3

"""
The pull request checker main function.
"""

import argparse
import json
import os
import sys
import traceback

import requests

import c2cciutils
import c2cciutils.pr_checks


def main() -> None:
    """
    Run the checks.
    """
    parser = argparse.ArgumentParser(description="Run the pull request checks of c2cciutils.")
    parser.add_argument("--stop", action="store_true", help="stop on first error")
    parser.add_argument("--check", help="runs only the specified check")

    args = parser.parse_args()

    github_event = json.loads(os.environ["GITHUB_EVENT"])

    commits_response = requests.get(
        github_event["event"]["pull_request"]["_links"]["commits"]["href"],
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
        headers=c2cciutils.add_authorization_header({}),
    )
    commits_response.raise_for_status()
    commits = commits_response.json()

    full_config = c2cciutils.get_config()
    config = full_config["pr-checks"]

    check_args = {
        "args": args,
        "full_config": full_config,
        "commits": commits,
        "github_event": github_event,
    }

    success = True
    for key, conf in config.items():
        if conf is not False and (args.check is None or args.check == key):
            check = getattr(c2cciutils.pr_checks, key)
            print(f"::group::Run check {key}")
            try:
                if not check(config={} if conf is True else conf, **check_args):
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
