"""
ATS (Applicant Tracking System) sources.
Queries career pages of top crypto companies directly via their ATS APIs.

Supports:
- Greenhouse (public API, no auth)
- Lever (public API, no auth)
- Ashby (public API, no auth)
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

from config import (
    GREENHOUSE_BOARDS,
    LEVER_BOARDS,
    ASHBY_BOARDS,
    TITLE_KEYWORDS,
    INDUSTRY_KEYWORDS,
)

logger = logging.getLogger(__name__)

TIMEOUT = 20


def _is_marketing_role(title: str) -> bool:
    """Check if a job title is marketing-related."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in TITLE_KEYWORDS)


# ─── Greenhouse ─────────────────────────────────────────────────────

def _fetch_greenhouse(company_name: str, board_slug: str) -> list[dict]:
    """Fetch marketing jobs from a Greenhouse job board."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs?content=true"
    jobs = []

    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("jobs", []):
            title = item.get("title", "")
            if not _is_marketing_role(title):
                continue

            location = ""
            offices = item.get("offices", [])
            if offices:
                location = ", ".join(o.get("name", "") for o in offices)
            location = location or item.get("location", {}).get("name", "")

            job_url = item.get("absolute_url", "")
            content = item.get("content", "")

            jobs.append({
                "title": title,
                "company": company_name,
                "location": location,
                "salary": "",  # Greenhouse API doesn't expose salary
                "url": job_url,
                "source": f"Greenhouse/{company_name}",
                "posted_date": item.get("updated_at", ""),
                "description": content,
            })

    except Exception as e:
        logger.warning(f"  Greenhouse/{company_name}: {e}")

    return jobs


# ─── Lever ──────────────────────────────────────────────────────────

def _fetch_lever(company_name: str, board_slug: str) -> list[dict]:
    """Fetch marketing jobs from a Lever job board."""
    url = f"https://api.lever.co/v0/postings/{board_slug}?mode=json"
    jobs = []

    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        for item in data:
            title = item.get("text", "")
            if not _is_marketing_role(title):
                continue

            categories = item.get("categories", {})
            location = categories.get("location", "")
            commitment = categories.get("commitment", "")

            description = item.get("descriptionPlain", "")
            lists_text = ""
            for lst in item.get("lists", []):
                lists_text += lst.get("text", "") + " "
                lists_text += " ".join(
                    li.get("text", "") for li in lst.get("content_list", lst.get("items", []))
                )

            jobs.append({
                "title": title,
                "company": company_name,
                "location": location,
                "salary": "",
                "url": item.get("hostedUrl", item.get("applyUrl", "")),
                "source": f"Lever/{company_name}",
                "posted_date": "",
                "description": f"{description} {lists_text}".strip(),
            })

    except Exception as e:
        logger.warning(f"  Lever/{company_name}: {e}")

    return jobs


# ─── Ashby ──────────────────────────────────────────────────────────

def _fetch_ashby(company_name: str, board_slug: str) -> list[dict]:
    """Fetch marketing jobs from an Ashby job board."""
    url = f"https://api.ashby.io/posting-api/job-board/{board_slug}"
    jobs = []

    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={
            "Accept": "application/json",
        })
        resp.raise_for_status()
        data = resp.json()

        postings = data.get("jobs", [])

        for item in postings:
            title = item.get("title", "")
            if not _is_marketing_role(title):
                continue

            location = item.get("location", "")
            if isinstance(location, dict):
                location = location.get("name", "")

            job_url = item.get("jobUrl", item.get("applyUrl", ""))
            if not job_url:
                posting_id = item.get("id", "")
                if posting_id:
                    job_url = f"https://jobs.ashbyhq.com/{board_slug}/{posting_id}"

            # Try to get compensation info
            compensation = item.get("compensation", {})
            salary = ""
            if compensation:
                salary_range = compensation.get("range", {})
                if salary_range:
                    min_val = salary_range.get("min", "")
                    max_val = salary_range.get("max", "")
                    if min_val and max_val:
                        salary = f"${int(min_val):,}-${int(max_val):,}"

            jobs.append({
                "title": title,
                "company": company_name,
                "location": location if isinstance(location, str) else "",
                "salary": salary,
                "url": job_url,
                "source": f"Ashby/{company_name}",
                "posted_date": item.get("publishedDate", ""),
                "description": item.get("descriptionHtml", item.get("descriptionPlain", "")),
            })

    except Exception as e:
        logger.warning(f"  Ashby/{company_name}: {e}")

    return jobs


# ─── Combined ATS Fetcher ──────────────────────────────────────────

def fetch_all_ats() -> list[dict]:
    """Fetch from all ATS boards in parallel."""
    all_jobs = []
    tasks = []

    # Build task list
    for name, slug in GREENHOUSE_BOARDS.items():
        tasks.append(("greenhouse", name, slug))
    for name, slug in LEVER_BOARDS.items():
        tasks.append(("lever", name, slug))
    for name, slug in ASHBY_BOARDS.items():
        tasks.append(("ashby", name, slug))

    logger.info(f"  ATS: querying {len(tasks)} company career pages")

    fetcher_map = {
        "greenhouse": _fetch_greenhouse,
        "lever": _fetch_lever,
        "ashby": _fetch_ashby,
    }

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_info = {}
        for ats_type, company, slug in tasks:
            fn = fetcher_map[ats_type]
            future = executor.submit(fn, company, slug)
            future_to_info[future] = (ats_type, company)

        for future in as_completed(future_to_info):
            ats_type, company = future_to_info[future]
            try:
                jobs = future.result()
                if jobs:
                    logger.info(f"  ATS/{company}: {len(jobs)} marketing roles")
                all_jobs.extend(jobs)
            except Exception as e:
                logger.warning(f"  ATS/{company}: {e}")

    logger.info(f"  ATS total: {len(all_jobs)} marketing roles across all companies")
    return all_jobs
