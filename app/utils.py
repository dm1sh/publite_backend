from typing import Union, Optional
from pydantic import BaseModel

Document_Tokens = dict[str, Union[str, dict[str, str]]]


class HTMLBook(BaseModel):
    title: str
    author: str
    cover: Optional[str]
    content: str
