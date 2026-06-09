from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.job_listing import JobListing


def find_duplicate_job(
    db: Session,
    source: str,
    external_id: str | None,
    job_url: str,
    content_hash: str,
) -> JobListing | None:
    if external_id:
        stmt = select(JobListing).where(
            and_(JobListing.source == source, JobListing.external_id == external_id)
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

    stmt = select(JobListing).where(
        and_(JobListing.source == source, JobListing.job_url == job_url)
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        return existing

    stmt = select(JobListing).where(JobListing.content_hash == content_hash)
    return db.execute(stmt).scalar_one_or_none()