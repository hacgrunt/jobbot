"""
SQLite storage for deduplication, tracking, and dashboard data.
Tracks which jobs have been seen and stores full job data for the dashboard.
"""

import json
import sqlite3
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_key TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            first_seen TEXT DEFAULT (datetime('now')),
            emailed INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_jobs (
            job_key TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            url TEXT,
            source TEXT,
            posted_date TEXT,
            description TEXT,
            score INTEGER DEFAULT 0,
            category TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            summary TEXT DEFAULT '',
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_dashboard_fetched
        ON dashboard_jobs(fetched_at)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_dashboard_category
        ON dashboard_jobs(category)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT NOT NULL,
            title TEXT,
            company TEXT,
            action TEXT DEFAULT 'flag',
            reason TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def is_seen(job_key: str) -> bool:
    conn = _connect()
    row = conn.execute(
        "SELECT 1 FROM seen_jobs WHERE job_key = ?", (job_key,)
    ).fetchone()
    conn.close()
    return row is not None


def mark_seen(jobs: list[dict]):
    if not jobs:
        return
    conn = _connect()
    conn.executemany(
        """INSERT OR IGNORE INTO seen_jobs (job_key, title, company, emailed)
           VALUES (?, ?, ?, 1)""",
        [(j["job_key"], j["title"], j["company"]) for j in jobs],
    )
    conn.commit()
    conn.close()


def filter_unseen(jobs: list[dict]) -> list[dict]:
    if not jobs:
        return []
    conn = _connect()
    seen_keys = {
        row[0]
        for row in conn.execute("SELECT job_key FROM seen_jobs").fetchall()
    }
    conn.close()
    return [j for j in jobs if j["job_key"] not in seen_keys]


def cleanup_old(days: int = 30):
    conn = _connect()
    conn.execute(
        "DELETE FROM seen_jobs WHERE first_seen < datetime('now', ?)",
        (f"-{days} days",),
    )
    conn.execute(
        "DELETE FROM dashboard_jobs WHERE fetched_at < datetime('now', ?)",
        (f"-{days} days",),
    )
    conn.commit()
    conn.close()


# ─── Dashboard Storage ────────────────────────────────────────────


def save_dashboard_jobs(jobs: list[dict]):
    """Save scored jobs to the dashboard table (upsert)."""
    if not jobs:
        return
    conn = _connect()
    conn.executemany(
        """INSERT OR REPLACE INTO dashboard_jobs
           (job_key, title, company, location, salary, url, source,
            posted_date, description, score, category, reason, summary)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                j.get("job_key", ""),
                j.get("title", ""),
                j.get("company", ""),
                j.get("location", ""),
                j.get("salary", ""),
                j.get("url", ""),
                j.get("source", ""),
                j.get("posted_date", ""),
                j.get("description", "")[:2000],  # truncate for storage
                j.get("score", 0),
                j.get("category", ""),
                j.get("reason", ""),
                j.get("summary", ""),
            )
            for j in jobs
        ],
    )
    conn.commit()
    conn.close()


def get_dashboard_jobs(hours: int | None = None, category: str | None = None) -> list[dict]:
    """Get jobs for the dashboard, optionally filtered by time window and category."""
    conn = _connect()
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM dashboard_jobs WHERE 1=1"
    params = []

    if hours is not None:
        query += " AND fetched_at >= datetime('now', ?)"
        params.append(f"-{hours} hours")

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY score DESC, fetched_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_dashboard_stats() -> dict:
    """Get summary stats for the dashboard."""
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM dashboard_jobs").fetchone()[0]
    last_refresh = conn.execute(
        "SELECT MAX(fetched_at) FROM dashboard_jobs"
    ).fetchone()[0]

    categories = {}
    for row in conn.execute(
        "SELECT category, COUNT(*) FROM dashboard_jobs GROUP BY category"
    ).fetchall():
        categories[row[0]] = row[1]

    conn.close()
    return {
        "total": total,
        "last_refresh": last_refresh,
        "categories": categories,
    }


# ─── User Feedback ───────────────────────────────────────────────


def save_feedback(job_key: str, title: str, company: str, reason: str):
    """Save user feedback (flag) for a job."""
    conn = _connect()
    conn.execute(
        """INSERT INTO user_feedback (job_key, title, company, reason)
           VALUES (?, ?, ?, ?)""",
        (job_key, title, company, reason),
    )
    conn.commit()
    conn.close()


def get_recent_feedback(limit: int = 50) -> list[dict]:
    """Get recent user feedback for injection into scoring prompt."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT title, company, reason, created_at
           FROM user_feedback
           ORDER BY created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_flagged_job_keys() -> set[str]:
    """Get all job_keys the user has flagged."""
    conn = _connect()
    keys = {
        row[0]
        for row in conn.execute("SELECT DISTINCT job_key FROM user_feedback").fetchall()
    }
    conn.close()
    return keys
