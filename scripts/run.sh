#!/bin/sh

# tells the bash shell to exit immediately if any subsequent commands returns a non-zero (error) exit status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting server..."
gunicorn --bind 0.0.0.0 --workers 4 data_backend.wsgi:application