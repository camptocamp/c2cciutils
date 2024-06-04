"""
Read the table of versions from SECURITY.md.
"""

import xml.etree.ElementTree  # nosec
from typing import Optional

import markdown
from markdown.extensions.tables import TableExtension

HEADER_VERSION = "Version"
HEADER_ALTERNATE_TAG = "Alternate Tag"
HEADER_SUPPORTED_UNTIL = "Supported Until"
SUPPORT_TO_BE_DEFINED = "To be defined"
SUPPORT_BEST_EFFORT = "Best effort"
SUPPORT_UNSUPPORTED = "Unsupported"


class Security:
    """
    Read the table of versions from SECURITY.md.
    """

    headers: list[str]
    data: list[list[str]]
    _row: Optional[list[str]] = None

    def __init__(self, status: str, check: bool = True):
        """
        Initialize.

        Arguments:
            status: the content of the SECURITY.md file.
            check: Set to `False` to skip the check.
        """

        self.headers = []
        self.data = []

        markdown_instance = markdown.Markdown(extensions=[TableExtension()])

        elem = markdown_instance.parser.parseDocument(
            [s for s in status.split("\n") if s != "" and s[0] == "|"]
        )
        self._pe(elem.getroot())

        self.data = [r for r in self.data if len([c for c in r if c is not None]) > 0]

        self.version_index = self.headers.index(HEADER_VERSION) if HEADER_VERSION in self.headers else -1
        self.alternate_tag_index = (
            self.headers.index(HEADER_ALTERNATE_TAG) if HEADER_ALTERNATE_TAG in self.headers else -1
        )
        self.support_until_index = (
            self.headers.index(HEADER_SUPPORTED_UNTIL) if HEADER_SUPPORTED_UNTIL in self.headers else -1
        )

        # Check the content if the content isn't empty
        if check and status:
            if not self.check(verbose=0):
                raise ValueError("SECURITY.md file is not valid.")

    def check(self, verbose: int = -1) -> bool:
        """
        Check the content.

        Arguments:
            verbose: the verbosity level, `-1` for no output, `0` for errors only, `1` for all.

        Return:
            `True` if the content is valid, `False` otherwise.
        """

        success = True
        if self.version_index == -1:
            if verbose >= 0:
                print("`Version` column not found.")
            success = False
        elif verbose >= 1:
            print(f"`Version` column found at index {self.version_index}.")

        if self.alternate_tag_index == -1:
            if verbose >= 1:
                print("Optional `Alternate Tag` column not found.")
        elif verbose >= 1:
            print(f"`Alternate Tag` column found at index {self.alternate_tag_index}.")

        if self.support_until_index == -1:
            if verbose >= 0:
                print("`Supported Until` column not found.")
            success = False
        elif verbose >= 1:
            print(f"`Supported Until` column found at index {self.support_until_index}.")

        return success

    def _pe(self, elem: xml.etree.ElementTree.Element) -> None:
        """
        Parse the HTML table.

        Arguments:
            elem: The XML element
        """
        if elem.tag == "th":
            assert elem.text is not None
            self.headers.append(elem.text)
        if elem.tag == "tr":
            self._row = []
            self.data.append(self._row)
        if elem.tag == "td":
            self._row.append(elem.text)  # type: ignore
        for element in list(elem):
            self._pe(element)
