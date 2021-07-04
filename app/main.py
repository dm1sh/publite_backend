from fastapi import FastAPI, File, UploadFile, HTTPException

from .epub import epub2html
from .fb2 import fb22html
from .utils import HashedHTMLBook, add_hash

app = FastAPI()


@app.get("/")
def root():
    return "Hello, World!"


@app.post("/uploadfile/", response_model=HashedHTMLBook)
async def create_upload_file(file: UploadFile = File(...)):
    if file.filename.endswith(".fb2"):
        content = await fb22html(file.file)
    elif file.filename.endswith(".epub"):
        content = await epub2html(file.file)
    else:
        raise HTTPException(status_code=415, detail="Error! Unsupported file type")

    h_content = add_hash(content)

    return h_content
