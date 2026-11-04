#!/bin/sh
set -e

echo "Starting app..."
exec gosu appuser python -m app.main
