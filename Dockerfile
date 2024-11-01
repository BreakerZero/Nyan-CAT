FROM python:3.11.10-alpine3.20

LABEL maintainer="Breaker000"

# Installer les dépendances système et pipx
RUN apk update && apk add --no-cache \
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

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances dans le conteneur
COPY requirements.txt requirements.txt

# Télécharger et configurer LanguageTool
RUN curl -L -o languagetool.zip https://languagetool.org/download/LanguageTool-stable.zip && \
    unzip languagetool.zip -d /app/languagetool && \
    rm languagetool.zip

# Utiliser pipx pour installer des outils et des dépendances globales
RUN pipx install --python python3 gunicorn \
    && pipx inject gunicorn  -r requirements.txt

# Copier le code de l'application dans le conteneur
COPY / /app

# Rendre le script init_database exécutable
RUN chmod +x /app/init_database.sh
# Exposer les ports pour Flask (5000) et LanguageTool (8081)
EXPOSE 5000 8081

# Définir les variables d'environnement pour Flask
ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Lancer LanguageTool et Flask en parallèle
CMD java -cp /app/languagetool/LanguageTool-*/languagetool-server.jar org.languagetool.server.HTTPServer --port 8081 --allow-origin & \
    /app/init_database.sh