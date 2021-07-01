from tempfile import SpooledTemporaryFile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from typing import Optional


namespaces = {
    "": "http://www.gribuser.ru/xml/fictionbook/2.0",
    "xlink": "http://www.w3.org/1999/xlink",
}
HREF = f"{{{namespaces['xlink']}}}href"


async def fb22html(file: SpooledTemporaryFile) -> str:

    """
    Splits fb2 to tokens and joins them to one html file
    """

    try:

        tokens = fb22tokens(file)
        ...
        # TODO: join tokens to HTML
        html_content = ""
        ...
        return html_content

    except Exception as e:
        return "Error! Wrong FB2 file format: " + str(e)


def fb22tokens(file: SpooledTemporaryFile) -> dict[str, str]:

    """
    Parses fb2 file as xml document. It puts book metadata, its content and media to `tokens` dictionary and returns it.

    `tokens` format:

    { "metadata": { ... },

    "content": "\<string\>",

    "\<asset_id\>": "\<base64_data\>" }
    """

    tokens = {"metadata": {}, "content": ""}

    book = ET.parse(file)
    description, body, *assets = book.getroot()

    description: Element
    body: Element
    assets: list[Element]

    # Reading book metadata

    book_info = description.find("title-info")
    if book_info:
        metadata = {}
        metadata["title"] = book_info.find("book-title", namespaces).text
        metadata["author"] = get_author(book_info.find("author", namespaces))
        metadata["cover"] = get_cover(book_info.find("coverpage", namespaces))
        if metadata["cover"] is None:
            metadata.pop("cover")

        if len(metadata.keys()):
            tokens["metadata"] = metadata.copy()

    # Reading book content

    tokens["content"] = ET.tostring(body).replace(b"ns0:", b"")

    # Reading assets

    for asset in assets:
        key = asset.get("id")
        media_type = asset.get("content-type")
        b64_content = asset.text
        tokens[key] = f"data:{media_type};base64,{b64_content}"

    return tokens


def get_author(author: Element) -> str:

    """
    Converts author xml structure to string
    """

    res = []
    for tag_name in ("first-name", "middle-name", "last-name"):
        el = author.find(tag_name, namespaces)
        if not el is None:
            res.append(el.text)
    if len(res) == 0:
        res = author.find("nickname", namespaces).text
    else:
        res = " ".join(res)

    return res


def get_cover(coverpage: Optional[Element]) -> Optional[str]:

    """
    Extracts cover image id if exists
    """

    if coverpage:
        return coverpage.find("image", namespaces).get(HREF)
