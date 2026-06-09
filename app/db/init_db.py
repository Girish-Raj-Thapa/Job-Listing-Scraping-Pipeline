from app.db.base import Base
from app.db.session import engine
from app.models import job_listing, scrape_error, scrape_job, scrape_source


def init_db() -> None:
    Base.metadata.create_all(bind=engine)