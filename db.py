"""
SQLite storage for deduplication and tracking.
Tracks which jobs have been seen so we don't email duplicates.
"""

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
    conn.commit()
    conn.close()
