import asyncio

from app.db.session import SessionLocal
from app.tasks.celery import celery
from app.services.scrape_runner import run_scrape_for_source


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def scrape_source_task(self, source_name: str, scrape_job_id: int) -> None:
    db = SessionLocal()
    try:
        asyncio.run(run_scrape_for_source(db, source_name, scrape_job_id))
    finally:
        db.close()