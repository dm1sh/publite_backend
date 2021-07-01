from typing import Union, Optional
from pydantic import BaseModel
import re

Document_Tokens = dict[str, Union[str, dict[str, str]]]


class HTMLBook(BaseModel):
    title: str
    author: str
    cover: Optional[str]
    content: str


def strip_whitespace(s: bytes) -> str:
    return re.sub("\s+(?=<)", "", s.decode()).strip()
