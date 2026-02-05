"""
Job filtering and deduplication.
Applies location, seniority, employment type, salary, and dedup rules.
"""

import hashlib
import logging
import re

from config import (
    ACCEPTED_LOCATIONS,
    EXCLUDED_LEVELS,
    EXCLUDED_TYPES,
    MIN_SALARY,
    TITLE_KEYWORDS,
    INDUSTRY_KEYWORDS,
)

logger = logging.getLogger(__name__)


def make_job_key(job: dict) -> str:
    """Create a dedup key from normalized title + company."""
    title = re.sub(r"[^a-z0-9 ]", "", job.get("title", "").lower()).strip()
    company = re.sub(r"[^a-z0-9 ]", "", job.get("company", "").lower()).strip()
    raw = f"{title}|{company}"
    return hashlib.md5(raw.encode()).hexdigest()


def _check_location(job: dict) -> bool:
    """Return True if job location matches accepted locations."""
    location = job.get("location", "").lower()

    # If no location specified, include it (might be remote)
    if not location or location in ("", "none", "n/a", "nan"):
        return True

    return any(loc in location for loc in ACCEPTED_LOCATIONS)


def _check_level(job: dict) -> bool:
    """Return True if job is NOT junior/entry level."""
    title = job.get("title", "").lower()
    desc_start = job.get("description", "")[:500].lower()

    for excl in EXCLUDED_LEVELS:
        if excl in title:
            return False

    # Only exclude on description if multiple signals
    desc_excl_count = sum(1 for excl in EXCLUDED_LEVELS if excl in desc_start)
    if desc_excl_count >= 2:
        return False

    return True


def _check_employment_type(job: dict) -> bool:
    """Return True if job is full-time (not contract/freelance)."""
    title = job.get("title", "").lower()
    desc_start = job.get("description", "")[:300].lower()

    for excl in EXCLUDED_TYPES:
        if excl in title:
            return False
        if excl in desc_start and "full" not in desc_start:
            return False

    return True


def _parse_salary_number(text: str) -> int | None:
    """Extract the highest salary number from a salary string."""
    if not text:
        return None

    text = text.replace(",", "").replace(" ", "")

    # Find all numbers that look like salaries
    numbers = re.findall(r"\$?(\d{3,})", text)
    if not numbers:
        return None

    values = [int(n) for n in numbers]

    # Handle hourly rates (multiply by 2080)
    if any(kw in text.lower() for kw in ["hour", "hr", "/h"]):
        values = [v * 2080 for v in values]

    # Handle monthly rates
    if "month" in text.lower():
        values = [v * 12 for v in values]

    return max(values) if values else None


def _check_salary(job: dict) -> bool:
    """Return True if salary is not listed or meets minimum."""
    salary_text = job.get("salary", "")
    if not salary_text or salary_text.strip() in ("", "nan", "None"):
        return True  # No salary listed = include

    parsed = _parse_salary_number(salary_text)
    if parsed is None:
        return True  # Can't parse = include

    return parsed >= MIN_SALARY


def _check_relevance(job: dict) -> bool:
    """Basic keyword relevance check before AI scoring."""
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    desc = job.get("description", "")[:2000].lower()

    # Must match at least one title keyword
    has_title = any(kw in title for kw in TITLE_KEYWORDS)

    # Must match at least one industry keyword (in title, company, or description)
    combined = f"{title} {company} {desc}"
    has_industry = any(kw in combined for kw in INDUSTRY_KEYWORDS)

    return has_title and has_industry


def filter_jobs(jobs: list[dict]) -> list[dict]:
    """Apply all filters and deduplicate."""
    # Step 1: Add job keys
    for job in jobs:
        job["job_key"] = make_job_key(job)

    # Step 2: Deduplicate by job_key (keep first occurrence, prefer longer description)
    by_key = {}
    for job in jobs:
        key = job["job_key"]
        if key not in by_key:
            by_key[key] = job
        else:
            # Keep the one with more information
            existing_desc_len = len(by_key[key].get("description", ""))
            new_desc_len = len(job.get("description", ""))
            if new_desc_len > existing_desc_len:
                by_key[key] = job

    deduped = list(by_key.values())
    logger.info(f"After dedup: {len(deduped)} (was {len(jobs)})")

    # Step 3: Apply filters
    filters = [
        ("location", _check_location),
        ("level", _check_level),
        ("employment_type", _check_employment_type),
        ("salary", _check_salary),
        ("relevance", _check_relevance),
    ]

    filtered = deduped
    for name, fn in filters:
        before = len(filtered)
        filtered = [j for j in filtered if fn(j)]
        dropped = before - len(filtered)
        if dropped:
            logger.info(f"  Filter '{name}': dropped {dropped}, remaining {len(filtered)}")

    logger.info(f"After all filters: {len(filtered)} jobs")
    return filtered
