"""
Module for FB2 file conversion to html
"""

import html
import xml.etree.ElementTree as ET
from tempfile import SpooledTemporaryFile
from typing import Optional
from xml.etree.ElementTree import Element

from fastapi import HTTPException

from .utils import DocumentTokens, HTMLBook, strip_whitespace

namespaces = {
    "": "http://www.gribuser.ru/xml/fictionbook/2.0",
    "xlink": "http://www.w3.org/1999/xlink",
}
HREF = f"{{{namespaces['xlink']}}}href"


async def fb22html(file: SpooledTemporaryFile) -> HTMLBook:

    """
    Splits fb2 to tokens and joins them to one html file
    """

    try:
        tokens = fb22tokens(file)
        set_cover(tokens)
        html_content = fb2body2html(tokens)

        return {
            **(tokens["metadata"]),
            "content": html.escape(html.unescape(html_content.decode())),
        }

    except Exception as err:
        raise HTTPException(
            status_code=500, detail="Error! Wrong fb2 file format: " + str(err)
        ) from err


def fb22tokens(file: SpooledTemporaryFile) -> DocumentTokens:

    r"""
    Parses fb2 file as xml document.
    It puts book metadata, its content and media to `tokens` dictionary and returns it.

    `tokens` format:

    { "metadata": { ... },

    "content": "\<string\>",

    "\<asset_id\>": "\<base64_data\>" }
    """

    tokens = {
        "metadata": {
            "title": "",
            "author": "",
        },
        "content": b"<root>",
    }

    book = ET.parse(file)
    root = book.getroot()

    description = root.find("./description", namespaces)
    bodies = root.findall("./body", namespaces)
    assets = root.findall("./binary", namespaces)

    # Reading book metadata

    book_info = description.find("./title-info", namespaces)
    if book_info:
        metadata = {}
        metadata["title"] = book_info.find("./book-title", namespaces).text
        metadata["author"] = get_author(book_info.find("./author", namespaces))
        metadata["cover"] = get_cover(book_info.find("./coverpage", namespaces))
        if "cover" not in metadata.keys():
            metadata.pop("cover")

        if len(metadata.keys()) != 0:
            tokens["metadata"] = metadata.copy()

    # Reading book content

    for body in bodies:
        tokens["content"] += ET.tostring(body).replace(b"ns0:", b"")

    tokens["content"] += b"</root>"

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
    for tag_name in (
        "first-name",
        "middle-name",
        "last-name",
    ):
        tag = author.find("./" + tag_name, namespaces)
        if tag is not None:
            res.append(tag.text)
    if len(res) == 0:
        res = author.find("./nickname", namespaces).text
    else:
        res = " ".join(res)

    return res


def get_cover(coverpage: Optional[Element]) -> Optional[str]:

    """
    Extracts cover image id if exists
    """

    if coverpage:
        return coverpage.find("./image", namespaces).get(HREF)

    return None


def set_cover(tokens: DocumentTokens) -> None:
    """Gets cover from book and sets it in metadata"""
    cover = tokens["metadata"]["cover"]
    if cover is None:
        tokens["metadata"]["cover"] = "none"
    elif cover[0] == "#":
        tokens["metadata"]["cover"] = tokens[cover[1:]]


def fb2body2html(tokens: DocumentTokens) -> str:

    """
    Convert fb2 xml to html, joins bodies into one string
    """

    res = b""

    xml_root = ET.fromstring(strip_whitespace(tokens["content"]))
    for body in xml_root.iterfind("./body"):
        res += process_section(body, tokens)

    return res


def process_section(body: Element, tokens: DocumentTokens) -> str:

    """
    Processes individual sections, recursively goes throw sections tree
    """

    res = b"<section>\n"

    for tag_name in ("title", "epigraph", "annotation"):
        tag = body.find("./" + tag_name)
        if tag:
            process_content(tag, tokens)
            res += children_to_html(tag)
    image = body.find("./image")
    if image:
        process_image(image, tokens)
        res += ET.tostring(image)

    for section in body.findall("./section"):
        if section.find("./section"):
            res += process_section(section, tokens)
        else:
            process_content(section, tokens)
            res += b"<section>\n" + children_to_html(section) + b"</section>\n"

    return res + b"</section>\n"


def children_to_html(root: Element) -> str:

    """
    Converts xml tag children to string
    """

    res = b""

    for child in root:
        res += ET.tostring(child)

    return res


def process_image(element: Element, tokens: DocumentTokens) -> None:

    r"""
    Converts fb2 \<image /\> to html \<img /\>. Replaces xlink:href with src="\<base64_image_data\>"
    """

    element.tag = "img"

    href = element.get(HREF)
    element.attrib.pop(HREF)

    element.set("src", tokens[href[1:]] if href[0] == "#" else href)


tag_replacement = {
    "empty-line": "br",
    "emphasis": "em",
    "strikethrough": "strike",
    "v": "p",
}

tag_with_class = {
    "subtitle": "p",
    "cite": "div",
    "poem": "div",
    "stanza": "div",
    "epigraph": "div",
    "text-author": "p",
}


def process_content(root: Element, tokens: DocumentTokens) -> None:

    """
    Converts fb2 xml tag names to html equivalents and my own styled elements.
    Resolves binary data dependencies
    """

    for child in root:
        process_content(child, tokens)

        if child.tag == "a":
            href = child.get(HREF)
            child.attrib.pop(HREF)
            child.set("href", href)

        if child.tag == "image":
            process_image(child, tokens)

        elif child.tag in tag_replacement.keys():
            child.tag = tag_replacement[child.tag]

        elif child.tag in tag_with_class.keys():
            child.set("class", child.tag)
            child.tag = tag_with_class[child.tag]
