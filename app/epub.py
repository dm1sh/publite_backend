import aiofiles as aiof
from base64 import b64encode
from fastapi import HTTPException

import ebooklib
from ebooklib import epub

from tempfile import SpooledTemporaryFile

from .utils import Document_Tokens


async def epub2html(file: SpooledTemporaryFile) -> str:

    """
    Splits epub to tokens and joins them to one html file
    """

    try:
        tokens = await epub_to_tokens(file)

        print(tokens["metadata"])
        ...
        # TODO: join tokens to HTML
        html_content = ""
        ...
        return {**(tokens["metadata"]), "content": html_content}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error! Wrong epub file format: " + str(e)
        )


async def epub_to_tokens(file: SpooledTemporaryFile) -> Document_Tokens:

    """
    Passes file content to EbookLib library and parses epub tokens into dict of the following format:

    { "\<file_name\>": "\<file_content\>" }

    Where file content is either plain text for xhtml or base64 encoded data for other formats, prepared for embeding to html
    """

    tokens = {}

    async with aiof.tempfile.NamedTemporaryFile() as tmp:
        await tmp.write(file.read())

        book = epub.read_epub(tmp.name)

        # Adding book metadata to tokens list

        metadata = {}
        metadata["title"] = convert_list(book.get_metadata("DC", "title"))
        metadata["author"] = convert_list(book.get_metadata("DC", "creator"))

        tokens["metadata"] = metadata.copy()

        # Iterating over Items

        for item in book.get_items():

            item_type = item.get_type()
            name = item.get_name()
            content = item.get_content()

            if item_type == ebooklib.ITEM_DOCUMENT:
                # Adding book chapters to tokens list
                tokens[name] = content

            elif item_type in (
                ebooklib.ITEM_COVER,
                ebooklib.ITEM_IMAGE,
                ebooklib.ITEM_STYLE,
                ebooklib.ITEM_VIDEO,
                ebooklib.ITEM_VECTOR,
            ):
                # Adding assets to tokens list
                media_type = item.media_type
                b64_content = b64encode(content).decode()

                tokens[name] = f"data:{media_type};base64,{b64_content}"

                if item_type == ebooklib.ITEM_COVER:
                    tokens["metadata"]["cover"] = name

    return tokens


def convert_list(titles_list: list[tuple[str, dict[str, str]]]):
    res = []
    for title_obj in titles_list:
        res.append(title_obj[0])

    return "; ".join(res)
