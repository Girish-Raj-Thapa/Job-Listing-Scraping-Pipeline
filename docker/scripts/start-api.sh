#!/bin/sh
set -eu

/bin/sh /app/docker/scripts/wait-for-db.sh

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
