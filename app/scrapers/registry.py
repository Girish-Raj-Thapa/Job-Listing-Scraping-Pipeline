from app.models.scrape_source import ScrapeSource
from app.scrapers.ashby import AshbySource
from app.scrapers.arbeitnow import ArbeitnowSource
from app.scrapers.base import BaseJobSource
from app.scrapers.greenhouse import GreenhouseSource
from app.scrapers.lever import LeverSource
from app.scrapers.python_org import PythonOrgSource


def get_source_for_record(source: ScrapeSource) -> BaseJobSource:
    url = source.base_url.lower()

    if "arbeitnow.com" in url:
        return ArbeitnowSource(source)
    if "boards-api.greenhouse.io" in url:
        return GreenhouseSource(source)
    if "api.lever.co" in url:
        return LeverSource(source)
    if "api.ashbyhq.com" in url:
        return AshbySource(source)
    if "python.org/jobs" in url:
        return PythonOrgSource(source)

    raise ValueError(f"Unsupported source: {source.name}")
