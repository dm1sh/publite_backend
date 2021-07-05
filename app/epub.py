import aiofiles as aiof
from base64 import b64encode
from fastapi import HTTPException

import ebooklib
from ebooklib import epub

from tempfile import SpooledTemporaryFile

from .utils import Document_Tokens, strip_whitespace, HTMLBook


async def epub2html(file: SpooledTemporaryFile) -> HTMLBook:

    """
    Splits epub to tokens and joins them to one html file
    """

    try:
        tokens, spine = await epub_to_tokens(file)
        set_cover(tokens)

        html_content = epub_tokens2html(spine, tokens)

        return {**(tokens["metadata"]), "content": strip_whitespace(html_content)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error! Wrong epub file format: " + str(e)
        )


async def epub_to_tokens(
    file: SpooledTemporaryFile,
) -> tuple[Document_Tokens, list[tuple[str, str]]]:

    """
    Passes file content to EbookLib library and parses epub tokens into dict of the following format:

    { "\<file_name\>": "\<file_content\>" }

    Where file content is either plain text for xhtml or base64 encoded data for other formats, prepared for embeding to html
    """

    tokens = {}

    async with aiof.tempfile.NamedTemporaryFile() as tmp:
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
            file_path = reader.opf_dir + "/" + item.get_name()

            if item_type == ebooklib.ITEM_DOCUMENT:
                # Adding book chapters to tokens list
                name = item.get_id()
                tokens[file_path] = item.get_body_content()
                tokens["toc"][name] = file_path

            elif item_type in (
                ebooklib.ITEM_COVER,
                ebooklib.ITEM_IMAGE,
                ebooklib.ITEM_VIDEO,
                ebooklib.ITEM_VECTOR,
            ):
                # Adding assets to tokens list

                content = item.get_content()
                media_type = item.media_type
                b64_content = b64encode(content).decode()

                tokens[file_path] = f"data:{media_type};base64,{b64_content}"

                if item_type == ebooklib.ITEM_COVER:
                    tokens["metadata"]["cover"] = file_path

    return tokens, book.spine.copy()


def read_metadata(book: epub.EpubBook):
    metadata = {}
    metadata["title"] = book.get_metadata("DC", "title")[0][0]
    metadata["author"] = convert_list(book.get_metadata("DC", "creator"))

    return metadata.copy()


def convert_list(titles_list: list[tuple[str, dict[str, str]]]):
    res = []
    for title_obj in titles_list:
        res.append(title_obj[0])

    return "; ".join(res)


def set_cover(tokens: Document_Tokens):
    cover_name = tokens["metadata"].get("cover")
    if cover_name in tokens.keys():
        tokens["metadata"]["cover"] = tokens[cover_name]


def epub_tokens2html(spine: list[tuple[str, str]], tokens: Document_Tokens):
    res = b""

    for name, _ in spine:
        file_path = tokens["toc"].get(name)
        if file_path:
            res += process_xhtml(file_path, tokens)

    return res


def process_xhtml(path: str, tokens: Document_Tokens):
    # TODO: Add xhtml procession
    return tokens[path]
