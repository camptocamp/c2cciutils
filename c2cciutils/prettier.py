# -*- coding: utf-8 -*-

import difflib
import os

import node_vm2
import yaml


class Prettier:
    module: None

    def __enter__(self):
        with open(os.path.join(os.path.dirname(__file__), "prettier.js")) as query_open:
            javascript = query_open.read()

        self.module = node_vm2.NodeVM.code(
            javascript,
            os.path.join(os.path.dirname(__file__), "node_modules"),
            console="inherit",
            require={"external": True},
        )
        return self

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        self.module.__exit__(type, value, traceback)

    def get_info(self, filename):
        return self.module.call_member("getFileInfo", filename)

    def check(self, filename, config):
        try:
            with open(filename) as the_file_to_check:
                data = the_file_to_check.read()
                success = self.module.call_member("check", data, config)
            if not success:
                new_data = self.module.call_member("format", data, config)
                print()
                print(
                    "Wrong file formatting with config:\n{}{}".format(
                        self.dump_yaml(config),
                        "".join(
                            difflib.unified_diff(
                                data.splitlines(True),
                                new_data.splitlines(True),
                                filename,
                                filename + "-formated",
                            )
                        ),
                    )
                )
            return success
        except node_vm2.VMError as exception:
            print(
                "ERROR on check the file '{}' with config:\n{}\n{}".format(
                    filename, self.dump_yaml(config), exception
                )
            )
            return False

    def dump_yaml(self, data, filename="ci/config.yaml"):
        return self.format_str(yaml.dump(data, default_flow_style=False, Dumper=yaml.SafeDumper), filename)

    def format_str(self, data, filename="ci/config.yaml"):
        info = self.get_info(filename)
        if info.get("info", {}).get("ignored", False):
            return data
        if not info.get("info", {}).get("inferredParser"):
            return data
        config = info["config"]
        config["parser"] = info["info"]["inferredParser"]
        try:
            return self.module.call_member("format", data, config)
        except node_vm2.VMError as exception:
            print(exception)
            return data

    def format(self, filename, config):
        try:
            with open(filename) as the_file_to_format:
                new_data = self.module.call_member("format", the_file_to_format.read(), config)
            with open(filename, "w") as the_file_to_format:
                the_file_to_format.write(new_data)
        except node_vm2.VMError as exception:
            print(
                "ERROR on formatted the file '{}' with config:\n{}\n{}".format(
                    filename, self.dump_yaml(config), exception
                )
            )
            return False
        return True


def dump_yaml(data, filename="ci/config.yaml"):
    with Prettier() as prettier:
        return prettier.dump_yaml(data, filename)
