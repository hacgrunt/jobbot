"""
AI-powered relevance scoring using Claude API.
Scores jobs and categorizes them for email sections.
"""

import json
import logging

import anthropic

from config import (
    ANTHROPIC_API_KEY,
    SCORING_MODEL,
    SCORING_BATCH_SIZE,
    MIN_RELEVANCE_SCORE,
    TOP_COMPANIES_SET,
)

logger = logging.getLogger(__name__)

SCORING_PROMPT = """You are evaluating job postings for a specific candidate. Here is their profile:

- Senior product marketing professional, 33, MBA
- Primary target: Product Marketing Manager (PMM) roles in crypto/web3
- Secondary target: PMM roles in AI/tech
- Tertiary: Other marketing roles (growth, brand, content, comms) at top crypto companies
- Location: NYC or Remote only
- Seniority: Mid to Senior level (not junior/entry)
- Values established, reputable companies with product-market fit
- Minimum compensation: $170k+ (but unlisted salary is fine)

For each job below, evaluate and return a JSON array. Each element must have:
- "index": the job's index number (as provided)
- "score": overall relevance score 1-10
- "category": exactly one of: "top_pick", "pmm_crypto", "pmm_ai", "other_marketing_crypto", "top_company"
- "reason": one concise sentence explaining the score

Scoring guidelines:
- 9-10: Perfect match. Senior PMM at a respected crypto/web3 company. Would be excited to apply.
- 7-8: Strong match. PMM or senior marketing at a solid crypto/AI company. Worth applying.
- 6: Decent match. Marketing role at a relevant company, but may not be ideal title/level/industry.
- 1-5: Poor match. Wrong industry, wrong level, or wrong function. Exclude.

Category definitions:
- "top_pick": Score 8-10. Best matches across any industry.
- "pmm_crypto": Score 6-7. Product marketing at a crypto/web3 company.
- "pmm_ai": Score 6-7. Product marketing at an AI/tech company (not crypto).
- "other_marketing_crypto": Score 6-7. Non-PMM marketing (growth, brand, content, comms) at a crypto company.
- "top_company": Any marketing role at one of these companies regardless of exact fit: Coinbase, Kraken, Uniswap, Hyperliquid, Anchorage, Fireblocks, Solana, ENS Labs, Circle, Tether, Aave, Consensys, Alchemy, Chainalysis, Phantom, Polygon, Arbitrum, Optimism, Paradigm, a16z.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanation outside the JSON array.

Here are the jobs to evaluate:

"""


def _build_job_summary(idx: int, job: dict) -> str:
    """Build a concise summary of a job for the scoring prompt."""
    desc = job.get("description", "")
    # Truncate description to save tokens
    if len(desc) > 500:
        desc = desc[:500] + "..."

    return (
        f"[{idx}] Title: {job['title']}\n"
        f"    Company: {job['company']}\n"
        f"    Location: {job['location']}\n"
        f"    Salary: {job['salary'] or 'Not listed'}\n"
        f"    Source: {job['source']}\n"
        f"    Description: {desc}\n"
    )


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Score and categorize jobs using Claude API."""
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set. Skipping AI scoring, using keyword-based fallback.")
        return _fallback_scoring(jobs)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    scored = []

    # Process in batches
    for batch_start in range(0, len(jobs), SCORING_BATCH_SIZE):
        batch = jobs[batch_start : batch_start + SCORING_BATCH_SIZE]
        logger.info(f"Scoring batch {batch_start // SCORING_BATCH_SIZE + 1}: {len(batch)} jobs")

        # Build prompt with job summaries
        summaries = "\n".join(
            _build_job_summary(i, job) for i, job in enumerate(batch)
        )
        prompt = SCORING_PROMPT + summaries

        try:
            response = client.messages.create(
                model=SCORING_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()

            # Try to extract JSON from the response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            scores = json.loads(content)

            for score_item in scores:
                idx = score_item.get("index", 0)
                if 0 <= idx < len(batch):
                    job = batch[idx].copy()
                    job["score"] = score_item.get("score", 0)
                    job["category"] = score_item.get("category", "other_marketing_crypto")
                    job["reason"] = score_item.get("reason", "")

                    if job["score"] >= MIN_RELEVANCE_SCORE:
                        scored.append(job)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scoring response: {e}")
            # Fallback: include all jobs in batch with default scores
            for job in batch:
                job_copy = job.copy()
                job_copy["score"] = 6
                job_copy["category"] = _guess_category(job)
                job_copy["reason"] = "AI scoring unavailable, included by keyword match"
                scored.append(job_copy)

        except Exception as e:
            logger.error(f"Scoring API call failed: {e}")
            for job in batch:
                job_copy = job.copy()
                job_copy["score"] = 6
                job_copy["category"] = _guess_category(job)
                job_copy["reason"] = "AI scoring unavailable"
                scored.append(job_copy)

    logger.info(f"Scoring complete: {len(scored)} jobs passed threshold (>= {MIN_RELEVANCE_SCORE})")
    return scored


def _guess_category(job: dict) -> str:
    """Fallback category assignment based on keywords."""
    company = job.get("company", "").lower()
    title = job.get("title", "").lower()
    desc = job.get("description", "")[:1000].lower()
    combined = f"{title} {company} {desc}"

    is_top_company = any(tc in company for tc in TOP_COMPANIES_SET)
    is_pmm = any(kw in title for kw in ["product marketing", "pmm"])
    is_crypto = any(
        kw in combined
        for kw in ["crypto", "blockchain", "web3", "defi", "digital asset"]
    )
    is_ai = any(
        kw in combined
        for kw in ["artificial intelligence", " ai ", "machine learning", "llm"]
    )

    if is_top_company:
        return "top_company"
    if is_pmm and is_crypto:
        return "pmm_crypto"
    if is_pmm and is_ai:
        return "pmm_ai"
    if is_crypto:
        return "other_marketing_crypto"
    return "pmm_ai"


def _fallback_scoring(jobs: list[dict]) -> list[dict]:
    """Score jobs without AI using simple keyword heuristics."""
    scored = []
    for job in jobs:
        job_copy = job.copy()
        job_copy["category"] = _guess_category(job)
        job_copy["reason"] = "Keyword-based match (no API key)"

        # Simple scoring
        score = 6
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()

        if any(kw in title for kw in ["product marketing", "pmm"]):
            score += 1
        if any(kw in title for kw in ["senior", "head", "director", "lead", "vp"]):
            score += 1
        if any(tc in company for tc in TOP_COMPANIES_SET):
            score += 1

        job_copy["score"] = min(score, 10)
        if job_copy["score"] >= MIN_RELEVANCE_SCORE:
            scored.append(job_copy)

    return scored
