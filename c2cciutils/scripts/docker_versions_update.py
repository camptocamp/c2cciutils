import argparse
import re
import subprocess  # nosec
import tempfile

import ruamel.yaml

import c2cciutils


def main() -> None:
    """Update the version of packages in the file ci/dpkg-versions.yaml."""

    argparser = argparse.ArgumentParser(
        description="Update the version of packages in the file ci/dpkg-versions.yaml."
    )
    argparser.add_argument("--branch", help="The branch to audit, not defined means autodetect")
    args = argparser.parse_args()

    cache: dict[str, dict[str, str]] = {}
    yaml = ruamel.yaml.YAML()  # default_flow_style=False)
    with open("ci/dpkg-versions.yaml", encoding="utf-8") as versions_file:
        versions_config = yaml.load(versions_file)
        for versions in versions_config.values():
            for package_full in versions.keys():
                dist, package = package_full.split("/")
                if dist not in cache:
                    correspondence = {
                        "ubuntu_22_04": ("ubuntu", "22.04", "jammy"),
                        "debian_11": ("debian", "11", "bullseye"),
                        "debian_12": ("debian", "12", "bookworm"),
                    }
                    if dist in correspondence:
                        images, tag, dist_name = correspondence[dist]
                        subprocess.run(
                            ["docker", "rm", "--force", "apt"], stderr=subprocess.DEVNULL, check=False
                        )
                        subprocess.run(
                            [
                                "docker",
                                "run",
                                "--tty",
                                "--interactive",
                                "--detach",
                                "--name=apt",
                                "--entrypoint=",
                                f"{images}:{tag}",
                                "tail",
                                "--follow",
                                "/dev/null",
                            ],
                            check=True,
                        )
                        if images == "ubuntu":
                            with tempfile.NamedTemporaryFile(mode="w", encoding=("utf-8")) as sources_list:
                                sources_list.write(
                                    "\n".join(
                                        [
                                            f"deb http://archive.ubuntu.com/ubuntu/ {dist_name}-security main restricted",
                                            f"deb http://archive.ubuntu.com/ubuntu/ {dist_name}-security universe",
                                            f"deb http://archive.ubuntu.com/ubuntu/ {dist_name}-security multiverse",
                                            "",
                                        ]
                                    )
                                )
                                sources_list.flush()
                                subprocess.run(
                                    ["docker", "cp", sources_list.name, "apt:/etc/apt/sources.list"],
                                    check=True,
                                )

                        subprocess.run(["docker", "exec", "apt", "apt-get", "update"], check=True)

                        package_re = re.compile(r"^([^ /]+)/[a-z-,]+ ([^ ]+) (all|amd64)( .*)?$")
                        proc = subprocess.run(
                            ["docker", "exec", "apt", "apt", "list"], check=True, stdout=subprocess.PIPE
                        )
                        for proc_line in proc.stdout.decode("utf-8").split("\n"):
                            package_match = package_re.match(proc_line)
                            if package_match is None:
                                print(f"not matching: {proc_line}")
                                continue
                            cache.setdefault(dist, {})[package_match.group(1)] = package_match.group(2)

                        subprocess.run(["docker", "rm", "--force", "apt"], check=True)

                if package in cache[dist]:
                    versions[package_full] = cache[dist][package]

    with open("ci/dpkg-versions.yaml", "w", encoding="utf-8") as versions_file:
        yaml.dump(versions_config, versions_file)

    current_branch = c2cciutils.get_branch(args.branch)
    c2cciutils.create_pull_request_if_needed(
        current_branch, f"dpkg-update/{current_branch}", "Update dpkg package versions"
    )


if __name__ == "__main__":
    main()
