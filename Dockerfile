FROM python

WORKDIR /srv

COPY ./requirements.txt /srv/requirements.txt

RUN pip install -r requirements.txt

EXPOSE 80

COPY ./app /srv/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]