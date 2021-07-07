"""
Utils for publite_backend module
"""


import re
from hashlib import sha256
from typing import Optional, Union

from pydantic import BaseModel  # pylint: disable=no-name-in-module

DocumentTokens = dict[str, Union[str, dict[str, str]]]


class HTMLBook(BaseModel):  # pylint: disable=too-few-public-methods
    """Transitional model for returned book data"""

    title: str
    author: str
    cover: Optional[str]
    content: str


class HashedHTMLBook(HTMLBook):  # pylint: disable=too-few-public-methods
    """Model for returned book data with content hash"""

    hash: str


replacements = [
    ("&#13;", ""),
    ("&#17;", ""),
    (r">\s+?<", "><"),
]


def strip_whitespace(string: bytes) -> str:

    """Removes"""

    res = string.decode()

    for old, new in replacements:
        res = re.sub(old, new, res)

    return res.strip()


def add_hash(content: HTMLBook) -> HashedHTMLBook:

    """
    Adds hash of book content
    """

    h_content: HashedHTMLBook = content.copy()
    h_content["hash"] = sha256(content["content"].encode()).hexdigest()

    return h_content
