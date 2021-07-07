FROM python

WORKDIR /srv

COPY ./requirements /srv/requirements

RUN pip install -r requirements/prod.txt

EXPOSE 80

COPY ./app /srv/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]