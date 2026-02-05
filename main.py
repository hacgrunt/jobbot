#!/usr/bin/env python3
"""
JobBot - Daily job alert email bot.
Fetches jobs from 30+ sources, filters, scores with AI, and emails a digest.

Usage:
    python main.py              # Full run: fetch, filter, score, email
    python main.py --dry-run    # Do everything except send the email
    python main.py --test-email # Send a test email with dummy data
"""

import argparse
import logging
import sys
from datetime import datetime

from sources import fetch_all_jobs
from filters import filter_jobs
from scorer import score_jobs
from emailer import send_email, build_email_html
from db import filter_unseen, mark_seen, cleanup_old

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run(dry_run: bool = False):
    """Main pipeline: fetch -> filter -> deduplicate -> score -> email."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("JobBot starting")
    logger.info("=" * 60)

    # Step 1: Fetch from all sources
    logger.info("\n--- Step 1: Fetching jobs from all sources ---")
    raw_jobs = fetch_all_jobs()
    logger.info(f"Raw jobs fetched: {len(raw_jobs)}")

    if not raw_jobs:
        logger.warning("No jobs fetched from any source. Check API connectivity.")
        # Still send email so user knows the bot ran
        send_email([])
        return

    # Step 2: Apply filters (location, level, type, salary, relevance keywords)
    logger.info("\n--- Step 2: Filtering jobs ---")
    filtered_jobs = filter_jobs(raw_jobs)
    logger.info(f"Jobs after filtering: {len(filtered_jobs)}")

    # Step 3: Remove previously seen jobs
    logger.info("\n--- Step 3: Deduplicating against history ---")
    new_jobs = filter_unseen(filtered_jobs)
    logger.info(f"New (unseen) jobs: {len(new_jobs)}")

    # Step 4: AI scoring and categorization
    logger.info("\n--- Step 4: AI scoring ---")
    if new_jobs:
        scored_jobs = score_jobs(new_jobs)
        logger.info(f"Jobs passing score threshold: {len(scored_jobs)}")
    else:
        scored_jobs = []
        logger.info("No new jobs to score.")

    # Step 5: Send email
    logger.info("\n--- Step 5: Sending email digest ---")
    if dry_run:
        html = build_email_html(scored_jobs)
        output_path = "/tmp/jobbot_preview.html"
        with open(output_path, "w") as f:
            f.write(html)
        logger.info(f"DRY RUN: Email preview saved to {output_path}")
        logger.info(f"Open it with: open {output_path}")
    else:
        send_email(scored_jobs)

    # Step 6: Mark jobs as seen
    if scored_jobs and not dry_run:
        mark_seen(scored_jobs)
        logger.info(f"Marked {len(scored_jobs)} jobs as seen.")

    # Step 7: Cleanup old records
    cleanup_old(days=30)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"\nJobBot finished in {elapsed:.1f}s")
    logger.info(f"Summary: {len(raw_jobs)} fetched -> {len(filtered_jobs)} filtered -> {len(new_jobs)} new -> {len(scored_jobs)} emailed")


def test_email():
    """Send a test email with dummy data to verify email setup."""
    dummy_jobs = [
        {
            "title": "Senior Product Marketing Manager",
            "company": "Coinbase",
            "location": "Remote",
            "salary": "$180,000-$220,000",
            "url": "https://example.com/job1",
            "source": "Greenhouse/Coinbase",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 9,
            "category": "top_pick",
            "reason": "Perfect match: Senior PMM at top crypto company",
            "job_key": "test1",
        },
        {
            "title": "Product Marketing Lead",
            "company": "Uniswap Labs",
            "location": "New York, NY",
            "salary": "$170,000-$200,000",
            "url": "https://example.com/job2",
            "source": "Greenhouse/Uniswap",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 8,
            "category": "top_pick",
            "reason": "Strong match: PMM Lead at top DeFi protocol",
            "job_key": "test2",
        },
        {
            "title": "Product Marketing Manager, DeFi",
            "company": "Phantom",
            "location": "Remote",
            "salary": "",
            "url": "https://example.com/job3",
            "source": "Ashby/Phantom",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 7,
            "category": "pmm_crypto",
            "reason": "Good fit: PMM at leading wallet company",
            "job_key": "test3",
        },
        {
            "title": "Growth Marketing Manager",
            "company": "Alchemy",
            "location": "New York, NY",
            "salary": "$160,000-$190,000",
            "url": "https://example.com/job4",
            "source": "Greenhouse/Alchemy",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 7,
            "category": "other_marketing_crypto",
            "reason": "Growth role at top infra company",
            "job_key": "test4",
        },
        {
            "title": "Senior PMM, AI Products",
            "company": "OpenAI",
            "location": "Remote",
            "salary": "$200,000-$280,000",
            "url": "https://example.com/job5",
            "source": "JobSpy/linkedin",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 7,
            "category": "pmm_ai",
            "reason": "Strong AI PMM role but not crypto",
            "job_key": "test5",
        },
        {
            "title": "Head of Marketing",
            "company": "Solana Labs",
            "location": "Remote",
            "salary": "",
            "url": "https://example.com/job6",
            "source": "Greenhouse/Solana",
            "posted_date": "2025-01-01",
            "description": "Test job listing",
            "score": 6,
            "category": "top_company",
            "reason": "Leadership role at top L1",
            "job_key": "test6",
        },
    ]

    logger.info("Sending test email...")
    send_email(dummy_jobs)
    logger.info("Test email sent!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobBot - Daily job alert email bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview email without sending")
    parser.add_argument("--test-email", action="store_true", help="Send test email with dummy data")
    args = parser.parse_args()

    if args.test_email:
        test_email()
    else:
        run(dry_run=args.dry_run)
