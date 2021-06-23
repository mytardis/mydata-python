FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN pip install --upgrade pip

WORKDIR /app
COPY ./ /app

RUN pip install -r requirements.txt
RUN pip install -r requirements-test.txt
