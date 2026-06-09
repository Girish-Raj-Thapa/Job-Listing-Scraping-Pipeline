from datetime import datetime

import structlog
from sqlalchemy.orm import Session

from app.models.scrape_error import ScrapeError
from app.models.scrape_job import ScrapeJob, ScrapeJobStatus
from app.models.scrape_source import ScrapeSource
from app.scrapers.registry import get_source_by_name
from app.services.ingestion import ingest_normalized_jobs


logger = structlog.get_logger()


async def run_scrape_for_source(db: Session, source_name: str, scrape_job_id: int) -> ScrapeJob:
    scrape_job = db.get(ScrapeJob, scrape_job_id)
    if not scrape_job:
        raise ValueError(f"Scrape job {scrape_job_id} not found")

    scrape_job.status = ScrapeJobStatus.running
    scrape_job.started_at = datetime.utcnow()
    db.commit()

    logger.info("scrape_started", scrape_job_id=scrape_job_id, source=source_name)

    try:
        source = get_source_by_name(source_name)
        normalized_jobs = await source.collect()
        result = ingest_normalized_jobs(db, normalized_jobs)

        scrape_job.status = ScrapeJobStatus.success
        scrape_job.finished_at = datetime.utcnow()
        scrape_job.total_found = result.total_found
        scrape_job.total_saved = result.total_saved
        scrape_job.total_duplicates = result.total_duplicates
        scrape_job.error_count = result.error_count
        db.commit()

        logger.info(
            "scrape_completed",
            scrape_job_id=scrape_job_id,
            source=source_name,
            total_found=result.total_found,
            total_saved=result.total_saved,
            duplicates=result.total_duplicates,
            error_count=result.error_count,
        )
        return scrape_job
    except Exception as exc:
        db.rollback()

        scrape_job = db.get(ScrapeJob, scrape_job_id)
        scrape_job.status = ScrapeJobStatus.failed
        scrape_job.finished_at = datetime.utcnow()
        scrape_job.error_count += 1
        db.add(
            ScrapeError(
                scrape_job_id=scrape_job_id,
                url=None,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        )
        db.commit()

        logger.exception("scrape_failed", scrape_job_id=scrape_job_id, source=source_name)
        raise


def create_scrape_job(db: Session, source_name: str) -> ScrapeJob:
    source = db.query(ScrapeSource).filter(ScrapeSource.name == source_name).first()
    if not source:
        raise ValueError(f"Source '{source_name}' not found in database")

    scrape_job = ScrapeJob(source_id=source.id, status=ScrapeJobStatus.pending)
    db.add(scrape_job)
    db.commit()
    db.refresh(scrape_job)
    return scrape_job