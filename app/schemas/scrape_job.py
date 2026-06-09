from datetime import datetime

from pydantic import BaseModel


class ScrapeJobRead(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_found: int
    total_saved: int
    total_duplicates: int
    error_count: int

    class Config:
        from_attributes = True