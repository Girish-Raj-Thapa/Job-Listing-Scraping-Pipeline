from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from app.models.job_listing import JobListing
from app.schemas.job_listing import JobListingCreate
from app.services.dedup import build_content_hash
from app.services.repository import find_duplicate_job


logger = structlog.get_logger()


@dataclass
class IngestionResult:
    total_found: int = 0
    total_saved: int = 0
    total_duplicates: int = 0
    error_count: int = 0


def ingest_normalized_jobs(db: Session, jobs: list[dict]) -> IngestionResult:
    result = IngestionResult(total_found=len(jobs))

    for raw_job in jobs:
        try:
            validated = JobListingCreate(**raw_job)
            content_hash = build_content_hash(
                title=validated.title,
                company=validated.company,
                location=validated.location,
                job_url=str(validated.job_url),
            )

            duplicate = find_duplicate_job(
                db=db,
                source=validated.source,
                external_id=validated.external_id,
                job_url=str(validated.job_url),
                content_hash=content_hash,
            )

            if duplicate:
                if duplicate.source == validated.source:
                    refreshed = False

                    if validated.job_type and duplicate.job_type != validated.job_type:
                        duplicate.job_type = validated.job_type
                        refreshed = True

                    if validated.tags and duplicate.tags != validated.tags:
                        duplicate.tags = validated.tags
                        refreshed = True

                    if refreshed:
                        db.add(duplicate)
                        db.commit()
                        logger.info(
                            "duplicate_refreshed",
                            source=duplicate.source,
                            job_id=duplicate.id,
                            title=duplicate.title,
                        )

                result.total_duplicates += 1
                logger.info(
                    "duplicate_skipped",
                    source=validated.source,
                    title=validated.title,
                    job_url=str(validated.job_url),
                )
                continue

            db_job = JobListing(
                source=validated.source,
                external_id=validated.external_id,
                title=validated.title,
                company=validated.company,
                location=validated.location,
                remote_type=validated.remote_type,
                job_type=validated.job_type,
                tags=validated.tags,
                salary_min=validated.salary_min,
                salary_max=validated.salary_max,
                currency=validated.currency,
                job_url=str(validated.job_url),
                description=validated.description,
                posted_at=validated.posted_at,
                content_hash=content_hash,
            )
            db.add(db_job)
            db.commit()
            db.refresh(db_job)

            result.total_saved += 1
            logger.info(
                "job_saved",
                source=db_job.source,
                job_id=db_job.id,
                title=db_job.title,
            )
        except Exception as exc:
            db.rollback()
            result.error_count += 1
            logger.exception("job_ingest_failed", error=str(exc), payload=raw_job)

    return result
