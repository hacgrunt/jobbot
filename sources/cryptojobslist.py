"""
CryptoJobsList RSS feed source.
RSS: https://api.cryptojobslist.com/jobs.rss
"""

import logging
import re
import feedparser

logger = logging.getLogger(__name__)

RSS_URL = "https://api.cryptojobslist.com/jobs.rss"


def fetch_cryptojobslist() -> list[dict]:
    jobs = []

    try:
        logger.info("  CryptoJobsList: fetching RSS feed")
        feed = feedparser.parse(RSS_URL)

        if feed.bozo and not feed.entries:
            logger.warning(f"  CryptoJobsList: feed parse error: {feed.bozo_exception}")
            return []

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            summary = entry.get("summary", entry.get("description", ""))

            # Extract company from title (common formats):
            # "Role at Company" or "Role - Company" or "Role | Company"
            company = ""
            for separator in [" at ", " - ", " | ", " @ "]:
                if separator in title:
                    parts = title.rsplit(separator, 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                    break

            # If no company found in title, try to extract from link
            # e.g. https://cryptojobslist.com/jobs/marketing-manager-at-companyname
            if not company and link:
                match = re.search(r"-at-([^?/]+)$", link.split("?")[0])
                if match:
                    company = match.group(1).replace("-", " ").title()

            # Also try to extract from description/summary HTML
            if not company and summary:
                # Look for company name in bold or header tags
                company_match = re.search(r"<(?:strong|b|h\d)>([^<]+)</(?:strong|b|h\d)>", summary)
                if company_match:
                    company = company_match.group(1).strip()

            # Extract tags
            tags = [t.get("term", "") for t in entry.get("tags", [])]
            location = ""
            for tag in tags:
                if any(loc in tag.lower() for loc in ["remote", "new york", "nyc", "usa", "global"]):
                    location = tag
                    break

            # Skip entries with no identifiable company
            if not company:
                logger.info(f"  CryptoJobsList: skipping '{title}' - no company found")
                continue

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": "",
                "url": link,
                "source": "CryptoJobsList",
                "posted_date": published,
                "description": summary,
            })

    except Exception as e:
        logger.error(f"  CryptoJobsList failed: {e}")

    logger.info(f"  CryptoJobsList total: {len(jobs)} jobs")
    return jobs
