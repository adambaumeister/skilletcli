FROM ubuntu:latest
COPY . /skilletcli
WORKDIR /skilletcli
RUN apt update -y
RUN apt upgrade -y python3
RUN python3 -m venv venv && \
    source venv\bin\activate
RUN pip install -r requirements.txt
