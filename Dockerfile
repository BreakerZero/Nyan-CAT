FROM python:3.12.10-alpine3.21

LABEL maintainer="Breaker000"

RUN apk update && apk add --no-cache \
    coreutils \
    curl \
    unzip \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-distutils-extra \
    openjdk11-jre \
    bash \
    git \
    build-base \
    python3-dev \
    ffmpeg \
    lapack-dev \
    blas-dev \
    libgcc \
    libjpeg-turbo-dev \
    libpng-dev \
    tiff-dev \
    openblas-dev \
    gfortran \
    gtk+3.0-dev \
    gstreamer-dev \
    libdc1394-dev \
    pipx \
    && pipx ensurepath

WORKDIR /app

COPY requirements.txt requirements.txt

RUN curl -L -o languagetool.zip https://languagetool.org/download/LanguageTool-stable.zip && \
    unzip languagetool.zip -d /app/languagetool && \
    rm languagetool.zip

RUN pipx install --python python3 gunicorn \
    && pipx inject gunicorn  -r requirements.txt

COPY / /app

RUN chmod +x /app/init_database.sh

EXPOSE 5000 8081

ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD /app/init_database.sh