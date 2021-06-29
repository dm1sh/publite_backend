from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

from .epub import epub2html

app = FastAPI()

@app.get('/')
def root():
    return "Hello, World!"

@app.post('/uploadfile/', )
async def create_upload_file(file: UploadFile = File(...)):
    if file.filename.endswith('.epub'):
        content = await epub2html(file.file)
    elif file.filename.endswith('.fb2'):
        content = await fb22html(file.file)
    else:
        content = 'Error! Unsupported file type'
    return HTMLResponse(content=content)