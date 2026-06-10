import asyncio

import httpx
import structlog

from app.models.scrape_source import ScrapeSource
from app.scrapers.exceptions import NonRetryableScrapeError, RetryableScrapeError


logger = structlog.get_logger()


class BaseJobSource:
    platform_name: str

    def __init__(self, source: ScrapeSource):
        self.source = source

    @property
    def source_name(self) -> str:
        return self.source.name

    @property
    def source_display_name(self) -> str:
        return self.source.display_name or self.source.name

    @property
    def source_company_name(self) -> str | None:
        return self.source.company_name

    @property
    def base_url(self) -> str:
        return self.source.base_url

    @property
    def rate_limit_seconds(self) -> int:
        return max(0, self.source.rate_limit_seconds)

    @property
    def request_timeout_seconds(self) -> int:
        return max(1, self.source.request_timeout_seconds)

    async def _request_json(self, url: str | None = None) -> dict | list:
        request_url = url or self.base_url

        if self.rate_limit_seconds:
            logger.info(
                "source_rate_limit_wait",
                source=self.source_name,
                delay_seconds=self.rate_limit_seconds,
            )
            await asyncio.sleep(self.rate_limit_seconds)

        try:
            async with httpx.AsyncClient(
                timeout=self.request_timeout_seconds,
                follow_redirects=True,
            ) as client:
                response = await client.get(request_url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 429 or status_code >= 500:
                raise RetryableScrapeError(
                    f"{self.source_name} returned retryable HTTP {status_code}"
                ) from exc
            raise NonRetryableScrapeError(
                f"{self.source_name} returned HTTP {status_code}"
            ) from exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            raise RetryableScrapeError(
                f"{self.source_name} request failed: {type(exc).__name__}"
            ) from exc
        except ValueError as exc:
            raise NonRetryableScrapeError(
                f"{self.source_name} returned invalid JSON"
            ) from exc

    async def fetch_jobs(self) -> list[dict]:
        raise NotImplementedError

    def normalize(self, raw: dict) -> dict:
        raise NotImplementedError

    async def collect(self) -> list[dict]:
        raw_jobs = await self.fetch_jobs()
        return [self.normalize(item) for item in raw_jobs]
