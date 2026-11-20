#!/bin/sh
set -e

echo "Applying migrations..."
gosu appuser alembic upgrade head || {
  echo "Migrations failed. Exiting..."
  exit 1
}

echo "Starting app..."
exec gosu appuser python -m app.main
