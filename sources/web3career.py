"""
Web3.career API source.
Free API: https://web3.career/web3-jobs-api
"""

import logging
import requests

logger = logging.getLogger(__name__)

API_URL = "https://web3.career/api/v1"


def fetch_web3career() -> list[dict]:
    jobs = []

    # Fetch marketing-specific endpoint and general search
    endpoints = [
        f"{API_URL}?tag=marketing",
        f"{API_URL}?tag=growth",
        f"{API_URL}?tag=community",
    ]

    seen_urls = set()

    for url in endpoints:
        try:
            logger.info(f"  Web3.career: {url}")
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "JobBot/1.0 (personal job search tool)"
            })
            resp.raise_for_status()
            data = resp.json()

            # API may return list directly or nested under a key
            listings = data if isinstance(data, list) else data.get("jobs", data.get("data", []))

            for item in listings:
                job_url = item.get("url", item.get("apply_url", ""))
                if not job_url:
                    continue
                # Ensure absolute URL
                if job_url.startswith("/"):
                    job_url = f"https://web3.career{job_url}"
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                jobs.append({
                    "title": item.get("title", item.get("position", "")),
                    "company": item.get("company", item.get("company_name", "")),
                    "location": item.get("location", ""),
                    "salary": item.get("salary", item.get("compensation", "")),
                    "url": job_url,
                    "source": "Web3.career",
                    "posted_date": item.get("date", item.get("created_at", "")),
                    "description": item.get("description", item.get("details", "")),
                })

        except Exception as e:
            logger.warning(f"  Web3.career endpoint failed: {e}")
            continue

    logger.info(f"  Web3.career total: {len(jobs)} jobs")
    return jobs
