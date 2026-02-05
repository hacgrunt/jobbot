"""
AI-powered relevance scoring using Claude API.
Scores jobs and categorizes them for email sections.
"""

import json
import logging
import re

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
- "summary": one sentence like "Senior PMM role at leading DEX protocol" or "Growth marketing at unknown crypto startup — verify company"
- "reason": one concise sentence explaining the score

Scoring guidelines:
- 9-10: Perfect match. Senior PMM at a respected crypto/web3 company. Would be excited to apply.
- 7-8: Strong match. PMM or senior marketing at a solid crypto/AI company. Worth applying.
- 6: Decent match. Marketing role at a relevant company, but may not be ideal title/level/industry.
- 1-5: Poor match. Wrong industry, wrong level, or wrong function. Exclude.

BE STRICT. Unknown or obscure companies should score lower (max 6) unless the role is exceptional.
Companies like "Glint Tech Solutions", "Biz2Credit", or generic staffing agencies should score 1-3.
Only established crypto/web3/AI companies or well-known tech companies should score 7+.

Category definitions:
- "top_pick": Score 8-10. Best matches across any industry.
- "pmm_crypto": Score 6-7. Product marketing at a crypto/web3 company.
- "pmm_ai": Score 6-7. Product marketing at an AI/tech company (not crypto).
- "other_marketing_crypto": Score 6-7. Non-PMM marketing (growth, brand, content, comms) at a crypto company.
- "top_company": Any marketing role at one of these companies regardless of exact fit: Coinbase, Kraken, Uniswap, Hyperliquid, Anchorage, Fireblocks, Solana, ENS Labs, Circle, Tether, Aave, Consensys, Alchemy, Chainalysis, Phantom, Polygon, Arbitrum, Optimism, Paradigm, a16z.

IMPORTANT: Return ONLY a valid JSON array. No markdown fences, no explanation, just the raw JSON.

Here are the jobs to evaluate:

"""


def _build_job_summary(idx: int, job: dict) -> str:
    """Build a concise summary of a job for the scoring prompt."""
    desc = job.get("description", "")
    # Strip HTML tags for cleaner input
    desc = re.sub(r"<[^>]+>", " ", desc)
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) > 600:
        desc = desc[:600] + "..."

    return (
        f"[{idx}] Title: {job['title']}\n"
        f"    Company: {job['company'] or 'UNKNOWN'}\n"
        f"    Location: {job['location'] or 'Not specified'}\n"
        f"    Salary: {job['salary'] or 'Not listed'}\n"
        f"    Source: {job['source']}\n"
        f"    Description: {desc}\n"
    )


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Score and categorize jobs using Claude API."""
    if not ANTHROPIC_API_KEY:
        logger.warning("No ANTHROPIC_API_KEY set, using keyword-based fallback.")
        return _fallback_scoring(jobs)

    logger.info(f"ANTHROPIC_API_KEY is set (starts with {ANTHROPIC_API_KEY[:10]}...)")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    scored = []

    # Process in batches
    for batch_start in range(0, len(jobs), SCORING_BATCH_SIZE):
        batch = jobs[batch_start : batch_start + SCORING_BATCH_SIZE]
        batch_num = batch_start // SCORING_BATCH_SIZE + 1
        logger.info(f"Scoring batch {batch_num}: {len(batch)} jobs")

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
            logger.info(f"API response length: {len(content)} chars")

            # Extract JSON from response (handle markdown fences)
            json_content = content
            if "```" in json_content:
                # Find content between fences
                match = re.search(r"```(?:json)?\s*\n?(.*?)```", json_content, re.DOTALL)
                if match:
                    json_content = match.group(1).strip()

            # Find the JSON array
            bracket_start = json_content.find("[")
            bracket_end = json_content.rfind("]")
            if bracket_start != -1 and bracket_end != -1:
                json_content = json_content[bracket_start : bracket_end + 1]

            scores = json.loads(json_content)
            logger.info(f"Parsed {len(scores)} score entries from API")

            for score_item in scores:
                idx = score_item.get("index", 0)
                if 0 <= idx < len(batch):
                    job = batch[idx].copy()
                    job["score"] = score_item.get("score", 0)
                    job["category"] = score_item.get("category", "other_marketing_crypto")
                    job["reason"] = score_item.get("reason", "")
                    job["summary"] = score_item.get("summary", "")

                    if job["score"] >= MIN_RELEVANCE_SCORE:
                        scored.append(job)
                    else:
                        logger.info(f"  Excluded (score {job['score']}): {job['title']} at {job['company']}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scoring JSON: {e}")
            logger.error(f"Raw response: {content[:500]}")
            scored.extend(_fallback_scoring(batch))

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e.status_code} - {e.message}")
            scored.extend(_fallback_scoring(batch))

        except Exception as e:
            logger.error(f"Scoring failed: {type(e).__name__}: {e}")
            scored.extend(_fallback_scoring(batch))

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
    crypto_keywords = ["crypto", "blockchain", "web3", "defi", "digital asset", "token", "nft", "dao"]
    ai_keywords = ["artificial intelligence", "machine learning", "llm", "generative ai"]
    is_crypto = any(kw in combined for kw in crypto_keywords)
    is_ai = any(kw in combined for kw in ai_keywords)

    if is_top_company:
        return "top_company"
    if is_pmm and is_crypto:
        return "pmm_crypto"
    if is_pmm and is_ai:
        return "pmm_ai"
    if is_crypto:
        return "other_marketing_crypto"
    return "pmm_ai"


def _build_fallback_summary(job: dict) -> str:
    """Generate a keyword-based summary for fallback scoring."""
    title = job.get("title", "")
    company = job.get("company", "Unknown company")
    combined = f"{title} {company} {job.get('description', '')[:500]}".lower()

    industry = "crypto" if any(kw in combined for kw in ["crypto", "blockchain", "web3", "defi"]) else "AI/tech" if any(kw in combined for kw in ["ai", "artificial intelligence", "machine learning"]) else "tech"

    is_known = any(tc in company.lower() for tc in TOP_COMPANIES_SET)
    company_note = company if is_known else f"{company} (unverified)"

    return f"{title} at {company_note} — {industry} sector"


def _fallback_scoring(jobs: list[dict]) -> list[dict]:
    """Score jobs without AI using stricter keyword heuristics."""
    scored = []
    for job in jobs:
        job_copy = job.copy()
        job_copy["category"] = _guess_category(job)

        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        combined = f"{title} {company} {job.get('description', '')[:500]}".lower()

        # Start at 5 and earn points
        score = 5

        # Title match
        if any(kw in title for kw in ["product marketing", "pmm"]):
            score += 2
        elif any(kw in title for kw in ["growth marketing", "marketing lead", "head of marketing", "marketing director"]):
            score += 1

        # Seniority
        if any(kw in title for kw in ["senior", "head", "director", "lead", "vp", "principal"]):
            score += 1

        # Known company
        if any(tc in company for tc in TOP_COMPANIES_SET):
            score += 2

        # Industry match in title/company (strong signal)
        crypto_in_title_or_company = any(
            kw in f"{title} {company}"
            for kw in ["crypto", "blockchain", "web3", "defi", "digital asset"]
        )
        if crypto_in_title_or_company:
            score += 1

        job_copy["score"] = min(score, 10)
        job_copy["summary"] = _build_fallback_summary(job)
        job_copy["reason"] = ""

        if job_copy["score"] >= MIN_RELEVANCE_SCORE:
            scored.append(job_copy)

    return scored
