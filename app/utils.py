from typing import Union, Optional
from pydantic import BaseModel
import re

Document_Tokens = dict[str, Union[str, dict[str, str]]]


class HTMLBook(BaseModel):
    title: str
    author: str
    cover: Optional[str]
    content: str


replacements = [
    ("&#13;", "\r"),
    (">\s+?<", "><"),
]


def strip_whitespace(s: bytes) -> str:
    res = s.decode()

    for old, new in replacements:
        res = re.sub(old, new, res)

    return res.strip()
