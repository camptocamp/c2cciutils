#!/usr/bin/env python3


import argparse
import configparser
import json


def main() -> None:
    """Run the command."""
    parser = argparse.ArgumentParser(
        description="""Output packages with versions from Pipfile.lock in Pipfile format (similar to pip freeze).
Useful to pin all the dependency in the Pipfile, on stabilization branch to be able to upgrade one package that have a security issue."""
    )
    parser.add_argument("--packages", action="store_true", help="Output only the packages section")
    parser.add_argument("--dev-packages", action="store_true", help="Output only the dev-packages section")
    parser.add_argument("--pipfile", default="Pipfile", help="The base Pipfile filename")
    args = parser.parse_args()

    packages = {}
    dev_packages = {}

    with open(args.pipfile + ".lock", encoding="utf-8") as pipfilelock_file:
        pipfilelock = json.loads(pipfilelock_file.read())
        for pkg, pkg_config in pipfilelock["default"].items():
            packages[pkg] = pkg_config["version"]
        for pkg, pkg_config in pipfilelock["develop"].items():
            dev_packages[pkg] = pkg_config["version"]

    config = configparser.ConfigParser()
    config.read(args.pipfile)

    if args.packages or not args.packages and not args.dev_packages:
        print("[packages]")
        print("# Lock dependencies")
        for pkg, version in packages.items():
            if pkg not in config["packages"] and f'"{pkg}"' not in config["packages"]:
                quote = '"' if "." in pkg else ""
                print(f'{quote}{pkg}{quote} = "{version}"')

    if args.packages and args.dev_packages or not args.packages and not args.dev_packages:
        print()

    if args.dev_packages or not args.packages and not args.dev_packages:
        print("[dev-packages]")
        print("# Lock dependencies")
        for pkg, version in dev_packages.items():
            if pkg not in config["dev-packages"] and f'"{pkg}"' not in config["dev-packages"]:
                quote = '"' if "." in pkg else ""
                print(f'{quote}{pkg}{quote} = "{version}"')


if __name__ == "__main__":
    main()
