import asyncio
from datetime import UTC, datetime, timedelta

import structlog

from app.db.session import SessionLocal
from app.models.scrape_job import ScrapeJob, ScrapeJobStatus
from app.models.scrape_source import ScrapeSource
from app.scrapers.exceptions import RetryableScrapeError
from app.services.scrape_runner import create_scrape_job, record_scrape_failure, reset_scrape_job_for_retry
from app.tasks.celery import celery
from app.services.scrape_runner import run_scrape_for_source


logger = structlog.get_logger()


def _latest_scrape_for_source(db, source_id: int) -> ScrapeJob | None:
    return (
        db.query(ScrapeJob)
        .filter(ScrapeJob.source_id == source_id)
        .order_by(ScrapeJob.id.desc())
        .first()
    )


def _source_is_due(db, source: ScrapeSource, now: datetime) -> tuple[bool, str]:
    if not source.is_active:
        return False, "inactive"
    if not source.schedule_enabled:
        return False, "schedule_disabled"

    latest_scrape = _latest_scrape_for_source(db, source.id)
    if not latest_scrape:
        return True, "never_scraped"

    if latest_scrape.status in {ScrapeJobStatus.pending, ScrapeJobStatus.running}:
        return False, "already_running"

    reference_time = latest_scrape.finished_at or latest_scrape.started_at
    if not reference_time:
        return True, "missing_reference_time"

    due_at = reference_time.replace(tzinfo=UTC) + timedelta(hours=source.schedule_interval_hours)
    if now >= due_at:
        return True, "interval_elapsed"

    return False, "not_due_yet"


@celery.task(bind=True)
def scrape_source_task(self, source_name: str, scrape_job_id: int) -> None:
    db = SessionLocal()
    try:
        source = db.query(ScrapeSource).filter(ScrapeSource.name == source_name).first()
        if not source:
            raise ValueError(f"Source '{source_name}' not found")

        try:
            asyncio.run(run_scrape_for_source(db, source_name, scrape_job_id))
        except RetryableScrapeError as exc:
            db.rollback()
            if self.request.retries < source.max_retries:
                reset_scrape_job_for_retry(db, scrape_job_id)
                logger.warning(
                    "scrape_retry_scheduled",
                    scrape_job_id=scrape_job_id,
                    source=source_name,
                    retry_count=self.request.retries + 1,
                    max_retries=source.max_retries,
                    retry_backoff_seconds=source.retry_backoff_seconds,
                    error=str(exc),
                )
                raise self.retry(exc=exc, countdown=source.retry_backoff_seconds)

            record_scrape_failure(db, scrape_job_id, source_name, exc)
            raise
        except Exception as exc:
            db.rollback()
            record_scrape_failure(db, scrape_job_id, source_name, exc)
            raise
    finally:
        db.close()


@celery.task(name="app.tasks.scraping.scrape_all_sources_task")
def scrape_all_sources_task() -> dict[str, int]:
    db = SessionLocal()
    queued = 0
    try:
        sources = (
            db.query(ScrapeSource)
            .filter(ScrapeSource.is_active.is_(True))
            .order_by(ScrapeSource.name.asc())
            .all()
        )

        for source in sources:
            scrape_job = create_scrape_job(db, source.name)
            scrape_source_task.delay(source.name, scrape_job.id)
            queued += 1

        logger.info("scrape_all_sources_queued", queued=queued)
        return {"queued": queued}
    finally:
        db.close()


@celery.task(name="app.tasks.scraping.scrape_due_sources_task")
def scrape_due_sources_task() -> dict[str, int]:
    db = SessionLocal()
    queued = 0
    skipped = 0
    now = datetime.now(UTC)

    try:
        sources = (
            db.query(ScrapeSource)
            .filter(ScrapeSource.is_active.is_(True))
            .order_by(ScrapeSource.name.asc())
            .all()
        )

        for source in sources:
            is_due, reason = _source_is_due(db, source, now)
            if not is_due:
                skipped += 1
                logger.info(
                    "scheduled_source_skipped",
                    source=source.name,
                    reason=reason,
                    schedule_enabled=source.schedule_enabled,
                    schedule_interval_hours=source.schedule_interval_hours,
                )
                continue

            scrape_job = create_scrape_job(db, source.name)
            scrape_source_task.delay(source.name, scrape_job.id)
            queued += 1
            logger.info(
                "scheduled_source_queued",
                source=source.name,
                scrape_job_id=scrape_job.id,
                reason=reason,
                schedule_interval_hours=source.schedule_interval_hours,
            )

        logger.info("scrape_due_sources_checked", queued=queued, skipped=skipped)
        return {"queued": queued, "skipped": skipped}
    finally:
        db.close()
