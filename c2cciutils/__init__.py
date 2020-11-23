# -*- coding: utf-8 -*-

import os.path
import re

import yaml


def apply(config, default_config):
    for key in default_config.keys():
        if key not in config:
            config[key] = default_config[key]
        elif isinstance(default_config[key], dict) and isinstance(config[key], dict):
            apply(config[key], default_config[key])


def get_config():
    config = {}
    if os.path.exists("ci/config.yaml"):
        with open("ci/config.yaml") as open_file:
            config = yaml.load(open_file, yaml.SafeLoader)

    version_branch_re = config.get("version", {}).get("branch_to_version_re", {}).get("from")
    if version_branch_re is not None and config.get("version", {}).get("branch_re") is None:
        config["version"]["branch_re"] = version_branch_re

    editorconfig_properties = {
        "end_of_line": "lf",
        "insert_final_newline": "true",
        "charset": "utf-8",
        "indent_style": "space",
        "trim_trailing_whitespace": "true",
        "max_line_length": "110",
        "quote_type": "single",
    }
    editorconfig_properties_2 = dict(editorconfig_properties)
    editorconfig_properties_4 = dict(editorconfig_properties)
    editorconfig_properties_2["indent_size"] = "2"
    editorconfig_properties_4["indent_size"] = "4"
    editorconfig_properties_mk = dict(editorconfig_properties_4)
    editorconfig_properties_mk["indent_style"] = "tab"
    editorconfig_full_properties = {
        "*.py": editorconfig_properties_4,
        "*.yaml": editorconfig_properties_2,
        "*.json": editorconfig_properties,
        "*.java": editorconfig_properties_4,
        "*.js": editorconfig_properties_2,
        "*.mk": editorconfig_properties_mk,
        "*.MAKEFILE": editorconfig_properties_mk,
    }

    default_config = {
        "version": {
            "branch_re": r"[0-9]+.[0-9]+",
            "tag_re": r"[0-9]+.[0-9]+.[0-9]+",
            "tag_to_version_re": {"from": r"(.*)", "to": r"\1"},
            "branch_to_version_re": {"from": r"(.*)", "to": r"\1"},
            "version_to_branch_re": {"from": r"(.*)", "to": r"\1"},
        },
        "publish": {
            "pypi": ["minor"],
            "docker": {
                "images": {os.environ["GITHUB_REPOSITORY"]: True}
                if "GITHUB_REPOSITORY" in os.environ
                else {},
                "repository": {
                    "github": {"dns": "ghcr.io", "versions": ["major", "minor", "master", "spesific"]},
                    "dockerhub": {"versions": ["major", "minor", "master", "branch", "specific"]},
                },
            },
        },
        "checks": {
            "print_versions": {
                "versions": [
                    {"name": "java", "cmd": ["java", "--version"]},
                    {"name": "python", "cmd": ["python3", "--version"]},
                    {"name": "pip", "cmd": ["python3", "-m", "pip", "--version"]},
                    {"name": "pipenv", "cmd": ["pipenv", "--version"]},
                    {"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]},
                    {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]},
                    {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]},
                ]
            },
            "print_config": True,
            "black_config": {"propertires": {"line-length": 110}},
            "editorconfig": {
                "properties": editorconfig_full_properties,
            },
            "gitattribute": True,
            "eof": True,
            "workflows": {"images_blacklist": ["ubuntu-latest"], "timeout": True},
            "required_workflows": {
                "main.yaml": {"if": "!startsWith(github.event.head_commit.message, '[skip ci] ')"},
                "clean.yaml": {"runs_re": ["c2cciutils-clean$"]},
                "audit.yaml": {"runs_re": ["c2cciutils-audit$"], "strategy-fail-fast": False},
                "backport.yaml": True,
                "codeql.yaml": True,
                "dependabot-auto-merge.yaml": True,
            },
            "versions": {
                "outdated": True,
                "backport_tags": True,
                "rebuild": {
                    "files": [f for f in os.listdir(".github/workflows") if re.match(r"rebuild.*\.yaml", f)]
                },
                "audit": True,
                "branches": True,
            },
            "black": True,
            "isort": True,
        },
        "audit": {"pip": True, "pypenv": {"python_versions": ["3.7.8"]}, "npm": True},
    }
    apply(config, default_config)

    if config["checks"].get("versions", False):
        required_workflows = {
            rebuild: {"noif": True, "runs_re": [r"c2cciutils-publish( .*)?$"], "strategy-fail-fast": False}
            for rebuild in config["checks"]["versions"].get("file", ["rebuild.yaml"])
        }
        apply(config["checks"]["required_workflows"], required_workflows)

    for key, value in config["publish"]["docker"]["images"].items():
        if value is True:
            value = {}
            config["publish"]["docker"]["images"][key] = value
        if isinstance(value, dict):
            apply(
                value,
                {
                    "tags": ["{version}"],
                    "validate_tags": True,
                    "master_as": "latest",
                    "group": "default",
                },
            )

    return config


def convert(value, config):
    if not isinstance(config, dict):
        return value

    convert_from = config.get("from", r"(.*)")
    if convert_from[0] != "^":
        convert_from = "^" + convert_from
    if convert_from[-1] != "$":
        convert_from += "$"

    return re.sub(convert_from, config.get("to", r"\1"), value)
