from datetime import timedelta

from celery import Celery

from app.core.config import settings


celery = Celery(
    "job_scraper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.scraping"],
)

celery.conf.task_track_started = True
celery.conf.timezone = "UTC"
celery.conf.broker_connection_retry_on_startup = True
celery.conf.beat_schedule = {
    "check-due-sources-on-poll-interval": {
        "task": "app.tasks.scraping.scrape_due_sources_task",
        "schedule": timedelta(minutes=settings.beat_poll_interval_minutes),
    }
}
