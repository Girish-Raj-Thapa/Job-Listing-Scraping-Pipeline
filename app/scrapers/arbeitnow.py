from datetime import UTC, datetime

from app.scrapers.base import BaseJobSource


class ArbeitnowSource(BaseJobSource):
    platform_name = "arbeitnow"

    async def fetch_jobs(self) -> list[dict]:
        payload = await self._request_json()
        return payload.get("data", [])

    def _parse_posted_at(self, value: object) -> datetime | None:
        if value is None:
            return None

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value, tz=UTC)
            except (OverflowError, OSError, ValueError):
                return None

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

        return None

    def normalize(self, raw: dict) -> dict:
        remote_flag = raw.get("remote", False)
        remote_type = "remote" if remote_flag else "onsite"
        raw_job_types = raw.get("job_types") or []
        raw_tags = raw.get("tags") or []

        job_type = None
        if isinstance(raw_job_types, list):
            for value in raw_job_types:
                if isinstance(value, str) and value.strip():
                    job_type = value.strip()
                    break
        elif isinstance(raw_job_types, str) and raw_job_types.strip():
            job_type = raw_job_types.strip()

        tags: list[str] = []
        if isinstance(raw_tags, list):
            tags = [
                value.strip()
                for value in raw_tags
                if isinstance(value, str) and value.strip()
            ]

        return {
            "source": self.source_name,
            "external_id": str(raw.get("slug")) if raw.get("slug") else None,
            "title": raw.get("title", "").strip(),
            "company": raw.get("company_name") or self.source_company_name,
            "location": raw.get("location"),
            "remote_type": remote_type,
            "job_type": job_type,
            "tags": tags or None,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "job_url": raw.get("url"),
            "description": raw.get("description"),
            "posted_at": self._parse_posted_at(raw.get("created_at")),
        }
