#!/bin/sh
set -eu

/bin/sh /app/docker/scripts/wait-for-db.sh

exec celery -A app.tasks.celery.celery worker --loglevel=info
