#!/bin/sh
set -eu

python - <<'PY'
import time

import psycopg

from app.core.config import settings


dsn = settings.database_url.replace("+psycopg", "")
attempts = 30

for attempt in range(1, attempts + 1):
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        print("Database is ready")
        break
    except Exception as exc:
        if attempt == attempts:
            raise SystemExit(f"Database not ready after {attempts} attempts: {exc}")
        print(f"Waiting for database ({attempt}/{attempts}): {exc}")
        time.sleep(2)
PY
