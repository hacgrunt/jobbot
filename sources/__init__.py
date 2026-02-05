"""
Job source orchestration.
Fetches from all sources and returns a unified list.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources.jobspy_source import fetch_jobspy
from sources.web3career import fetch_web3career
from sources.cryptojobslist import fetch_cryptojobslist
from sources.remoteok import fetch_remoteok
from sources.ats import fetch_all_ats

logger = logging.getLogger(__name__)

# Each fetcher returns list[dict] with keys:
#   title, company, location, salary, url, source, posted_date, description


def fetch_all_jobs() -> list[dict]:
    """Fetch jobs from all sources concurrently."""
    fetchers = {
        "JobSpy": fetch_jobspy,
        "Web3.career": fetch_web3career,
        "CryptoJobsList": fetch_cryptojobslist,
        "RemoteOK": fetch_remoteok,
        "ATS (Company Pages)": fetch_all_ats,
    }

    all_jobs = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_name = {
            executor.submit(fn): name for name, fn in fetchers.items()
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                jobs = future.result()
                logger.info(f"[{name}] fetched {len(jobs)} jobs")
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"[{name}] FAILED: {e}")

    logger.info(f"Total raw jobs from all sources: {len(all_jobs)}")
    return all_jobs
