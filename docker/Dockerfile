FROM debian:buster-slim

COPY requirements.txt /etc/requirements.txt
COPY git-blacklist /etc/apt/preferences.d/git-blacklist

RUN apt-get update && apt-get -y upgrade && apt-get -y install python3 python3-pip && pip3 install -r /etc/requirements.txt && apt-get -y clean

