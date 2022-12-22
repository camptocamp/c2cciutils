#!/usr/bin/env python3

import argparse
import os
import subprocess  # nosec
import sys
from typing import Dict, cast

import yaml

import c2cciutils
import c2cciutils.configuration


def _print(message: str) -> None:
    print(message)
    sys.stdout.flush()


def main() -> None:
    """Create and cleanup a test database."""
    parser = argparse.ArgumentParser(
        description="Create and cleanup a test database.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Database credentials:
    host: test-pg-postgresql
    port: 5432
    user: postgres
    password: mySuperTestingPassword
    database name: postgres""",
    )
    parser.add_argument("--script", help="The script used to initialize the database")
    parser.add_argument("--cleanup", action="store_true", help="Drop the database")

    config = c2cciutils.get_config()
    with open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "applications-versions.yaml"
        ),
        "r",
        encoding="utf-8",
    ) as config_file:
        versions = cast(Dict[str, str], yaml.load(config_file, Loader=yaml.SafeLoader))

    args = parser.parse_args()

    if args.cleanup:
        _print("::group::Cleanup the database")
        subprocess.run([os.environ.get("HELM", "helm"), "uninstall", "test-pg"], check=False)
        _print("::endgroup::")
        sys.exit(0)

    _print("::group::Add repo")
    subprocess.run(
        [os.environ.get("HELM", "helm"), "repo", "add", "bitnami", "https://charts.bitnami.com/bitnami"],
        check=True,
    )
    _print("::endgroup::")

    _print("::group::Install chart")
    subprocess.run(
        [
            os.environ.get("HELM", "helm"),
            "install",
            "test-pg",
            f"--version={versions['postgresql']}",
        ]
        + [
            f"--set={k}={v}"
            for k, v in config.get("k8s", {})
            .get("db", {})
            .get("chart-options", c2cciutils.configuration.K8S_DB_CHART_OPTIONS_DEFAULT)
            .items()
        ]
        + ["bitnami/postgresql"],
        check=True,
    )
    _print("::endgroup::")

    _print("::group::Wait ready")
    subprocess.run(["c2cciutils-k8s-wait", "--selector=app.kubernetes.io/name=postgresql"], check=True)
    _print("::endgroup::")

    if args.script:
        _print("::group::Add data")
        with open(args.script, encoding="utf-8") as script:
            subprocess.run(
                [
                    "kubectl",
                    "run",
                    "test-pg-postgresql-client",
                    "--rm",
                    "--restart=Never",
                    "--namespace=default",
                    "--image=docker.io/bitnami/postgresql",
                    "--env=PGPASSWORD=mySuperTestingPassword",
                    "--stdin=true",
                    "--command",
                    "--",
                    "psql",
                    "--host=test-pg-postgresql",
                    "--username=postgres",
                    "--dbname=postgres",
                    "--port=5432",
                ],
                check=True,
                stdin=script,
            )
        _print("::endgroup::")


if __name__ == "__main__":
    main()
