from app.scrapers.arbeitnow import ArbeitnowSource
from app.scrapers.base import BaseJobSource


def get_source_by_name(name: str) -> BaseJobSource:
    sources = {
        "arbeitnow": ArbeitnowSource,
    }

    try:
        return sources[name]()
    except KeyError as exc:
        raise ValueError(f"Unsupported source: {name}") from exc


def get_supported_sources() -> list[str]:
    return ["arbeitnow"]
    