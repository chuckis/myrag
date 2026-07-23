#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
if [ "$1" = "--web" ]; then
    MYRAG_WEB=1 exec "$DIR/.venv/bin/python3" app.py
else
    exec "$DIR/.venv/bin/python3" app.py
fi
