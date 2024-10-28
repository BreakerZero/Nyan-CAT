#!/bin/bash

# Chemin vers la base de données dans le conteneur
DATABASE_PATH="/app/database/nyan.db"
INITIAL_DATABASE="/app/initial_nyan.db"

# Vérifie si le dossier database est vide ou si nyan.db n'existe pas
if [ ! -f "$DATABASE_PATH" ]; then
    echo "Database file not found. Initializing from the container's initial database."
    cp "$INITIAL_DATABASE" "$DATABASE_PATH"
else
    echo "Existing database file found. Using the existing database."
fi

# Démarrer l'application avec gunicorn
exec /app/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
