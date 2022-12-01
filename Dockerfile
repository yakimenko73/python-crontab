FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
COPY /src ./src
COPY /config ./config

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD cd src && python3 main.py