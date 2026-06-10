from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job_listing import JobListing
from app.models.scrape_job import ScrapeJob
from app.models.scrape_source import ScrapeSource
from app.services.scrape_runner import create_scrape_job
from app.tasks.scraping import scrape_source_task


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    jobs_count = db.query(JobListing).count()
    sources = db.query(ScrapeSource).order_by(ScrapeSource.name.asc()).all()
    recent_scrapes = db.query(ScrapeJob).order_by(ScrapeJob.id.desc()).limit(10).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "jobs_count": jobs_count,
            "sources": sources,
            "recent_scrapes": recent_scrapes,
        },
    )


@router.get("/jobs", response_class=HTMLResponse)
def jobs_page(
    request: Request,
    page: int = Query(default=1, ge=1),
    keyword: str | None = Query(default=None),
    location: str | None = Query(default=None),
    remote: str | None = Query(default=None),
    source: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    page_size = 10

    filter_values = {
        "keyword": keyword or "",
        "location": location or "",
        "remote": remote or "",
        "source": source or "",
        "job_type": job_type or "",
        "tag": tag or "",
    }

    stmt = select(JobListing)
    count_stmt = select(func.count()).select_from(JobListing)

    if keyword:
        stmt = stmt.where(JobListing.title.ilike(f"%{keyword}%"))
        count_stmt = count_stmt.where(JobListing.title.ilike(f"%{keyword}%"))
    if location:
        stmt = stmt.where(JobListing.location.ilike(f"%{location}%"))
        count_stmt = count_stmt.where(JobListing.location.ilike(f"%{location}%"))
    if remote:
        stmt = stmt.where(JobListing.remote_type == remote)
        count_stmt = count_stmt.where(JobListing.remote_type == remote)
    if source:
        stmt = stmt.where(JobListing.source == source)
        count_stmt = count_stmt.where(JobListing.source == source)
    if job_type:
        stmt = stmt.where(JobListing.job_type == job_type)
        count_stmt = count_stmt.where(JobListing.job_type == job_type)
    if tag:
        stmt = stmt.where(JobListing.tags.contains([tag]))
        count_stmt = count_stmt.where(JobListing.tags.contains([tag]))

    total_jobs = db.scalar(count_stmt) or 0
    total_pages = max(1, (total_jobs + page_size - 1) // page_size)
    current_page = min(page, total_pages)
    offset = (current_page - 1) * page_size

    jobs = (
        db.execute(
            stmt
            .order_by(JobListing.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    start_row = offset + 1 if total_jobs else 0
    end_row = min(offset + len(jobs), total_jobs)

    sources = db.query(ScrapeSource).order_by(ScrapeSource.name.asc()).all()
    source_options = [
        {
            "value": item.name,
            "label": item.display_name or item.name,
        }
        for item in sources
    ]
    source_label_map = {item.name: item.display_name or item.name for item in sources}
    remote_options = ["onsite", "remote"]
    job_type_options = db.execute(
        select(JobListing.job_type)
        .where(JobListing.job_type.is_not(None))
        .distinct()
        .order_by(JobListing.job_type.asc())
    ).scalars().all()
    tag_options = db.execute(
        text(
            """
            SELECT tag
            FROM (
                SELECT DISTINCT unnest(tags) AS tag
                FROM job_listings
                WHERE tags IS NOT NULL
            ) AS distinct_tags
            ORDER BY tag ASC
            LIMIT 30
            """
        )
    ).scalars().all()

    base_query = {
        key: value
        for key, value in filter_values.items()
        if value
    }

    def build_jobs_url(**updates: str | None) -> str:
        params = dict(base_query)
        for key, value in updates.items():
            if value:
                params[key] = value
            else:
                params.pop(key, None)

        if current_page > 1 and "page" not in updates:
            params["page"] = str(current_page)

        query_string = urlencode(params)
        return f"/jobs?{query_string}" if query_string else "/jobs"

    job_type_chips = [
        {
            "label": option,
            "active": filter_values["job_type"] == option,
            "url": build_jobs_url(job_type=None if filter_values["job_type"] == option else option, page=None),
        }
        for option in job_type_options[:12]
    ]
    tag_chips = [
        {
            "label": option,
            "active": filter_values["tag"] == option,
            "url": build_jobs_url(tag=None if filter_values["tag"] == option else option, page=None),
        }
        for option in tag_options[:18]
    ]

    prev_url = None
    if current_page > 1:
        prev_params = base_query | {"page": current_page - 1}
        prev_url = f"/jobs?{urlencode(prev_params)}"

    next_url = None
    if current_page < total_pages:
        next_params = base_query | {"page": current_page + 1}
        next_url = f"/jobs?{urlencode(next_params)}"

    export_query = urlencode(base_query)
    export_csv_url = "/api/v1/jobs/export.csv"
    export_xlsx_url = "/api/v1/jobs/export.xlsx"
    if export_query:
        export_csv_url = f"{export_csv_url}?{export_query}"
        export_xlsx_url = f"{export_xlsx_url}?{export_query}"

    return templates.TemplateResponse(
        "jobs/list.html",
        {
            "request": request,
            "jobs": jobs,
            "source_label_map": source_label_map,
            "current_page": current_page,
            "total_pages": total_pages,
            "page_size": page_size,
            "total_jobs": total_jobs,
            "start_row": start_row,
            "end_row": end_row,
            "has_prev": current_page > 1,
            "has_next": current_page < total_pages,
            "prev_url": prev_url,
            "next_url": next_url,
            "filter_values": filter_values,
            "source_options": source_options,
            "remote_options": remote_options,
            "job_type_options": job_type_options,
            "tag_options": tag_options,
            "job_type_chips": job_type_chips,
            "tag_chips": tag_chips,
            "export_csv_url": export_csv_url,
            "export_xlsx_url": export_xlsx_url,
        },
    )


@router.get("/scrapes", response_class=HTMLResponse)
def scrapes_page(request: Request, db: Session = Depends(get_db)):
    scrapes = db.query(ScrapeJob).order_by(ScrapeJob.id.desc()).limit(100).all()
    return templates.TemplateResponse(
        "scrapes/list.html",
        {"request": request, "scrapes": scrapes},
    )


@router.get("/sources", response_class=HTMLResponse)
def sources_page(request: Request, db: Session = Depends(get_db)):
    sources = db.query(ScrapeSource).order_by(ScrapeSource.name.asc()).all()
    return templates.TemplateResponse(
        "sources/list.html",
        {"request": request, "sources": sources},
    )


@router.post("/sources/{source_name}/run")
def run_source_from_ui(source_name: str, db: Session = Depends(get_db)):
    scrape_job = create_scrape_job(db, source_name)
    scrape_source_task.delay(source_name, scrape_job.id)
    return RedirectResponse(url="/sources", status_code=303)
