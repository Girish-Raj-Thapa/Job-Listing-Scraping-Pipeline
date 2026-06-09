from sqlalchemy.orm import Session

from app.models.scrape_source import ScrapeSource, SourceType


def seed_sources(db: Session) -> None:
    defaults = [
        {
            "name": "arbeitnow",
            "type": SourceType.api,
            "base_url": "https://www.arbeitnow.com/api/job-board-api",
            "is_active": True,
        },
    ]

    for item in defaults:
        exists = db.query(ScrapeSource).filter(ScrapeSource.name == item["name"]).first()
        if not exists:
            db.add(ScrapeSource(**item))

    db.commit()