from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scrape_job import ScrapeJob


router = APIRouter(prefix="/api/v1/scrape-jobs", tags=["scrape-jobs"])


@router.get("")
def list_scrape_jobs(db: Session = Depends(get_db)):
    return db.query(ScrapeJob).order_by(ScrapeJob.id.desc()).all()


@router.get("/{scrape_job_id}")
def get_scrape_job(scrape_job_id: int, db: Session = Depends(get_db)):
    scrape_job = db.get(ScrapeJob, scrape_job_id)
    if not scrape_job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return scrape_job