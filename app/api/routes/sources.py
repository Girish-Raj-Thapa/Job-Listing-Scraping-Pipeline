from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scrape_source import ScrapeSource
from app.services.scrape_runner import create_scrape_job
from app.tasks.scraping import scrape_source_task


router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.get("")
def list_sources(db: Session = Depends(get_db)):
    return db.query(ScrapeSource).order_by(ScrapeSource.name.asc()).all()


@router.post("/{source_name}/run")
def run_source(source_name: str, db: Session = Depends(get_db)):
    source = db.query(ScrapeSource).filter(ScrapeSource.name == source_name).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    scrape_job = create_scrape_job(db, source_name)
    task = scrape_source_task.delay(source_name, scrape_job.id)

    return {
        "message": "Scrape task queued",
        "scrape_job_id": scrape_job.id,
        "celery_task_id": task.id,
    }