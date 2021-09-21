# -*- coding: utf-8 -*-

"""
Load prettier.js and improve the API.
"""

import difflib
import os
from types import TracebackType
from typing import Any, Dict, Optional, Type, cast

import node_vm2
import yaml


class PrettierModule:
    """
    Expose and improve the prettier.js API.
    """

    def __init__(self, module: node_vm2.NodeVMModule) -> None:
        """
        Initialize.
        """
        self.module = module

    def get_info(self, filename: str) -> Dict[str, Any]:
        """
        Get the Prettier information related to a file.

        Arguments:
            filename: The file name to consider
        """
        return cast(Dict[str, Any], self.module.call_member("getFileInfo", filename))

    def check(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        Check a file.

        Arguments:
            filename: The file name to check
            config: The Prettier config related to the file
        """
        try:
            with open(filename, encoding="utf-8") as the_file_to_check:
                data = the_file_to_check.read()
                success = cast(bool, self.module.call_member("check", data, config))
            if not success:
                new_data = self.module.call_member("format", data, config)
                print()
                printable_diff = "".join(
                    difflib.unified_diff(
                        data.splitlines(True),
                        new_data.splitlines(True),
                        filename,
                        filename + "-formated",
                    )
                )
                print(f"Wrong file formatting with config:\n{self.dump_yaml(config)}{printable_diff}")
            return success
        except node_vm2.VMError as exception:
            print(
                f"ERROR on check the file '{filename}' with config:\n"
                f"{self.dump_yaml(config)}\n{exception}"
            )
            return False

    def dump_yaml(self, data: Dict[str, Any], filename: str = "ci/config.yaml") -> str:
        """
        Format some YAML.

        Arguments:
            data: The YAML to be dump and format
            filename: The file name used to get the Prettier config
        """
        return self.format_str(yaml.dump(data, default_flow_style=False, Dumper=yaml.SafeDumper), filename)

    def format_str(self, data: str, filename: str = "ci/config.yaml") -> str:
        """
        Format some data.

        Arguments:
            data: The data to be formatted
            filename: The file name used to get the Prettier config
        """
        info = self.get_info(filename)
        if info.get("info", {}).get("ignored", False):
            return data
        if not info.get("info", {}).get("inferredParser"):
            return data
        config = info["config"]
        config["parser"] = info["info"]["inferredParser"]
        try:
            return cast(str, self.module.call_member("format", data, config))
        except node_vm2.VMError as exception:
            print(exception)
            return data

    def format(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        Format a file.

        Arguments:
            filename: The file name to format
            config: The Prettier config related to the file
        """
        try:
            with open(filename, encoding="utf-8") as the_file_to_format:
                new_data = self.module.call_member("format", the_file_to_format.read(), config)
            with open(filename, "w", encoding="utf-8") as the_file_to_format:
                the_file_to_format.write(new_data)
        except node_vm2.VMError as exception:
            print(
                f"ERROR on formatted the file '{filename}' with config:\n"
                f"{self.dump_yaml(config)}\n{exception}"
            )
            return False
        return True


class Prettier:
    """
    Load prettier.js.
    """

    module: Optional[PrettierModule] = None

    def __enter__(self) -> PrettierModule:
        """
        Initialise.
        """
        with open(os.path.join(os.path.dirname(__file__), "prettier.js"), encoding="utf-8") as query_open:
            javascript = query_open.read()

        self.module = PrettierModule(
            node_vm2.NodeVM.code(
                javascript,
                os.path.join(os.path.dirname(__file__), "node_modules"),
                console="inherit",
                require={"external": True},
            )
        )
        return self.module

    def __exit__(
        self,
        tpe: Optional[Type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Any:
        """
        Close.
        """
        assert self.module is not None

        return self.module.module.__exit__(tpe, value, traceback)


def dump_yaml(data: Dict[str, Any], filename: str = "ci/config.yaml") -> str:
    """
    Dump the YAML according to the prettier configuration.

    Arguments:
        data: The content of the YAML
        filename: The destination file name
    """
    with Prettier() as prettier:
        return prettier.dump_yaml(data, filename)
