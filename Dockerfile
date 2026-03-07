# ---------- builder ----------
FROM python:3.13-alpine3.23 AS builder

LABEL maintainer="Breaker000"
WORKDIR /app

RUN cat /etc/apk/repositories
RUN apk update

RUN apk add --no-cache bash curl unzip git
RUN apk add --no-cache build-base python3-dev gfortran
RUN apk add --no-cache lapack-dev blas-dev openblas-dev
RUN apk add --no-cache libjpeg-turbo-dev libpng-dev tiff-dev
RUN apk add --no-cache gstreamer-dev libdc1394-dev

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --venv /opt/venv

FROM python:3.13-alpine3.23

WORKDIR /app

RUN cat /etc/apk/repositories
RUN apk update

RUN apk add --no-cache bash curl unzip git
RUN apk add --no-cache coreutils ffmpeg openjdk11-jre-headless
RUN apk add --no-cache libgcc libstdc++ openblas
RUN apk add --no-cache libjpeg-turbo libpng tiff
RUN apk add --no-cache gstreamer libdc1394

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
