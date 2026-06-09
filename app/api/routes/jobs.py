import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job_listing import JobListing


router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def build_jobs_query(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote: str | None = Query(default=None),
    source: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    posted_after: datetime | None = Query(default=None),
    posted_before: datetime | None = Query(default=None),
):
    stmt = select(JobListing)

    if keyword:
        stmt = stmt.where(JobListing.title.ilike(f"%{keyword}%"))
    if company:
        stmt = stmt.where(JobListing.company.ilike(f"%{company}%"))
    if location:
        stmt = stmt.where(JobListing.location.ilike(f"%{location}%"))
    if remote:
        stmt = stmt.where(JobListing.remote_type == remote)
    if source:
        stmt = stmt.where(JobListing.source == source)
    if job_type:
        stmt = stmt.where(JobListing.job_type == job_type)
    if tag:
        stmt = stmt.where(JobListing.tags.contains([tag]))
    if posted_after:
        stmt = stmt.where(JobListing.posted_at >= posted_after)
    if posted_before:
        stmt = stmt.where(JobListing.posted_at <= posted_before)

    return stmt.order_by(JobListing.created_at.desc())


@router.get("")
def list_jobs(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote: str | None = Query(default=None),
    source: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    posted_after: datetime | None = Query(default=None),
    posted_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = build_jobs_query(
        keyword=keyword,
        company=company,
        location=location,
        remote=remote,
        source=source,
        job_type=job_type,
        tag=tag,
        posted_after=posted_after,
        posted_before=posted_before,
    )
    jobs = db.execute(stmt).scalars().all()
    return jobs


def get_export_rows(jobs: list[JobListing]) -> list[list[object]]:
    return [
        [
            job.id,
            job.source,
            job.external_id,
            job.title,
            job.company,
            job.location,
            job.remote_type,
            job.job_type,
            ", ".join(job.tags or []),
            job.job_url,
            job.posted_at,
            job.created_at,
        ]
        for job in jobs
    ]


def get_export_headers() -> list[str]:
    return [
        "id",
        "source",
        "external_id",
        "title",
        "company",
        "location",
        "remote_type",
        "job_type",
        "tags",
        "job_url",
        "posted_at",
        "created_at",
    ]


@router.get("/export.csv")
def export_jobs_csv(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote: str | None = Query(default=None),
    source: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    posted_after: datetime | None = Query(default=None),
    posted_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = build_jobs_query(
        keyword=keyword,
        company=company,
        location=location,
        remote=remote,
        source=source,
        job_type=job_type,
        tag=tag,
        posted_after=posted_after,
        posted_before=posted_before,
    )
    jobs = db.execute(stmt).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(get_export_headers())
    writer.writerows(get_export_rows(jobs))

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobs.csv"},
    )


@router.get("/export.xlsx")
def export_jobs_excel(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote: str | None = Query(default=None),
    source: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    posted_after: datetime | None = Query(default=None),
    posted_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = build_jobs_query(
        keyword=keyword,
        company=company,
        location=location,
        remote=remote,
        source=source,
        job_type=job_type,
        tag=tag,
        posted_after=posted_after,
        posted_before=posted_before,
    )
    jobs = db.execute(stmt).scalars().all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Jobs"
    sheet.append(get_export_headers())

    for row in get_export_rows(jobs):
        sheet.append(row)

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=jobs.xlsx"},
    )


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(JobListing, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
