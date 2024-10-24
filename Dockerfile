# Utiliser une image de base Ubuntu
FROM ubuntu:latest

# Définir le mainteneur
LABEL maintainer="Breaker000"

# Mettre à jour le système et installer les dépendances nécessaires
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

# Créer un répertoire de travail pour l'application
WORKDIR /app

# Créer un environnement virtuel Python
RUN python3 -m venv /app/venv

# Activer l'environnement virtuel et installer les dépendances
COPY requirements.txt requirements.txt
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt
RUN /app/venv/bin/pip install gunicorn

# Copier le reste des fichiers de l'application dans le conteneur
COPY / /app

# Exposer le port sur lequel Flask va écouter
EXPOSE 5000

# Définir la variable d'environnement pour Flask
ENV PYTHONPATH="/app"
ENV FLASK_APP=app.py
ENV FLASK_ENV=production