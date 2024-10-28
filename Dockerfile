FROM ubuntu:latest

LABEL maintainer="Breaker000"

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    git \
    && apt-get clean

WORKDIR /app

RUN python3 -m venv /app/venv

COPY requirements.txt requirements.txt
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt
RUN /app/venv/bin/pip install gunicorn

COPY / /app

#RUN mv /app/static/js/ControlInput.js /app/static/js/controlInput.js

RUN chmod +x /app/init_database.sh

EXPOSE 5000

ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

ENTRYPOINT ["/app/init_database.sh"]