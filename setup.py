"""
The package setup.
"""

import os
import site
import sys

from setuptools import find_packages, setup

site.ENABLE_USER_SITE = "--user" in sys.argv

VERSION = os.environ.get("VERSION", "1.0")
HERE = os.path.abspath(os.path.dirname(__file__))

with open("requirements.txt", encoding="utf-8") as requirements:
    INSTALL_REQUIRES = [r for r in requirements.read().split("\n") if r]


def long_description() -> str:
    """
    Get the long description from README.md file.
    """
    try:
        with open("README.md", encoding="utf-8") as readme_file:
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
        "Typing :: Typed",
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
            "c2cciutils-k8s-install = c2cciutils.scripts.k8s.install:main",
            "c2cciutils-k8s-db = c2cciutils.scripts.k8s.db:main",
            "c2cciutils-k8s-wait = c2cciutils.scripts.k8s.wait:main",
            "c2cciutils-k8s-logs = c2cciutils.scripts.k8s.logs:main",
        ],
    },
    package_data={
        "c2cciutils": [
            "*.graphql",
            "*.json",
            "*.js",
            "node_modules/*/package.json",
            "node_modules/*/*.js",
            "node_modules/*/src/*.js",
            "node_modules/*/src/*/*.js",
            "node_modules/*/src/*/*/*.js",
            "node_modules/*/lib/*.js",
        ]
    },
)
