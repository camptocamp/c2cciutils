import argparse

import yaml

import c2cciutils.lib.docker


def main() -> None:
    """Dump the actual versions of packages in image to file ci/dpkg-versions.yaml."""

    argparser = argparse.ArgumentParser(
        description="Dump the actual versions of packages in image to file ci/dpkg-versions.yaml."
    )
    argparser.add_argument("--distribution", help="The default distribution code to be used")
    argparser.add_argument("--release", help="The default release version to be used")
    argparser.add_argument("images", help="The image to check", nargs="+")
    args = argparser.parse_args()

    versions_config, _ = c2cciutils.lib.docker.get_versions_config()
    for image in args.images:

        _, versions_image = c2cciutils.lib.docker.get_dpkg_packages_versions(
            image,
            default_distribution=args.distribution,
            default_release=args.release,
        )
        versions_config[image] = {k: str(v) for k, v in versions_image.items()}

    with open("ci/dpkg-versions.yaml", "w", encoding="utf-8") as versions_file:
        versions_file.write("# See repository list: https://repology.org/repositories/statistics\n\n")
        versions_file.write(yaml.dump(versions_config, Dumper=yaml.SafeDumper, default_flow_style=False))


if __name__ == "__main__":
    main()
