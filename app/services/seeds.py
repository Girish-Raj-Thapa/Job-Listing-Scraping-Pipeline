from sqlalchemy.orm import Session

from app.models.scrape_source import ScrapeSource, SourceType


def seed_sources(db: Session) -> None:
    defaults = [
        {
            "name": "arbeitnow",
            "display_name": "Arbeitnow",
            "company_name": None,
            "type": SourceType.api,
            "base_url": "https://www.arbeitnow.com/api/job-board-api",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 6,
            "rate_limit_seconds": 1,
            "request_timeout_seconds": 30,
            "max_retries": 3,
            "retry_backoff_seconds": 15,
        },
        {
            "name": "greenhouse-stripe",
            "display_name": "Stripe (Greenhouse)",
            "company_name": "Stripe",
            "type": SourceType.api,
            "base_url": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 6,
            "rate_limit_seconds": 1,
            "request_timeout_seconds": 30,
            "max_retries": 3,
            "retry_backoff_seconds": 15,
        },
        {
            "name": "greenhouse-cloudflare",
            "display_name": "Cloudflare (Greenhouse)",
            "company_name": "Cloudflare",
            "type": SourceType.api,
            "base_url": "https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs?content=true",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 6,
            "rate_limit_seconds": 1,
            "request_timeout_seconds": 30,
            "max_retries": 3,
            "retry_backoff_seconds": 15,
        },
        {
            "name": "lever-demo",
            "display_name": "Lever Demo",
            "company_name": "Lever Demo",
            "type": SourceType.api,
            "base_url": "https://api.lever.co/v0/postings/leverdemo?mode=json",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 12,
            "rate_limit_seconds": 2,
            "request_timeout_seconds": 30,
            "max_retries": 4,
            "retry_backoff_seconds": 20,
        },
        {
            "name": "ashby-openai",
            "display_name": "OpenAI (Ashby)",
            "company_name": "OpenAI",
            "type": SourceType.api,
            "base_url": "https://api.ashbyhq.com/posting-api/job-board/openai",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 6,
            "rate_limit_seconds": 1,
            "request_timeout_seconds": 30,
            "max_retries": 3,
            "retry_backoff_seconds": 15,
        },
        {
            "name": "ashby-cursor",
            "display_name": "Cursor (Ashby)",
            "company_name": "Cursor",
            "type": SourceType.api,
            "base_url": "https://api.ashbyhq.com/posting-api/job-board/cursor",
            "is_active": True,
            "schedule_enabled": True,
            "schedule_interval_hours": 6,
            "rate_limit_seconds": 1,
            "request_timeout_seconds": 30,
            "max_retries": 3,
            "retry_backoff_seconds": 15,
        },
    ]

    for item in defaults:
        exists = db.query(ScrapeSource).filter(ScrapeSource.name == item["name"]).first()
        if exists:
            for key, value in item.items():
                if getattr(exists, key) != value:
                    setattr(exists, key, value)
        else:
            db.add(ScrapeSource(**item))

    db.commit()
