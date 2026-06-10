from datetime import datetime

from app.scrapers.base import BaseJobSource


class AshbySource(BaseJobSource):
    platform_name = "ashby"

    async def fetch_jobs(self) -> list[dict]:
        payload = await self._request_json()
        return payload.get("jobs", [])

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def normalize(self, raw: dict) -> dict:
        tags = [
            value
            for value in [
                raw.get("department"),
                raw.get("team"),
                raw.get("workplaceType"),
            ]
            if isinstance(value, str) and value.strip()
        ]

        remote_type = "remote" if raw.get("isRemote") else None
        if not remote_type and isinstance(raw.get("workplaceType"), str):
            remote_type = "remote" if raw["workplaceType"].lower() == "remote" else raw["workplaceType"].lower()

        return {
            "source": self.source_name,
            "external_id": raw.get("id"),
            "title": (raw.get("title") or "").strip(),
            "company": self.source_company_name or self.source_display_name,
            "location": raw.get("location"),
            "remote_type": remote_type,
            "job_type": raw.get("employmentType"),
            "tags": tags or None,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "job_url": raw.get("jobUrl") or raw.get("applyUrl"),
            "description": raw.get("descriptionPlain") or raw.get("descriptionHtml"),
            "posted_at": self._parse_datetime(raw.get("publishedAt")),
        }
