"""
Email digest builder and sender.
Formats scored jobs into a sectioned HTML email and sends via Gmail SMTP.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    RECIPIENT_EMAIL,
    EMAIL_SUBJECT_PREFIX,
    SMTP_SERVER,
    SMTP_PORT,
    GREENHOUSE_BOARDS,
    LEVER_BOARDS,
    ASHBY_BOARDS,
)

logger = logging.getLogger(__name__)

# Number of company career pages we scan
ATS_COMPANY_COUNT = len(GREENHOUSE_BOARDS) + len(LEVER_BOARDS) + len(ASHBY_BOARDS)


def _group_by_category(jobs: list[dict]) -> dict[str, list[dict]]:
    """Group jobs by category, sorted by score within each group."""
    groups = {
        "top_pick": [],
        "pmm_crypto": [],
        "pmm_ai": [],
        "other_marketing_crypto": [],
        "top_company": [],
    }

    for job in jobs:
        cat = job.get("category", "other_marketing_crypto")
        if cat in groups:
            groups[cat].append(job)
        else:
            groups["other_marketing_crypto"].append(job)

    for cat in groups:
        groups[cat].sort(key=lambda j: j.get("score", 0), reverse=True)

    return groups


SECTION_HEADERS = {
    "top_pick": ("Top Picks", "Best matches — apply first"),
    "pmm_crypto": ("Product Marketing — Crypto/Web3", "Core PMM roles at crypto companies"),
    "pmm_ai": ("Product Marketing — AI/Tech", "PMM roles at AI and tech companies"),
    "other_marketing_crypto": (
        "Other Marketing — Crypto/Web3",
        "Growth, brand, content, and comms roles at crypto companies",
    ),
    "top_company": (
        "New at Top Companies",
        "Any marketing role at companies you follow",
    ),
}


def _render_job_card(job: dict) -> str:
    """Render a single job as an HTML card."""
    title = escape(job.get("title", "Unknown"))
    company = escape(job.get("company", "Unknown"))
    location = escape(job.get("location", ""))
    salary = escape(job.get("salary", ""))
    url = job.get("url", "#")
    score = job.get("score", 0)
    summary = escape(job.get("summary", ""))
    reason = escape(job.get("reason", ""))

    # Use summary if available, otherwise reason, otherwise nothing
    description_line = summary or reason
    # Don't show fallback noise
    if description_line and "unavailable" in description_line.lower():
        description_line = ""

    salary_badge = ""
    if salary:
        salary_badge = f'<span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:3px;font-size:12px;margin-left:8px;">{salary}</span>'

    score_color = "#4caf50" if score >= 8 else "#ff9800" if score >= 6 else "#f44336"

    return f"""
    <div style="border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px;background:#fff;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <a href="{url}" style="color:#1a73e8;text-decoration:none;font-size:16px;font-weight:600;">{title}</a>
                {salary_badge}
            </div>
            <span style="background:{score_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;white-space:nowrap;">{score}/10</span>
        </div>
        <div style="margin-top:6px;color:#333;font-size:14px;">
            <strong style="font-size:15px;">{company}</strong>
            {(' &middot; ' + location) if location else ''}
        </div>
        {f'<div style="margin-top:8px;color:#555;font-size:13px;line-height:1.4;">{description_line}</div>' if description_line else ''}
    </div>
    """


def _render_section(category: str, jobs: list[dict]) -> str:
    """Render a section of the email."""
    if not jobs:
        return ""

    header, subtitle = SECTION_HEADERS.get(category, (category, ""))
    cards = "\n".join(_render_job_card(job) for job in jobs)

    return f"""
    <div style="margin-bottom:32px;">
        <h2 style="color:#1a1a1a;font-size:20px;margin-bottom:4px;border-bottom:2px solid #1a73e8;padding-bottom:8px;">
            {header} <span style="font-size:14px;color:#888;font-weight:normal;">({len(jobs)})</span>
        </h2>
        <p style="color:#888;font-size:13px;margin-top:4px;margin-bottom:16px;">{subtitle}</p>
        {cards}
    </div>
    """


def build_email_html(jobs: list[dict]) -> str:
    """Build the full HTML email body."""
    groups = _group_by_category(jobs)
    today = datetime.now().strftime("%A, %B %d, %Y")
    total = sum(len(g) for g in groups.values())

    sections = ""
    for category in ["top_pick", "pmm_crypto", "pmm_ai", "other_marketing_crypto", "top_company"]:
        sections += _render_section(category, groups[category])

    summary_items = []
    for cat, cat_jobs in groups.items():
        if cat_jobs:
            header = SECTION_HEADERS[cat][0]
            summary_items.append(f"{len(cat_jobs)} {header}")
    summary = " &middot; ".join(summary_items)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
        <div style="max-width:680px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px 32px;">
                <h1 style="margin:0;font-size:24px;">JobBot Daily Digest</h1>
                <p style="margin:8px 0 0;color:#aaa;font-size:14px;">{today}</p>
            </div>

            <div style="background:#f0f4ff;padding:12px 32px;border-bottom:1px solid #e0e0e0;">
                <p style="margin:0;font-size:14px;color:#555;">
                    <strong>{total} new roles</strong> found today &middot; {summary}
                </p>
            </div>

            <div style="padding:24px 32px;">
                {sections if sections else '<p style="color:#888;text-align:center;padding:40px 0;">No new matching jobs found today. All sources were checked.</p>'}
            </div>

            <div style="background:#f5f5f5;padding:16px 32px;border-top:1px solid #e0e0e0;">
                <p style="margin:0;font-size:11px;color:#aaa;text-align:center;">
                    Scanned LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs,
                    Web3.career, CryptoJobsList, RemoteOK, and {ATS_COMPANY_COUNT} company career pages.
                    Duplicates filtered. Only verified links included.
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def send_email(jobs: list[dict]):
    """Send the digest email via Gmail SMTP."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not set. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD.")
        html = build_email_html(jobs)
        fallback_path = "/tmp/jobbot_email.html"
        with open(fallback_path, "w") as f:
            f.write(html)
        logger.info(f"Email written to {fallback_path} instead.")
        return

    today = datetime.now().strftime("%b %d")
    total = len(jobs)
    subject = f"{EMAIL_SUBJECT_PREFIX}: {total} new roles - {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL

    plain_lines = [f"JobBot Daily Digest - {today}", f"{total} new roles found\n"]
    for job in sorted(jobs, key=lambda j: j.get("score", 0), reverse=True):
        plain_lines.append(
            f"[{job.get('score', '?')}/10] {job['title']} at {job['company']} - {job.get('url', '')}"
        )
    plain_text = "\n".join(plain_lines)

    html = build_email_html(jobs)

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email sent to {RECIPIENT_EMAIL}: '{subject}'")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        fallback_path = "/tmp/jobbot_email.html"
        with open(fallback_path, "w") as f:
            f.write(html)
        logger.info(f"Email saved to {fallback_path}")
        raise
