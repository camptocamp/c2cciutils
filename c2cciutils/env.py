import json
import os
import subprocess  # nosec
import sys

import ruamel.yaml
import yaml

import c2cciutils.configuration


class PrintVersions:
    """
    Print some tools versions.
    """

    def __init__(self, config: c2cciutils.configuration.PrintVersions) -> None:
        """Construct."""
        self.config = config

    def __call__(self) -> None:
        """Run."""
        c2cciutils.print_versions(self.config)


class PrintConfig:
    """
    Print the configuration.
    """

    def __init__(self, config: c2cciutils.configuration.Configuration) -> None:
        """Construct."""
        self.config = config

    def __call__(self) -> None:
        """Run."""
        yaml_ = ruamel.yaml.YAML()
        yaml_.default_flow_style = False
        yaml_.dump(self.config, sys.stdout)


def print_environment_variables() -> None:
    """
    Print the environment variables.
    """
    for name, value in sorted(os.environ.items()):
        if name != "GITHUB_EVENT":
            print(f"{name}: {value}")


def print_github_event_file() -> None:
    """
    Print the GitHub event file.
    """
    if "GITHUB_EVENT_PATH" in os.environ:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as event:
            print(event.read())


def print_github_event_object() -> None:
    """
    Print the GitHub event object.
    """
    github_event = json.loads(os.environ["GITHUB_EVENT"])
    print(yaml.dump(github_event, indent=2))


def print_python_package_version() -> None:
    """
    Print the version of the Python packages.
    """
    subprocess.run(["python3", "-m", "pip", "freeze", "--all"])  # pylint: disable=subprocess-run-check


def print_node_package_version() -> None:
    """
    Print the version of the Python packages.
    """
    subprocess.run(["npm", "list", "--global"])  # pylint: disable=subprocess-run-check


def print_debian_package_version() -> None:
    """
    Print the version of the Python packages.
    """
    subprocess.run(["dpkg", "--list"])  # pylint: disable=subprocess-run-check


def print_environment(config: c2cciutils.configuration.Configuration, prefix: str = "Print ") -> None:
    """Print the GitHub environment information."""
    functions = [
        (
            "version",
            PrintVersions(config.get("print_versions", {})),
        ),
        ("configuration", PrintConfig(config)),
        ("environment variables", print_environment_variables),
    ]
    if "GITHUB_EVENT_PATH" in os.environ:
        functions.append(("GitHub event file", print_github_event_file))
    if "GITHUB_EVENT" in os.environ:
        functions.append(("GitHub event object", print_github_event_object))

    functions.extend(
        [
            ("Python package versions", print_python_package_version),
            ("Node package versions", print_node_package_version),
            ("Debian package versions", print_debian_package_version),
        ]
    )

    for name, function in functions:
        if prefix:
            print(f"::group::{prefix}{name}")
        else:
            print(f"::group::{name[0].upper()}{name[1:]}")
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            function()  # type: ignore
        except subprocess.CalledProcessError as error:
            print(f"::error::Error: {error}")
            print("::endgroup::")
        finally:
            print("::endgroup::")
