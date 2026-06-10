#!/bin/sh
set -eu

role="${1:-api}"
shift || true

case "$role" in
  api)
    exec /bin/sh /app/docker/scripts/start-api.sh "$@"
    ;;
  worker)
    exec /bin/sh /app/docker/scripts/start-worker.sh "$@"
    ;;
  beat)
    exec /bin/sh /app/docker/scripts/start-beat.sh "$@"
    ;;
  *)
    exec "$role" "$@"
    ;;
esac
