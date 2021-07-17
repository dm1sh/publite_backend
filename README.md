# publite backend

<p align="center">
  <img src="https://github.com/dm1sh/publite_backend/raw/main/logo.svg" alt="publite" width="150px">
</p>

## Overview

Backend for online ebook viewer publite

## Deploy

Run app locally (development only!)

```bash
# install requirements
pip install -r requirements/dev.txt

# run app with uvicorn
uvicorn app.main:app --reload --port <port>
```

Run app locally (test prod)

```bash
# install requirements
pip install -r requirements/prod.txt

# run app with uvicorn
uvicorn app.main:app --port <port>

# or

# run with python script
python run.py
```

Simple docker deployment

```bash
# build docker image
docker build . -t publite_backend

# run it with docker
docker run -p <port>:80 publite_backend
```

Dokku deployment with image from Docker Hub

```bash
dokku apps:create publitebackend

# increase file size limit to be able to upload bigger books
dokku nginx:set publitebackend client_max_body_size 50m

dokku git:from-image publitebackend publite/backend:latest
```

# TODO

- Separate epub and fb2 files to python modules
- Rewrite own `.opf` file parsing to get rid of dependency on EbookLib
- Add cli interfaces for epub and fb2 libs
