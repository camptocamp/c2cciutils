#!/usr/bin/env python3

"""
The checker main function.
"""

import argparse

import c2cciutils.env


def main() -> None:
    """
    Run the checks.
    """
    parser = argparse.ArgumentParser(description="Print the environment information.")
    parser.parse_args()

    c2cciutils.env.print_environment(c2cciutils.get_config(), "")


if __name__ == "__main__":
    main()
