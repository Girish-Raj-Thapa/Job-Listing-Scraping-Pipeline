# Job Listing Scraping Pipeline

Job listings ingestion pipeline built with FastAPI, Celery, Redis, PostgreSQL, SQLAlchemy, Alembic, and Jinja.

It currently supports:

- multi-source job ingestion from public job APIs
- source-specific normalization into one internal schema
- Pydantic validation before insert
- multi-step deduplication
- background scraping with Celery workers
- scheduled scraping with Celery Beat plus per-source DB schedule settings
- source-specific rate limits, timeouts, and retry policy
- PostgreSQL persistence for sources, scrape runs, jobs, and errors
- JSON API endpoints
- Jinja UI for jobs, scrapes, and sources
- filtered CSV and Excel exports

## Stack

- Backend: FastAPI
- Worker: Celery
- Scheduler: Celery Beat
- Queue: Redis
- Database: PostgreSQL
- ORM: SQLAlchemy 2
- Migrations: Alembic
- Validation: Pydantic
- Scraping client: `httpx`
- UI: Jinja templates
- Containers: Docker Compose

## Current Sources

The current project uses public structured job endpoints:

- `arbeitnow`
- `greenhouse-stripe`
- `greenhouse-cloudflare`
- `lever-demo`
- `ashby-openai`
- `ashby-cursor`

Readable source metadata is stored in the database, so the app can keep stable internal source keys while showing cleaner labels such as `OpenAI (Ashby)` and `Stripe (Greenhouse)` in the UI and exports.

## Pipeline Flow

Manual trigger flow:

```text
POST /api/v1/sources/{source_name}/run
        ↓
Create scrape_jobs row with status = pending
        ↓
Queue Celery task in Redis
        ↓
Worker loads the correct source adapter
        ↓
Fetch raw jobs from external source
        ↓
Normalize into internal schema
        ↓
Validate with Pydantic
        ↓
Build content hash
        ↓
Check duplicates
        ↓
Insert only new jobs
        ↓
Update scrape_jobs totals and status
```

Scheduled flow:

```text
Celery Beat poll
        ↓
scrape_due_sources_task
        ↓
Read source schedule settings from PostgreSQL
        ↓
Decide which sources are due
        ↓
Queue scrape_source_task per due source
```

## Scheduling Model

The schedule model is intentionally split:

- Celery Beat wakes up on a fixed poll interval from config: `BEAT_POLL_INTERVAL_MINUTES`
- each source stores its own schedule rules in PostgreSQL:
  - `schedule_enabled`
  - `schedule_interval_hours`

This means scheduling behavior is effectively database-driven without needing a full custom Beat backend.

## Deduplication Strategy

Jobs are deduplicated in this order:

1. same `source + external_id`
2. same `source + job_url`
3. same `content_hash`

The content hash is built from normalized values:

```text
title + company + location + job_url
```

The normalization layer lowercases and trims these values before hashing.

## Source Runtime Controls

Each `scrape_sources` row also stores runtime controls:

- `rate_limit_seconds`
- `request_timeout_seconds`
- `max_retries`
- `retry_backoff_seconds`

Transient failures such as network issues, `429`, or `5xx` responses are treated as retryable. Terminal failures are written to `scrape_errors`.

## Database Tables

### `scrape_sources`

Stores source config and runtime behavior.

- `id`
- `name`
- `display_name`
- `company_name`
- `type`
- `base_url`
- `is_active`
- `schedule_enabled`
- `schedule_interval_hours`
- `rate_limit_seconds`
- `request_timeout_seconds`
- `max_retries`
- `retry_backoff_seconds`
- `created_at`

### `scrape_jobs`

Stores each scraping run.

- `id`
- `source_id`
- `status`
- `started_at`
- `finished_at`
- `total_found`
- `total_saved`
- `total_duplicates`
- `error_count`

### `job_listings`

Stores normalized jobs.

- `id`
- `source`
- `external_id`
- `title`
- `company`
- `location`
- `remote_type`
- `job_type`
- `tags`
- `salary_min`
- `salary_max`
- `currency`
- `job_url`
- `description`
- `posted_at`
- `content_hash`
- `created_at`
- `updated_at`

### `scrape_errors`

