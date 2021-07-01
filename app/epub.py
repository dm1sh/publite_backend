import aiofiles as aiof
from base64 import b64encode

import ebooklib
from ebooklib import epub

from tempfile import SpooledTemporaryFile


async def epub2html(file: SpooledTemporaryFile) -> str:

    """
    Splits epub to tokens and joins them to one html file
    """

    try:
        tokens = await epub_to_tokens(file)
        ...
        # TODO: join tokens to HTML
        html_content = ""
        ...
        return html_content

    except Exception as e:
        return "Error! Wrong epub file format: " + str(e)


async def epub_to_tokens(file: SpooledTemporaryFile) -> dict[str, str]:

    """
    Passes file content to EbookLib library and parses epub tokens into dict of the following format:

    { "\<file_name\>": "\<file_content\>" }

    Where file content is either plain text for xhtml or base64 encoded data for other formats, prepared for embeding to html
    """

    tokens = {"metadata": {"test": "t"}}

    async with aiof.tempfile.NamedTemporaryFile() as tmp:
        await tmp.write(file.read())

        book = epub.read_epub(tmp.name)
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

    return tokens
