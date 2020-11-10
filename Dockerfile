FROM python:3.7.6-slim-buster

ENV PYTHONPATH /sources

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git make gcc

WORKDIR /sources

ADD ./requirements.txt /sources/requirements.txt

RUN pip install -r /sources/requirements.txt

ADD . /sources

RUN ["chmod", "+x", "/sources/run_server.sh"]
