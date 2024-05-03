FROM python:latest

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV TB_SERVER_ADDRESS ""
ENV REPORT_INTERVAL ""
ENV MQTT_BROKER_ADDRESS ""
ENV MQTT_BROKER_PORT 1883
ENV MQTT_BROKER_USER ""
ENV MQTT_BROKER_PASSWORD ""
LABEL authors="tomer.klein@gmail.com"

RUN apt -yqq update && \
    apt -yqq install fping && \
    rm -rf /var/lib/apt/lists/*
    
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --upgrade setuptools --no-cache-dir &&

COPY requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /app/config

COPY app /app

WORKDIR /app

ENTRYPOINT python app.py