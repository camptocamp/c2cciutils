import os
import site
import sys

from setuptools import find_packages, setup

site.ENABLE_USER_SITE = "--user" in sys.argv

VERSION = os.environ.get("version", "1.0")
HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "requirements.txt")) as open_file:
    INSTALL_REQUIRES = open_file.read().splitlines()


def long_description() -> str:
    try:
        with open("README.md") as readme_file:
            return readme_file.read()
    except FileNotFoundError:
        return ""


setup(
    name="c2cciutils",
    version=VERSION,
    description="Common utilities for Camptocamp CI",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="ci",
    author="Camptocamp",
    author_email="info@camptocamp.com",
    url="https://github.com/camptocamp/c2cciutils",
    license="FreeBSD",
    packages=find_packages(exclude=["tests", "docs"]),
    install_requires=INSTALL_REQUIRES,
    entry_points={
        "console_scripts": [
            "c2cciutils = c2cciutils.scripts.main:main",
            "c2cciutils-checks = c2cciutils.scripts.checks:main",
            "c2cciutils-audit = c2cciutils.scripts.audit:main",
            "c2cciutils-publish = c2cciutils.scripts.publish:main",
            "c2cciutils-clean = c2cciutils.scripts.clean:main",
            "c2cciutils-google-calendar = c2cciutils.publish:main_calendar",
        ],
    },
    package_data={"c2cciutils": ["*.graphql"]},
)
