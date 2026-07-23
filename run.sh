#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
exec "$DIR/.venv/bin/python3" app.py
