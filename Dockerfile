# ---------- builder ----------
FROM python:3.13-slim-bookworm AS builder

LABEL maintainer="Breaker000"
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl unzip git build-essential gfortran \
    libopenblas-dev liblapack-dev \
    libjpeg62-turbo-dev libpng-dev libtiff-dev \
    ffmpeg openjdk-17-jre-headless \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --venv /opt/venv

# ---------- runtime ----------
FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl unzip git coreutils ffmpeg openjdk-17-jre-headless \
    libopenblas0 libjpeg62-turbo libpng16-16 libtiff6 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY . /app

RUN chmod +x /app/init_database.sh

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000 8081

CMD ["/app/init_database.sh"]
