"""
RemoteOK JSON API source.
API: https://remoteok.com/api
"""

import logging
import requests

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"


def fetch_remoteok() -> list[dict]:
    jobs = []

    try:
        logger.info("  RemoteOK: fetching API")
        resp = requests.get(
            API_URL,
            timeout=30,
            headers={
                "User-Agent": "JobBot/1.0 (personal job search tool)",
                "Accept": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        # First item is metadata, skip it
        listings = data[1:] if len(data) > 1 else []

        for item in listings:
            # Filter for marketing/crypto related tags
            tags = [t.lower() for t in item.get("tags", [])]
            position = item.get("position", "").lower()
            company = item.get("company", "").lower()
            description = item.get("description", "").lower()

            # Check if this job is relevant (marketing + crypto/web3/AI)
            has_marketing = any(
                kw in position or kw in " ".join(tags)
                for kw in ["marketing", "growth", "pmm", "brand", "gtm", "communications"]
            )
            has_industry = any(
                kw in position or kw in " ".join(tags) or kw in company or kw in description
                for kw in [
                    "crypto", "blockchain", "web3", "defi", "bitcoin",
                    "ethereum", "token", "nft", "dao", "digital asset",
                    "ai", "artificial intelligence", "machine learning",
                ]
            )

            if not (has_marketing or has_industry):
                continue

            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = f"https://remoteok.com{url}"

            salary_min = item.get("salary_min", "")
            salary_max = item.get("salary_max", "")
            salary = ""
            if salary_min and salary_max:
                salary = f"${int(salary_min):,}-${int(salary_max):,}"
            elif salary_min:
                salary = f"${int(salary_min):,}+"

            jobs.append({
                "title": item.get("position", ""),
                "company": item.get("company", ""),
                "location": item.get("location", "Remote"),
                "salary": salary,
                "url": url,
                "source": "RemoteOK",
                "posted_date": item.get("date", ""),
                "description": item.get("description", ""),
            })

    except Exception as e:
        logger.error(f"  RemoteOK failed: {e}")

    logger.info(f"  RemoteOK total: {len(jobs)} jobs")
    return jobs
