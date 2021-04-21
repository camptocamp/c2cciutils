# -*- coding: utf-8 -*-


import xml.etree.ElementTree
from typing import List, Optional

import markdown
from markdown.extensions.tables import TableExtension


class Security:
    """
    Read the table of versions got from SECURITY.md
    """

    headers: List[str]
    data: List[List[str]]
    _row: Optional[List[str]] = None

    def __init__(self, status: str):
        """
        Parameters:
            status: the content of the SECURITY.md file.
        """

        self.headers = []
        self.data = []

        markdown_instance = markdown.Markdown(extensions=[TableExtension()])

        elem = markdown_instance.parser.parseDocument(  # type: ignore
            [s for s in status.split("\n") if s != "" and s[0] != "#" and s[0] != "["]
        )
        self._pe(elem.getroot())

        self.data = [r for r in self.data if len([c for c in r if c is not None]) > 0]
        for row in self.data:
            row.append("")

    def _pe(self, elem: xml.etree.ElementTree.Element) -> None:
        """
        Parse the HTML table
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