Stores failures during scrape execution.

- `id`
- `scrape_job_id`
- `url`
- `error_type`
- `error_message`
- `created_at`

## Project Structure

```text
app/
  api/
  core/
  db/
  models/
  schemas/
  scrapers/
  services/
  tasks/
  templates/
  static/
  web/
docker/
  Dockerfile
  scripts/
migrations/
```

## Run Locally

### 1. Start services

```bash
make up
```

### 2. Check status

```bash
make ps
make health
```

### 3. Run migrations

```bash
make upgrade
```

### 4. Inspect logs

```bash
make logs-api
make logs-worker
make logs-beat
```

## Useful Make Commands

```bash
make help
make up
make down
make restart
make ps
make logs
make logs-api
make logs-worker
make logs-beat
make shell-api
make shell-db
make revision ALEMBIC_MSG="add new field"
make upgrade
make current
make scrape-all
make scrape-due
make health
```

## API Endpoints

### Health

- `GET /health`

### Jobs

- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{id}`
- `GET /api/v1/jobs/export.csv`
- `GET /api/v1/jobs/export.xlsx`

Supported filters:

- `keyword`
- `company`
- `location`
- `remote`
- `source`
- `job_type`
- `tag`
- `posted_after`
- `posted_before`

Exports include both:

- `source_key`
- `source_name`

### Scrape Jobs

- `GET /api/v1/scrape-jobs`
- `GET /api/v1/scrape-jobs/{id}`

### Sources

- `GET /api/v1/sources`
- `POST /api/v1/sources/{source_name}/run`

## Web UI

Server-rendered pages:

- `/`
- `/jobs`
- `/scrapes`
- `/sources`

The `/jobs` page currently includes:

- 10-row pagination
- quick filter chips for common job types
- quick filter chips for common tags
- filter form for exact filtering
- filtered CSV and Excel export through one `Download` menu

The `/sources` page shows:

- source key and display name
- default company label
- schedule settings
- rate limits
- retry config
- manual run button

## Manual Verification

Use this order for a quick system check.

### 1. Infrastructure

```bash
make ps
make health
make logs-api
make logs-worker
make logs-beat
```

### 2. Source config

```bash
curl http://localhost:8001/api/v1/sources
```

Check that each source has:

- display metadata
- schedule settings
- retry config
- rate limit config

### 3. Manual source run

```bash
curl -X POST http://localhost:8001/api/v1/sources/ashby-openai/run
curl http://localhost:8001/api/v1/scrape-jobs
```

### 4. Scheduled due check

```bash
make scrape-due
```

Recently scraped sources should be skipped with `not_due_yet`.

### 5. Jobs and filters

```bash
curl "http://localhost:8001/api/v1/jobs?source=ashby-openai"
curl "http://localhost:8001/api/v1/jobs?job_type=Full-time"
curl "http://localhost:8001/api/v1/jobs?tag=Engineering"
```

### 6. Exports

```bash
curl -OJ http://localhost:8001/api/v1/jobs/export.csv
curl -OJ "http://localhost:8001/api/v1/jobs/export.xlsx?source=ashby-openai"
```

## PostgreSQL / DBeaver Access

The database is exposed on host port `5438`.

Use:

- Host: `localhost`
- Port: `5438`
- Database: `jobs_db`
- Username: `jobs_user`
- Password: `jobs_password`

## Current Status

Working now:

- Dockerized API, worker, beat, Redis, and PostgreSQL
- Alembic migration workflow
- multiple API job sources
- source-specific metadata in DB
- source-specific schedules in DB
- source-specific rate limits and retry policy in DB
- background scraping with Celery
- scheduled due-check with Celery Beat
- validation and deduplication
- job persistence
- scrape run tracking
- JSON API endpoints
- CSV and Excel export
- filtered exports
- Jinja UI with pagination and filtering

Not done yet:

- real HTML scraping
- Playwright-based browser scraping
- automated tests
- observability stack like Grafana/Loki
- richer admin/dashboard analytics

## Next Recommended Step

The strongest next technical step is adding one real website scraper:

1. one static HTML scraper with `BeautifulSoup`
2. later one dynamic scraper with `Playwright`

That would move the project from pure API ingestion into true mixed-source scraping.
