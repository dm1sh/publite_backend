from typing import Union, Optional
from pydantic import BaseModel
import re
from hashlib import sha256

Document_Tokens = dict[str, Union[str, dict[str, str]]]


class HTMLBook(BaseModel):
    title: str
    author: str
    cover: Optional[str]
    content: str


class HashedHTMLBook(HTMLBook):
    hash: str


replacements = [
    ("&#13;", "\r"),
    (">\s+?<", "><"),
]


def strip_whitespace(s: bytes) -> str:
    res = s.decode()

    for old, new in replacements:
        res = re.sub(old, new, res)

    return res.strip()


def add_hash(content: HTMLBook) -> HashedHTMLBook:
    h_content: HashedHTMLBook = content.copy()
    h_content["hash"] = sha256(content["content"].encode()).hexdigest()

    return h_content
