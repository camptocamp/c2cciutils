"""
Run a command in files folder.
"""

import argparse
import os.path
import subprocess
import sys


def main() -> None:
    """
    Run a command in files folder.
    """

    parser = argparse.ArgumentParser(
        description="""Run a command in files folder.

    Example:
    c2cciutils-run-in-dir --pass-filename --cmd cmd arg1 -aarg2 -a-arg -a--arg --files file1 dir/file2

    will be transform in:
    cmd arg1 arg2 -arg --arg  file1
    (cd dir && cmd arg1 arg2 -arg --arg file2
    """
    )
    parser.add_argument("--fail-fast", action="store_true", help="Fail on the first error")
    parser.add_argument("--pass-filename", action="store_true", help="Pass the filename to the command")
    parser.add_argument("--cmd", nargs="+", help="The command")
    parser.add_argument("-a", "--arg", nargs="+", help="The args")
    parser.add_argument("--files", nargs="+", help="The files")
    args = parser.parse_args()

    command = [*args.cmd, *args.arg]
    success = True
    for filename in args.files:
        filename = os.path.join(os.getcwd(), filename)
        proc = subprocess.run(
            [*command, os.path.basename(filename)] if args.pass_filenames else command,
            cwd=os.path.dirname(filename),
        )
        if proc.returncode != 0:
            if args.fail_fast:
                sys.exit(proc.returncode)
            success = False
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
