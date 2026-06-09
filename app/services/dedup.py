from hashlib import sha256


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def build_content_hash(
    title: str | None,
    company: str | None,
    location: str | None,
    job_url: str | None,
) -> str:
    hash_input = "|".join(
        [
            normalize_text(title),
            normalize_text(company),
            normalize_text(location),
            normalize_text(job_url),
        ]
    )
    return sha256(hash_input.encode("utf-8")).hexdigest()