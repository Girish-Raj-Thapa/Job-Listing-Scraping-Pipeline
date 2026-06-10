import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, NavigableString, Tag

from app.scrapers.base import BaseJobSource
from app.scrapers.exceptions import NonRetryableScrapeError


class PythonOrgSource(BaseJobSource):
    platform_name = "python_org"
    max_pages = 20

    async def fetch_jobs(self) -> list[dict]:
        jobs: list[dict] = []
        seen_job_urls: set[str] = set()

        for page_number in range(1, self.max_pages + 1):
            page_url = self._build_page_url(page_number)
            try:
                html = await self._request_text(page_url)
            except NonRetryableScrapeError as exc:
                if page_number > 1 and "HTTP 404" in str(exc):
                    break
                raise
            summaries = self._extract_summary_jobs(html)

            if not summaries:
                break

            # Stop if pagination starts repeating the same listing page.
            new_summaries = [summary for summary in summaries if summary["job_url"] not in seen_job_urls]
            if not new_summaries:
                break

            for summary in new_summaries:
                seen_job_urls.add(summary["job_url"])
                detail_url = summary["job_url"]
                detail_html = await self._request_text(detail_url)
                detail_fields = self._extract_detail_fields(detail_html)

                combined = {
                    **summary,
                    **detail_fields,
                    "title": detail_fields.get("title") or summary.get("title"),
                    "company": detail_fields.get("company") or summary.get("company"),
                    "location": detail_fields.get("location") or summary.get("location"),
                    "posted_at": detail_fields.get("posted_at") or summary.get("posted_at"),
                    "job_type": detail_fields.get("job_type") or summary.get("job_type"),
                    "tags": detail_fields.get("tags") or summary.get("tags"),
                }
                jobs.append(combined)

        return jobs

    def _build_page_url(self, page_number: int) -> str:
        if page_number == 1:
            return self.base_url

        parsed = urlsplit(self.base_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["page"] = str(page_number)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))

    def _extract_summary_jobs(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("ol.list-recent-jobs")
        if not container:
            return []

        jobs: list[dict] = []
        for item in container.find_all("li", recursive=False):
            title_link = item.select_one("h2.listing-company a[href]")
            if not title_link:
                continue

            title = title_link.get_text(strip=True)
            job_url = urljoin(self.base_url, title_link.get("href", ""))
            if not title or not job_url:
                continue

            company_block = item.select_one("span.listing-company-name")
            posted_time = item.select_one("span.listing-posted time")
            category_link = item.select_one("span.listing-company-category a")
            job_type_text = self._normalize_job_type(self._clean_text(item.select_one("span.listing-job-type")))

            tags = [category_link.get_text(strip=True)] if category_link and category_link.get_text(strip=True) else None

            jobs.append(
                {
                    "source": self.source_name,
                    "external_id": self._extract_external_id(job_url),
                    "title": title,
                    "company": self._extract_company_from_company_block(company_block),
                    "location": self._clean_text(item.select_one("span.listing-location")),
                    "remote_type": None,
                    "job_type": job_type_text,
                    "tags": tags,
                    "salary_min": None,
                    "salary_max": None,
                    "currency": None,
                    "job_url": job_url,
                    "description": None,
                    "posted_at": self._parse_datetime(posted_time.get("datetime")) if posted_time else None,
                }
            )

        return jobs

    def _extract_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        article = soup.select_one("article.text")
        if not article:
            return {}

        title, company, location = self._extract_header_fields(article)
        sections = self._extract_description_sections(article.select_one("div.job-description"))

        restrictions = sections.get("Restrictions")
        requirements = sections.get("Requirements")
        job_description = sections.get("Job Description")
        description = self._build_description(job_description, requirements, restrictions)

        posted_time = article.select_one("div.job-post-meta time")
        category_link = article.select_one("span.listing-company-category a")
        job_type_text = self._normalize_job_type(self._clean_text(article.select_one("span.listing-job-type")))
        tags = [category_link.get_text(strip=True)] if category_link and category_link.get_text(strip=True) else None

        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "posted_at": self._parse_datetime(posted_time.get("datetime")) if posted_time else None,
            "job_type": job_type_text or None,
            "tags": tags,
            "remote_type": self._derive_remote_type(restrictions),
        }

    def _extract_header_fields(self, article: Tag) -> tuple[str | None, str | None, str | None]:
        header = article.select_one("h1.listing-company")
        if not header:
            return None, None, None

        company_block = header.select_one("span.company-name") or header.select_one("span.listing-company-name")
        title_link = company_block.select_one("a[href]") if company_block else None
        title = title_link.get_text(strip=True) if title_link else None

        if not title and company_block:
            stripped_strings = [value.strip() for value in company_block.stripped_strings if value.strip()]
            title = stripped_strings[0] if stripped_strings else None

        company = self._extract_company_from_company_block(company_block)
        location = self._clean_text(header.select_one("span.listing-location"))
        return title, company, location

    def _extract_company_from_company_block(self, company_block: Tag | None) -> str | None:
        if not company_block:
            return None

        company_parts: list[str] = []
        after_break = False

        for child in company_block.children:
            if isinstance(child, Tag) and child.name == "br":
                after_break = True
                continue

            if not after_break:
                continue

            if isinstance(child, NavigableString):
                text = str(child).strip()
            elif isinstance(child, Tag):
                text = child.get_text(" ", strip=True)
            else:
                text = ""

            if text:
                company_parts.append(text)

        company = " ".join(company_parts).strip()
        if company:
            return company

        stripped_strings = [value.strip() for value in company_block.stripped_strings if value.strip()]
        if len(stripped_strings) >= 2:
            return stripped_strings[-1]
        return None

    def _extract_description_sections(self, description_block: Tag | None) -> dict[str, str]:
        if not description_block:
            return {}

        sections: dict[str, list[str]] = {}
        current_section: str | None = None

        for child in description_block.children:
            if not isinstance(child, Tag):
                continue

            if child.name == "h2":
                current_section = child.get_text(" ", strip=True)
                sections.setdefault(current_section, [])
                continue

            if not current_section:
                continue

            text = child.get_text("\n", strip=True)
            if text:
                sections[current_section].append(text)

        return {
            section: "\n\n".join(parts).strip()
            for section, parts in sections.items()
            if parts
        }

    def _build_description(
        self,
        job_description: str | None,
        requirements: str | None,
        restrictions: str | None,
    ) -> str | None:
        sections: list[str] = []

        if job_description:
            sections.append(f"Job Description\n{job_description}")
        if requirements:
            sections.append(f"Requirements\n{requirements}")
        if restrictions:
            sections.append(f"Restrictions\n{restrictions}")

        return "\n\n".join(sections).strip() or None

    def _derive_remote_type(self, restrictions: str | None) -> str | None:
        if not restrictions:
            return None

        normalized = restrictions.lower()
        if "no telecommuting" in normalized:
            return "onsite"
        if "telecommuting" in normalized or "remote" in normalized:
            return "remote"
        return None

    def _extract_external_id(self, job_url: str) -> str | None:
        match = re.search(r"/jobs/(\d+)/", job_url)
        return match.group(1) if match else None

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _clean_text(self, element: Tag | None) -> str | None:
        if not element:
            return None

        text = element.get_text(" ", strip=True)
        return text or None

    def _normalize_job_type(self, value: str | None) -> str | None:
        if not value:
            return None

        cleaned = value.strip()
        if len(cleaned) <= 100:
            return cleaned

        first_segment = cleaned.split(",", 1)[0].strip()
        if first_segment and len(first_segment) <= 100:
            return first_segment

        return cleaned[:100].rstrip()

    def normalize(self, raw: dict) -> dict:
        return {
            "source": raw.get("source", self.source_name),
            "external_id": raw.get("external_id"),
            "title": raw.get("title", "").strip(),
            "company": raw.get("company") or self.source_company_name,
            "location": raw.get("location"),
            "remote_type": raw.get("remote_type"),
            "job_type": raw.get("job_type"),
            "tags": raw.get("tags"),
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "job_url": raw.get("job_url"),
            "description": raw.get("description"),
            "posted_at": raw.get("posted_at"),
        }
