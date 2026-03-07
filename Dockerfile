# ---------- builder ----------
FROM python:3.13-alpine3.23 AS builder

LABEL maintainer="Breaker000"
WORKDIR /app

RUN apk add --no-cache \
    bash curl unzip git \
    build-base python3-dev gfortran \
    lapack-dev blas-dev openblas-dev \
    libjpeg-turbo-dev libpng-dev tiff-dev \
    gtk+3.0-dev gstreamer-dev libdc1394-dev

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --venv /opt/venv

FROM python:3.12.10-alpine3.21

WORKDIR /app

RUN apk add --no-cache \
    bash curl unzip \
    coreutils \
    ffmpeg \
    openjdk11-jre \
    libgcc libstdc++ \
    openblas \
    libjpeg-turbo libpng tiff \
    gtk+3.0 gstreamer libdc1394

RUN curl -L -o languagetool.zip https://internal1.languagetool.org/snapshots/LanguageTool-latest-snapshot.zip && \
    unzip languagetool.zip -d /app/languagetool && \
    rm languagetool.zip

COPY --from=builder /opt/venv /opt/venv

COPY . /app

RUN chmod +x /app/init_database.sh

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000 8081

CMD ["/app/init_database.sh"]
