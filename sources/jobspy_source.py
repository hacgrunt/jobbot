"""
JobSpy source: scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs.
"""

import logging
import time

logger = logging.getLogger(__name__)


def fetch_jobspy() -> list[dict]:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        logger.error("python-jobspy not installed, skipping JobSpy source")
        return []

    from config import JOBSPY_QUERIES

    all_jobs = []
    seen_urls = set()

    for query in JOBSPY_QUERIES:
        for site in ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google"]:
            try:
                logger.info(f"  JobSpy: {site} -> '{query}'")
                df = scrape_jobs(
                    site_name=[site],
                    search_term=query,
                    location="New York, NY",
                    results_wanted=25,
                    hours_old=48,
                    country_indeed="USA",
                    is_remote=True,
                )

                if df is None or df.empty:
                    continue

                for _, row in df.iterrows():
                    url = str(row.get("job_url", ""))
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    all_jobs.append({
                        "title": str(row.get("title", "")),
                        "company": str(row.get("company_name", row.get("company", ""))),
                        "location": str(row.get("location", "")),
                        "salary": _extract_salary(row),
                        "url": url,
                        "source": f"JobSpy/{site}",
                        "posted_date": str(row.get("date_posted", "")),
                        "description": str(row.get("description", "")),
                    })

                # Rate-limit between queries
                time.sleep(1)

            except Exception as e:
                logger.warning(f"  JobSpy {site} '{query}': {e}")
                continue

    logger.info(f"  JobSpy total: {len(all_jobs)} unique jobs")
    return all_jobs


def _extract_salary(row) -> str:
    min_sal = row.get("min_amount", None)
    max_sal = row.get("max_amount", None)
    interval = row.get("interval", "")

    if min_sal and max_sal:
        return f"${int(min_sal):,}-${int(max_sal):,} {interval}"
    elif min_sal:
        return f"${int(min_sal):,}+ {interval}"
    elif max_sal:
        return f"Up to ${int(max_sal):,} {interval}"
    return ""
