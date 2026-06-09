from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, HttpUrl


class JobListingCreate(BaseModel):
    source: str
    external_id: str | None = None
    title: str
    company: str | None = None
    location: str | None = None
    remote_type: str | None = None
    job_type: str | None = None
    tags: list[str] | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    job_url: HttpUrl
    description: str | None = None
    posted_at: datetime | None = None


class JobListingRead(BaseModel):
    id: int
    source: str
    external_id: str | None = None
    title: str
    company: str | None = None
    location: str | None = None
    remote_type: str | None = None
    job_type: str | None = None
    tags: list[str] | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    job_url: str
    description: str | None = None
    posted_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
