"""
CryptoJobsList RSS feed source.
RSS: https://api.cryptojobslist.com/jobs.rss
"""

import logging
import feedparser

logger = logging.getLogger(__name__)

RSS_URL = "https://api.cryptojobslist.com/jobs.rss"


def fetch_cryptojobslist() -> list[dict]:
    jobs = []

    try:
        logger.info(f"  CryptoJobsList: fetching RSS feed")
        feed = feedparser.parse(RSS_URL)

        if feed.bozo and not feed.entries:
            logger.warning(f"  CryptoJobsList: feed parse error: {feed.bozo_exception}")
            return []

        for entry in feed.entries:
            # Extract fields from RSS entry
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            summary = entry.get("summary", entry.get("description", ""))

            # Try to extract company from title (format: "Role at Company")
            company = ""
            if " at " in title:
                parts = title.rsplit(" at ", 1)
                title = parts[0].strip()
                company = parts[1].strip()

            # Extract tags if available
            tags = [t.get("term", "") for t in entry.get("tags", [])]
            location = ""
            for tag in tags:
                if any(loc in tag.lower() for loc in ["remote", "new york", "nyc", "usa"]):
                    location = tag
                    break

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": "",  # RSS doesn't typically include salary
                "url": link,
                "source": "CryptoJobsList",
                "posted_date": published,
                "description": summary,
            })

    except Exception as e:
        logger.error(f"  CryptoJobsList failed: {e}")

    logger.info(f"  CryptoJobsList total: {len(jobs)} jobs")
    return jobs
