"""
Automatically generated file from a JSON schema.
"""

from typing import Literal, TypedDict, Union

# | Application configuration.
# |
# | An application configuration
ApplicationConfiguration = TypedDict(
    "ApplicationConfiguration",
    {
        # | URL pattern.
        # |
        # | URL pattern, to be used for files that didn't come from GitHub release, available arguments: {version}
        "url-pattern": str,
        # | The type of file.
        # |
        # | The type of file
        "type": "TheTypeOfFile",
        # | The filename to get.
        # |
        # | The name of the file to get in the GitHub release
        "get-file-name": str,
        # | The created tile name.
        # |
        # | The name of the final tile we will create
        "to-file-name": str,
        # | The tile name to get in the tar file.
        "tar-file-name": str,
        # | The commands to run after the tile creation.
        "finish-commands": list[list[str]],
    },
    total=False,
)


ApplicationsConfiguration = dict[str, "ApplicationConfiguration"]
"""
Applications configuration.

All the applications configuration
"""


TheTypeOfFile = Union[Literal["tar"]]
"""
The type of file.

The type of file
"""
THETYPEOFFILE_TAR: Literal["tar"] = "tar"
"""The values for the 'The type of file' enum"""
