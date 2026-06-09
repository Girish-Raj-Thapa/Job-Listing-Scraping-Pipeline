# Job Listing Scraping Pipeline

Job listings ingestion pipeline built with FastAPI, Celery, Redis, PostgreSQL, SQLAlchemy, Alembic, and Jinja.

The current MVP supports:

- scraping jobs from `Arbeitnow`
- normalizing raw source data into one internal schema
- validating jobs with Pydantic before insert
- deduplicating jobs before save
- storing scrape runs, jobs, and scrape errors in PostgreSQL
- triggering scraping in the background with Celery
- listing jobs through JSON API endpoints
- exporting jobs as CSV and Excel
- filtering jobs by keyword, source, location, remote type, job type, and tag/topic
- paginating jobs in the Jinja UI
- viewing jobs and scrape runs in a basic Jinja UI

## Stack

- Backend: FastAPI
- Worker: Celery
- Queue: Redis
- Database: PostgreSQL
- ORM: SQLAlchemy 2
- Migrations: Alembic
- Validation: Pydantic
- Scraping client: `httpx`
- UI: Jinja templates
- Containers: Docker Compose

## Current Source Support

- `arbeitnow`

Planned later:

- USAJOBS
- Adzuna
- HTML source scraping
- Playwright-based browser scraping

## How The Pipeline Works

The scraping flow is:

```text
POST /api/v1/sources/{source_name}/run
        ↓
Create scrape_jobs row with status = pending
        ↓
Queue Celery task
        ↓
Worker loads the scraper for that source
        ↓
Fetch raw jobs from external source
        ↓
Normalize each job into project schema
        ↓
Validate with Pydantic
        ↓
Build content hash
        ↓
Check duplicates
        ↓
Save new jobs
        ↓
Update scrape_jobs counters and status
```

### Step-by-step in code

1. Request hits `app/api/routes/sources.py`.
2. `create_scrape_job()` in `app/services/scrape_runner.py` creates a `scrape_jobs` row with `pending`.
3. `scrape_source_task.delay(...)` sends the task to Redis.
4. Celery worker receives the task in `app/tasks/scraping.py`.
5. Worker calls `run_scrape_for_source(...)` in `app/services/scrape_runner.py`.
6. The source adapter is loaded from `app/scrapers/registry.py`.
7. `ArbeitnowSource.fetch_jobs()` requests the remote API in `app/scrapers/arbeitnow.py`.
8. `ArbeitnowSource.normalize()` converts each raw record into the project’s internal shape.
9. `ingest_normalized_jobs(...)` in `app/services/ingestion.py` validates each job with `JobListingCreate`.
10. A content hash is generated in `app/services/dedup.py`.
11. `find_duplicate_job(...)` in `app/services/repository.py` checks if the job already exists.
12. New jobs are inserted into `job_listings`.
13. `scrape_jobs` is updated with totals for found, saved, duplicates, and errors.
14. If something fails, a row is written to `scrape_errors`.

## Deduplication Strategy

The project currently deduplicates using three checks:

1. same `source + external_id`
2. same `source + job_url`
3. same `content_hash`

The content hash is built from normalized values:

```text
title + company + location + job_url
```

Whitespace and casing are normalized before hashing.

## Database Tables

### `scrape_sources`

Stores each supported source.

- `id`
- `name`
- `type`
- `base_url`
- `is_active`
- `created_at`

### `scrape_jobs`

Stores each scrape run.

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

Stores failures during a scrape run.

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

## Local Run

### 1. Start services

```bash
make up
```

### 2. Check status

```bash
make ps
make health
```

### 3. Create migration

```bash
make revision ALEMBIC_MSG="create initial tables"
```

### 4. Apply migration

```bash
make upgrade
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
make shell-api
make shell-db
make revision ALEMBIC_MSG="add new field"
make upgrade
make current
```

## API Endpoints

### Health

- `GET /health`

### Jobs

- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{id}`
- `GET /api/v1/jobs/export.csv`
- `GET /api/v1/jobs/export.xlsx`

Supported filters on `GET /api/v1/jobs`:

- `keyword`
- `company`
- `location`
- `remote`
- `source`
- `job_type`
- `tag`
- `posted_after`
- `posted_before`

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

Use `/sources` to manually trigger a scrape from the browser.

The `/jobs` page currently includes:

- 10-row pagination
- quick filter chips for common job types
- quick filter chips for common tags/topics
- filter form for exact filtering
- a `Download` menu with CSV and Excel export

## Manual Verification Flow

Use this sequence to test the current MVP:

### 1. Confirm app is up

```bash
make up
make ps
make health
```

### 2. Confirm seeded sources

```bash
curl http://localhost:8001/api/v1/sources
```

Expected:

- one source named `arbeitnow`

### 3. Trigger a scrape

```bash
curl -X POST http://localhost:8001/api/v1/sources/arbeitnow/run
```

### 4. Watch worker logs

```bash
make logs-worker
```

### 5. Check scrape status

```bash
curl http://localhost:8001/api/v1/scrape-jobs
```

### 6. Check saved jobs

```bash
curl http://localhost:8001/api/v1/jobs
```

### 7. Test deduplication

Run the same scrape again:

```bash
curl -X POST http://localhost:8001/api/v1/sources/arbeitnow/run
```

Expected:

- `total_duplicates` should increase
- job rows should not be inserted twice

### 8. Test filtered exports

```bash
curl -OJ http://localhost:8001/api/v1/jobs/export.csv
curl -OJ "http://localhost:8001/api/v1/jobs/export.xlsx?job_type=Freelance"
```

Both export endpoints support the same filters as `GET /api/v1/jobs`.
If you export from the `/jobs` page, the active filters are preserved automatically.

## DBeaver / PostgreSQL Access

The database is exposed on host port `5438`.

Use these settings:

- Host: `localhost`
- Port: `5438`
- Database: `jobs_db`
- Username: `jobs_user`
- Password: `jobs_password`

## Important Implementation Notes

- Scrapers do not write to the database directly.
- Validation happens before database insert.
- Deduplication happens in service code before insert.
- Celery runs the scrape asynchronously so the API returns quickly.
- The API and worker both wait for PostgreSQL availability through the Docker startup scripts.
- `Arbeitnow` `created_at` currently comes as a Unix timestamp, so the scraper explicitly handles integer timestamps.

## Current Status

What is already working:

- Dockerized app, worker, Redis, and PostgreSQL
- Alembic migration workflow
- Arbeitnow scraping
- background job execution with Celery
- validation and deduplication
- job persistence
- JSON API endpoints
- CSV export route
- Excel export route
- filtered exports
- pagination in the jobs UI
- filter UI with job type and tag/topic grouping
- Jinja pages

What still needs work:

- second data source
- automated tests
- README screenshots / architecture diagram
- stronger error reporting and observability
- scheduled scraping

## Next Planned Improvements

- add USAJOBS source
- add tests with `pytest`
- improve source-specific error capture
- add pagination to jobs API
- improve export formatting
- add scheduled scraping with Celery Beat
- improve dashboard metrics
