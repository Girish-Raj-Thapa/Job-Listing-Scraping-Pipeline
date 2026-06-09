from datetime import datetime

from pydantic import BaseModel


class ScrapeSourceRead(BaseModel):
    id: int
    name: str
    type: str
    base_url: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True