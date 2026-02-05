"""
Job filtering and deduplication.
Applies location, seniority, employment type, salary, keyword relevance,
and URL verification.
"""

import hashlib
import logging
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    ACCEPTED_LOCATIONS,
    EXCLUDED_LEVELS,
    EXCLUDED_TYPES,
    MIN_SALARY,
    TITLE_KEYWORDS,
    INDUSTRY_KEYWORDS,
    TOP_COMPANIES_SET,
)

logger = logging.getLogger(__name__)

# Strong crypto/web3 keywords that must appear in title, company, or source
# (not just buried in a job description)
STRONG_INDUSTRY_KEYWORDS = [
    "crypto", "cryptocurrency", "blockchain", "web3", "defi",
    "digital assets", "digital currency", "nft", "dao", "stablecoin",
    "tokenomics", "onchain", "on-chain", "dex", "cefi",
    "ethereum", "solana", "bitcoin",
]

# AI/tech keywords
AI_KEYWORDS = [
    "artificial intelligence", " ai ", "machine learning", "llm",
    "generative ai", "deep learning",
]


def make_job_key(job: dict) -> str:
    """Create a dedup key from normalized title + company."""
    title = re.sub(r"[^a-z0-9 ]", "", job.get("title", "").lower()).strip()
    company = re.sub(r"[^a-z0-9 ]", "", job.get("company", "").lower()).strip()
    raw = f"{title}|{company}"
    return hashlib.md5(raw.encode()).hexdigest()


def _check_location(job: dict) -> bool:
    """Return True if job location matches accepted locations."""
    location = job.get("location", "").lower()
    if not location or location in ("", "none", "n/a", "nan"):
        return True
    return any(loc in location for loc in ACCEPTED_LOCATIONS)


def _check_level(job: dict) -> bool:
    """Return True if job is NOT junior/entry level."""
    title = job.get("title", "").lower()
    for excl in EXCLUDED_LEVELS:
        if excl in title:
            return False
    desc_start = job.get("description", "")[:500].lower()
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
    numbers = re.findall(r"\$?(\d{3,})", text)
    if not numbers:
        return None
    values = [int(n) for n in numbers]
    if any(kw in text.lower() for kw in ["hour", "hr", "/h"]):
        values = [v * 2080 for v in values]
    if "month" in text.lower():
        values = [v * 12 for v in values]
    return max(values) if values else None


def _check_salary(job: dict) -> bool:
    """Return True if salary is not listed or meets minimum."""
    salary_text = job.get("salary", "")
    if not salary_text or salary_text.strip() in ("", "nan", "None"):
        return True
    parsed = _parse_salary_number(salary_text)
    if parsed is None:
        return True
    return parsed >= MIN_SALARY


def _check_relevance(job: dict) -> bool:
    """Strict relevance check: must have marketing title AND crypto/AI signal in title/company/source."""
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    source = job.get("source", "").lower()

    # Must match at least one title keyword
    has_title = any(kw in title for kw in TITLE_KEYWORDS)
    if not has_title:
        return False

    # Check if company is in our known top companies list — auto-pass industry check
    if any(tc in company for tc in TOP_COMPANIES_SET):
        return True

    # Check if the source is crypto-specific — auto-pass industry check
    crypto_sources = ["web3.career", "cryptojobslist", "remoteok", "greenhouse/", "lever/", "ashby/"]
    if any(cs in source for cs in crypto_sources):
        return True

    # For JobSpy results: require crypto/AI keyword in title OR company name (not just description)
    # This prevents random companies like "Biz2Credit" from passing just because
    # the description mentions "digital" somewhere
    title_and_company = f"{title} {company}"
    has_strong_industry = any(kw in title_and_company for kw in STRONG_INDUSTRY_KEYWORDS)
    has_ai_industry = any(kw in title_and_company for kw in AI_KEYWORDS)

    if has_strong_industry or has_ai_industry:
        return True

    # Last resort: only pass if description has overwhelming crypto signals
    # (5+ distinct keywords AND crypto appears in first 300 chars)
    desc = job.get("description", "")[:3000].lower()
    desc_start = desc[:300]
    crypto_count = sum(1 for kw in STRONG_INDUSTRY_KEYWORDS if kw in desc)
    crypto_in_opening = any(
        kw in desc_start
        for kw in ["crypto", "blockchain", "web3", "defi", "digital assets"]
    )
    if crypto_count >= 5 and crypto_in_opening:
        return True

    return False


def _check_has_company(job: dict) -> bool:
    """Reject jobs with no company name."""
    company = job.get("company", "").strip()
    if not company or company.lower() in ("", "none", "n/a", "nan", "unknown"):
        return False
    return True


def verify_urls(jobs: list[dict]) -> list[dict]:
    """Verify job URLs are reachable. Remove dead links."""
    if not jobs:
        return []

    logger.info(f"Verifying {len(jobs)} job URLs...")
    verified = []
    dead_count = 0

    def _check_url(job):
        url = job.get("url", "")
        if not url or not url.startswith("http"):
            return job, False
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True, headers={
                "User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"
            })
            return job, resp.status_code < 400
        except Exception:
            # If HEAD fails, try GET (some servers don't support HEAD)
            try:
                resp = requests.get(url, timeout=10, allow_redirects=True, stream=True, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"
                })
                resp.close()
                return job, resp.status_code < 400
            except Exception:
                return job, False

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(_check_url, job) for job in jobs]
        for future in as_completed(futures):
            job, is_valid = future.result()
            if is_valid:
                verified.append(job)
            else:
                dead_count += 1
                logger.info(f"  Dead link removed: {job.get('title', '?')} at {job.get('company', '?')}")

    if dead_count:
        logger.info(f"URL verification: {dead_count} dead links removed, {len(verified)} verified")
    return verified


def filter_jobs(jobs: list[dict]) -> list[dict]:
    """Apply all filters and deduplicate."""
    # Step 1: Add job keys
    for job in jobs:
        job["job_key"] = make_job_key(job)

    # Step 2: Deduplicate by job_key (keep longest description)
    by_key = {}
    for job in jobs:
        key = job["job_key"]
        if key not in by_key:
            by_key[key] = job
        else:
            existing_desc_len = len(by_key[key].get("description", ""))
            new_desc_len = len(job.get("description", ""))
            if new_desc_len > existing_desc_len:
                by_key[key] = job

    deduped = list(by_key.values())
    logger.info(f"After dedup: {len(deduped)} (was {len(jobs)})")

    # Step 3: Apply filters
    filters = [
        ("has_company", _check_has_company),
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
