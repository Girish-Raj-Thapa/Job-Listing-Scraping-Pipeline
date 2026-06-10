from datetime import datetime

from pydantic import BaseModel


class ScrapeSourceRead(BaseModel):
    id: int
    name: str
    display_name: str | None
    company_name: str | None
    type: str
    base_url: str
    is_active: bool
    schedule_enabled: bool
    schedule_interval_hours: int
    rate_limit_seconds: int
    request_timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True
