#!/bin/bash
set -euo pipefail

DATABASE_PATH="/app/database/nyan.db"
INITIAL_DATABASE="/app/initial_nyan.db"

mkdir -p "$(dirname "$DATABASE_PATH")"

if [ ! -f "$DATABASE_PATH" ]; then
    echo "Database file not found. Initializing from the container's initial database."
    cp "$INITIAL_DATABASE" "$DATABASE_PATH"
else
    echo "Existing database file found. Using the existing database."
fi

exec /opt/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 app:app