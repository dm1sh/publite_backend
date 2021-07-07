"""Webserver for epub and fb2 files convertation to html"""

from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel  # pylint: disable=no-name-in-module

from .epub import epub2html
from .fb2 import fb22html
from .utils import HashedHTMLBook, add_hash


class DebugInfo(BaseModel):  # pylint: disable=too-few-public-methods
    """Main handler return types"""

    startup_time: str


app = FastAPI()

start_time = datetime.now()


@app.get("/", response_model=DebugInfo)
def root():
    """
    Test if server is running.

    Returns startup time
    """
    return {"startup_time": start_time.isoformat()}


@app.post("/uploadfile/", response_model=HashedHTMLBook)
async def create_upload_file(file: UploadFile = File(...)):
    """
    Main api handler:

    Accepts files with fb2 and epub extensions

    Returns HTTP 415 error if file has unsupported format

    Else returns object with book metadata and its html
    """
    if file.filename.endswith(".fb2"):
        content = await fb22html(file.file)
    elif file.filename.endswith(".epub"):
        content = await epub2html(file.file)
    else:
        raise HTTPException(status_code=415, detail="Error! Unsupported file type")

    h_content = add_hash(content)

    return h_content
