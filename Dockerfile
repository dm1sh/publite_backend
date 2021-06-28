FROM python

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

EXPOSE 80

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]