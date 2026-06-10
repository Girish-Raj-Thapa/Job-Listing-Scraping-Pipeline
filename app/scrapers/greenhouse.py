from datetime import datetime

from app.scrapers.base import BaseJobSource


class GreenhouseSource(BaseJobSource):
    platform_name = "greenhouse"

    async def fetch_jobs(self) -> list[dict]:
        payload = await self._request_json()
        return payload.get("jobs", [])

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def normalize(self, raw: dict) -> dict:
        departments = [
            item.get("name", "").strip()
            for item in raw.get("departments", [])
            if isinstance(item, dict) and item.get("name")
        ]
        offices = [
            item.get("name", "").strip()
            for item in raw.get("offices", [])
            if isinstance(item, dict) and item.get("name")
        ]
        tags = [value for value in departments + offices if value]

        return {
            "source": self.source_name,
            "external_id": str(raw.get("id")) if raw.get("id") else None,
            "title": (raw.get("title") or "").strip(),
            "company": raw.get("company_name") or self.source_company_name,
            "location": (raw.get("location") or {}).get("name"),
            "remote_type": None,
            "job_type": None,
            "tags": tags or None,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "job_url": raw.get("absolute_url"),
            "description": raw.get("content"),
            "posted_at": self._parse_datetime(raw.get("updated_at") or raw.get("first_published")),
        }
