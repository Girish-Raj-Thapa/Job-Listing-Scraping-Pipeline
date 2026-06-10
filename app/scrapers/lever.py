from datetime import UTC, datetime

from app.scrapers.base import BaseJobSource


class LeverSource(BaseJobSource):
    platform_name = "lever"

    async def fetch_jobs(self) -> list[dict]:
        payload = await self._request_json()
        return payload if isinstance(payload, list) else []

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            try:
                return datetime.fromtimestamp(timestamp, tz=UTC)
            except (OverflowError, OSError, ValueError):
                return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def normalize(self, raw: dict) -> dict:
        categories = raw.get("categories") or {}
        tags = [
            value
            for value in [
                categories.get("team"),
                categories.get("department"),
                categories.get("workplaceType"),
            ]
            if isinstance(value, str) and value.strip()
        ]

        description_parts = [
            raw.get("descriptionPlain"),
            raw.get("descriptionBodyPlain"),
            raw.get("additionalPlain"),
        ]
        description = "\n\n".join(part.strip() for part in description_parts if isinstance(part, str) and part.strip())

        return {
            "source": self.source_name,
            "external_id": raw.get("id"),
            "title": (raw.get("text") or "").strip(),
            "company": self.source_company_name or self.source_display_name,
            "location": categories.get("location"),
            "remote_type": "remote" if raw.get("workplaceType") == "remote" else None,
            "job_type": categories.get("commitment"),
            "tags": tags or None,
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "job_url": raw.get("hostedUrl") or raw.get("applyUrl"),
            "description": description or None,
            "posted_at": self._parse_datetime(raw.get("createdAt")),
        }
