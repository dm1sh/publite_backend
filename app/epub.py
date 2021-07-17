"""
Module for EPUB file conversion to html
"""

import html
import os
from base64 import b64encode
from functools import cache
from tempfile import SpooledTemporaryFile

import aiofiles
import ebooklib
from ebooklib import epub
from fastapi import HTTPException
from lxml import etree

from .utils import DocumentTokens, HTMLBook, strip_whitespace

parser = etree.XMLParser(recover=True)

IMAGE = "{http://www.w3.org/2000/svg}image"
HREF = "{http://www.w3.org/1999/xlink}href"


async def epub2html(file: SpooledTemporaryFile) -> HTMLBook:

    """
    Splits epub to tokens and joins them to one html file
    """

    try:
        tokens, spine = await epub_to_tokens(file)
        set_cover(tokens)

        html_content = epub_tokens2html(spine, tokens)

        return {
            **(tokens["metadata"]),
            "content": html_content,
        }

    except Exception as err:
        raise HTTPException(
            status_code=500, detail="Error! Wrong epub file format: " + str(err)
        ) from err


async def epub_to_tokens(
    file: SpooledTemporaryFile,
) -> tuple[DocumentTokens, list[tuple[str, str]]]:

    r"""
    Passes file content to EbookLib library and parses epub tokens into dict of
    the following format:

    { "\<file_name\>": "\<file_content\>" }

    Where file content is either plain text for xhtml or base64 encoded data
    for other formats, prepared for embeding to html
    """

    tokens = {}

    async with aiofiles.tempfile.NamedTemporaryFile() as tmp:
        await tmp.write(file.read())

        # Reading book file
        reader = epub.EpubReader(tmp.name)
        book = reader.load()
        reader.process()

        tokens["metadata"] = read_metadata(book)
        tokens["toc"] = {}

        # Iterating over Items

        for item in book.get_items():
            item: epub.EpubItem

            item_type = item.get_type()
            file_path = os.path.join(reader.opf_dir, item.get_name())

            if item_type == ebooklib.ITEM_DOCUMENT:
                # Adding book chapters to tokens list
                name = item.get_id()
                tokens[file_path] = strip_whitespace(item.get_body_content())
                tokens["toc"][name] = file_path

            elif item_type in (
                ebooklib.ITEM_AUDIO,
                ebooklib.ITEM_COVER,
                ebooklib.ITEM_IMAGE,
                ebooklib.ITEM_VECTOR,
                ebooklib.ITEM_VIDEO,
            ):
                # Adding assets to tokens list

                content = item.get_content()
                media_type = item.media_type
                b64_content = b64encode(content).decode()

                tokens[file_path] = f"data:{media_type};base64,{b64_content}"

                if item_type == ebooklib.ITEM_COVER:
                    tokens["metadata"]["cover"] = file_path

    return tokens, book.spine.copy()


def read_metadata(book: epub.EpubBook) -> dict[str, str]:
    """
    Reads metadata from xml to dict
    """

    metadata = {}
    metadata["title"] = book.get_metadata("DC", "title")[0][0]
    metadata["author"] = convert_list(book.get_metadata("DC", "creator"))

    return metadata.copy()


def convert_list(titles_list: list[tuple[str, dict[str, str]]]) -> str:
    """
    Joins titles list to one string
    """

    res = []
    for title_obj in titles_list:
        res.append(title_obj[0])

    return "; ".join(res)


def set_cover(tokens: DocumentTokens) -> None:
    """
    Converts cover file name to base64 image stored in `tokens`
    """

    cover_name = tokens["metadata"].get("cover")
    if cover_name in tokens.keys():
        tokens["metadata"]["cover"] = tokens[cover_name]


def epub_tokens2html(spine: list[tuple[str, str]], tokens: DocumentTokens) -> bytes:
    """
    Joins chapters in `spice` to one html string
    """

    res = ""

    for name, _ in spine:
        file_path = tokens["toc"].get(name)
        if file_path:
            res += process_xhtml(file_path, tokens)

    return html.unescape(res)


def process_xhtml(path: str, tokens: DocumentTokens) -> bytes:
    """
    Processes content of one xml body
    """

    xml: etree.Element = etree.fromstring(tokens[path], parser=parser)

    if xml.tag == "body":
        xml.tag = "div"

    process_content(xml, path, tokens)

    return (
        f'<section id="b_{path_to_name(path)}">{etree.tostring(xml).decode()}</section>'
    )


def process_content(node: etree.Element, path: str, tokens: DocumentTokens) -> None:
    """
    Recursive function for xml element convertion to valid html
    """

    # Process universal tags

    if node.get("epub:type"):
        node.attrib.pop("epub:type")
    el_id = node.get("id")
    if el_id:
        node.set("id", f"{path_to_name(path)}_{el_id}")

    # Tag processing

    if node.tag == "a":
        process_a_element(node, path)

    elif node.tag == "hgroup":
        node.tag = "div"

    elif node.tag in ("img", "source", "video", "audio"):
        process_media_element(node, path, tokens)

    elif node.tag == IMAGE:
        href = node.get(HREF)
        media_path = rel_to_abs_path(path, href)
        if media_path in tokens.keys():
            node.set(HREF, tokens[media_path])

    elif node.tag == "trigger":
        node.getparent().remove(node)

    # Recursively run for all children

    for child in node:
        process_content(child, path, tokens)


def process_a_element(node: etree.Element, path: str):
    r"""
    Converts `filed` links to ids in \<a\> element
    """

    href = node.get("href")
    if href.count(".xhtml") or href.count(".html"):
        id_pos = href.rfind("#")
        if id_pos != -1:
            href_path, el_id = href[:id_pos], href[id_pos:]
            node.set("href", f"#{path_to_name(href_path)}_{el_id[1:]}")
        else:
            node.set("href", f"#b_{path_to_name(href)}")
    elif href.count("#"):
        node.set("href", f"#{path_to_name(path)}_{href[1:]}")


def process_media_element(node: etree.Element, path: str, tokens: DocumentTokens):
    """
    Replaces file paths to base64 encoded media in `src` and `srcset` tags
    """

    src = node.get("src")
    attr = "src"

    if not src:
        src = node.get("srcset")
        attr = "srcset"

    if src:
        media_path = rel_to_abs_path(path, src)
        if media_path in tokens.keys():
            node.set(attr, tokens[media_path])


def rel_to_abs_path(parent: str, rel: str):
    """
    Helper for relative path to media convertion to absolute
    """

    return os.path.normpath(os.path.join(os.path.dirname(parent), rel))


@cache
def path_to_name(path: str) -> str:
    """
    Helper function for getting file name
    """

    return os.path.basename(path).split(".")[0]


def children_to_html(root: etree.Element) -> bytes:
    """
    Converts all xml children of element to string and joins them
    """

    res = b""

    for child in root:
        res += etree.tostring(child)

    return res
