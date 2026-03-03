#!/usr/bin/env python3
"""
JobBot Dashboard - Simple web UI for browsing job search results.

Usage:
    python dashboard.py                  # Start dashboard on port 5000
    python dashboard.py --port 8080      # Custom port
    python dashboard.py --refresh        # Refresh jobs then start dashboard
    python dashboard.py --refresh-only   # Refresh jobs without starting dashboard
"""

import argparse
import logging
import threading
from datetime import datetime
from html import escape

from flask import Flask, request, jsonify

from sources import fetch_all_jobs
from filters import filter_jobs
from scorer import score_jobs
from db import (
    save_dashboard_jobs,
    get_dashboard_jobs,
    get_dashboard_stats,
    filter_unseen,
    mark_seen,
    cleanup_old,
    save_feedback,
    get_flagged_job_keys,
)
from filters import make_job_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Track refresh state
_refresh_lock = threading.Lock()
_refresh_status = {"running": False, "last_run": None, "last_result": ""}


# ─── Refresh Pipeline ─────────────────────────────────────────────


def refresh_jobs():
    """Run the full fetch -> filter -> score pipeline and save to dashboard DB."""
    with _refresh_lock:
        if _refresh_status["running"]:
            return {"status": "already_running"}
        _refresh_status["running"] = True

    try:
        logger.info("=" * 60)
        logger.info("Dashboard refresh starting")
        logger.info("=" * 60)

        # Step 1: Fetch
        logger.info("Step 1: Fetching jobs from all sources...")
        raw_jobs = fetch_all_jobs()
        logger.info(f"Raw jobs fetched: {len(raw_jobs)}")

        if not raw_jobs:
            _refresh_status["last_result"] = "No jobs fetched"
            return {"status": "no_jobs"}

        # Step 2: Filter
        logger.info("Step 2: Filtering jobs...")
        filtered_jobs = filter_jobs(raw_jobs)
        logger.info(f"Jobs after filtering: {len(filtered_jobs)}")

        # Step 3: Score
        logger.info("Step 3: AI scoring...")
        if filtered_jobs:
            scored_jobs = score_jobs(filtered_jobs)
            logger.info(f"Jobs passing score threshold: {len(scored_jobs)}")
        else:
            scored_jobs = []

        # Step 4: Save to dashboard DB
        logger.info("Step 4: Saving to dashboard...")
        save_dashboard_jobs(scored_jobs)

        # Step 5: Cleanup old entries
        cleanup_old(days=30)

        result = f"Refreshed: {len(raw_jobs)} fetched -> {len(filtered_jobs)} filtered -> {len(scored_jobs)} scored"
        logger.info(result)
        _refresh_status["last_result"] = result
        return {"status": "ok", "message": result, "count": len(scored_jobs)}

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        _refresh_status["last_result"] = f"Error: {e}"
        return {"status": "error", "message": str(e)}

    finally:
        _refresh_status["last_run"] = datetime.now().isoformat()
        _refresh_status["running"] = False


# ─── Routes ────────────────────────────────────────────────────────


@app.route("/")
def index():
    """Serve the dashboard HTML page."""
    return DASHBOARD_HTML



@app.route("/api/stats")
def api_stats():
    """Get dashboard summary stats."""
    stats = get_dashboard_stats()
    stats["refresh_running"] = _refresh_status["running"]
    stats["last_refresh"] = _refresh_status["last_run"] or stats.get("last_refresh")
    stats["last_result"] = _refresh_status["last_result"]
    return jsonify(stats)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Trigger a background job refresh."""
    if _refresh_status["running"]:
        return jsonify({"status": "already_running"}), 409

    thread = threading.Thread(target=refresh_jobs, daemon=True)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Save user feedback (flag) for a job."""
    data = request.get_json()
    if not data or not data.get("job_key"):
        return jsonify({"status": "error", "message": "job_key required"}), 400

    save_feedback(
        job_key=data["job_key"],
        title=data.get("title", ""),
        company=data.get("company", ""),
        reason=data.get("reason", "").strip(),
    )
    return jsonify({"status": "ok"})


@app.route("/api/jobs")
def api_jobs_with_flags():
    """Get jobs filtered by time window and category, with flag status."""
    hours = request.args.get("hours", type=int)
    category = request.args.get("category", "all")
    jobs = get_dashboard_jobs(hours=hours, category=category)
    flagged_keys = get_flagged_job_keys()
    for j in jobs:
        j.pop("description", None)
        j["flagged"] = j["job_key"] in flagged_keys
    return jsonify({"jobs": jobs, "count": len(jobs)})


# ─── Dashboard HTML ────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JobBot Dashboard</title>
<style>
  :root {
    --bg: #0f0f13;
    --surface: #1a1a24;
    --surface-hover: #22222f;
    --border: #2a2a3a;
    --text: #e4e4ef;
    --text-muted: #8888a0;
    --accent: #6366f1;
    --accent-dim: #4f46e5;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .header h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .header h1 span {
    color: var(--accent);
  }

  .header-meta {
    font-size: 13px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .refresh-btn {
    background: var(--accent);
    color: white;
    border: none;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }
  .refresh-btn:hover { background: var(--accent-dim); }
  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .refresh-btn.spinning::after {
    content: '';
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid white;
    border-top-color: transparent;
    border-radius: 50%;
    margin-left: 8px;
    animation: spin 0.8s linear infinite;
    vertical-align: middle;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .filters {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .filter-group {
    display: flex;
    gap: 4px;
    background: var(--bg);
    border-radius: 10px;
    padding: 3px;
  }

  .filter-btn {
    background: transparent;
    color: var(--text-muted);
    border: none;
    padding: 7px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .filter-btn:hover {
    color: var(--text);
    background: var(--surface-hover);
  }
  .filter-btn.active {
    background: var(--accent);
    color: white;
  }

  .main {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px 16px;
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    font-size: 14px;
    color: var(--text-muted);
  }

  .job-count {
    font-weight: 600;
    color: var(--text);
  }

  .empty-state {
    text-align: center;
    padding: 80px 20px;
    color: var(--text-muted);
  }
  .empty-state h2 {
    font-size: 18px;
    margin-bottom: 8px;
    color: var(--text);
  }
  .empty-state p {
    font-size: 14px;
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.5;
  }

  .job-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    transition: border-color 0.15s;
  }
  .job-card:hover {
    border-color: var(--accent);
  }

  .job-card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
  }

  .job-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--accent);
    text-decoration: none;
    line-height: 1.3;
  }
  .job-title:hover { text-decoration: underline; }

  .score-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .score-high { background: var(--green); color: #000; }
  .score-mid { background: var(--amber); color: #000; }
  .score-low { background: var(--red); color: #fff; }

  .job-company {
    font-size: 15px;
    font-weight: 600;
    margin-top: 6px;
    color: var(--text);
  }

  .job-meta {
    display: flex;
    gap: 16px;
    margin-top: 6px;
    font-size: 13px;
    color: var(--text-muted);
    flex-wrap: wrap;
  }

  .job-meta span {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .salary-badge {
    background: #16382a;
    color: var(--green);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
  }

  .job-summary {
    margin-top: 10px;
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
  }

  .category-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 10px;
  }
  .cat-top_pick { background: #3b1764; color: #c084fc; }
  .cat-pmm_crypto { background: #1e3a5f; color: #60a5fa; }
  .cat-pmm_agentic { background: #3b2f0a; color: #fbbf24; }
  .cat-pmm_ai { background: #1a3636; color: #5eead4; }
  .cat-other_marketing_crypto { background: #2a2040; color: #a78bfa; }
  .cat-top_company { background: #1c3322; color: #86efac; }
  .cat-pmm_payments { background: #2f2215; color: #fb923c; }

  .section-divider {
    margin: 32px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  .section-divider .count {
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 400;
  }

  .flag-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
  }
  .flag-btn:hover {
    border-color: var(--red);
    color: var(--red);
  }
  .flag-btn.flagged {
    background: rgba(239, 68, 68, 0.15);
    border-color: var(--red);
    color: var(--red);
    cursor: default;
  }

  .flag-form {
    display: none;
    margin-top: 10px;
    padding: 12px;
    background: var(--bg);
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  .flag-form.open { display: block; }

  .flag-presets {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .flag-preset {
    background: var(--surface-hover);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .flag-preset:hover {
    border-color: var(--accent);
    color: var(--text);
  }

  .flag-input-row {
    display: flex;
    gap: 8px;
  }
  .flag-input {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-family: inherit;
  }
  .flag-input::placeholder { color: var(--text-muted); }
  .flag-input:focus {
    outline: none;
    border-color: var(--accent);
  }
  .flag-submit {
    background: var(--red);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }
  .flag-submit:hover { opacity: 0.9; }

  @media (max-width: 640px) {
    .header { padding: 16px; }
    .main { padding: 16px 12px; }
    .job-card { padding: 16px; }
    .header-top { flex-direction: column; align-items: flex-start; gap: 12px; }
    .filters { gap: 6px; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div>
      <h1>Job<span>Bot</span> Dashboard</h1>
    </div>
    <div style="display:flex;align-items:center;gap:16px;">
      <div class="header-meta">
        <span id="job-total"></span>
        <span id="last-refresh"></span>
        <span id="last-result" style="font-size:11px;opacity:0.7;"></span>
      </div>
      <button class="refresh-btn" id="refresh-btn" onclick="triggerRefresh()">Refresh Jobs</button>
    </div>
  </div>

  <div class="filters">
    <div class="filter-group" id="time-filters">
      <button class="filter-btn active" data-hours="" onclick="setTimeFilter(this)">All</button>
      <button class="filter-btn" data-hours="1" onclick="setTimeFilter(this)">1 hour</button>
      <button class="filter-btn" data-hours="12" onclick="setTimeFilter(this)">12 hours</button>
      <button class="filter-btn" data-hours="24" onclick="setTimeFilter(this)">24 hours</button>
      <button class="filter-btn" data-hours="168" onclick="setTimeFilter(this)">Week</button>
    </div>

    <div class="filter-group" id="category-filters">
      <button class="filter-btn active" data-category="all" onclick="setCategoryFilter(this)">All</button>
      <button class="filter-btn" data-category="top_pick" onclick="setCategoryFilter(this)">Top Picks</button>
      <button class="filter-btn" data-category="pmm_crypto" onclick="setCategoryFilter(this)">PMM Crypto</button>
      <button class="filter-btn" data-category="pmm_agentic" onclick="setCategoryFilter(this)">Agentic</button>
      <button class="filter-btn" data-category="pmm_payments" onclick="setCategoryFilter(this)">Payments</button>
      <button class="filter-btn" data-category="pmm_ai" onclick="setCategoryFilter(this)">AI</button>
      <button class="filter-btn" data-category="top_company" onclick="setCategoryFilter(this)">Top Co.</button>
    </div>
  </div>
</div>

<div class="main" id="main">
  <div class="empty-state" id="loading">
    <h2>Loading...</h2>
    <p>Fetching job data from the database.</p>
  </div>
</div>

<script>
const CATEGORY_LABELS = {
  top_pick: "Top Pick",
  pmm_crypto: "PMM Crypto/Web3",
  pmm_agentic: "Agentic",
  pmm_ai: "PMM AI/Tech",
  pmm_payments: "Payments/Stablecoins",
  other_marketing_crypto: "Marketing Crypto",
  top_company: "Top Company",
};

const CATEGORY_ORDER = [
  "top_pick", "pmm_crypto", "pmm_agentic", "pmm_payments",
  "pmm_ai", "other_marketing_crypto", "top_company"
];

let currentHours = null;
let currentCategory = "all";

function setTimeFilter(btn) {
  document.querySelectorAll("#time-filters .filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  const h = btn.dataset.hours;
  currentHours = h ? parseInt(h) : null;
  loadJobs();
}

function setCategoryFilter(btn) {
  document.querySelectorAll("#category-filters .filter-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  currentCategory = btn.dataset.category;
  loadJobs();
}

function scoreClass(score) {
  if (score >= 8) return "score-high";
  if (score >= 6) return "score-mid";
  return "score-low";
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr + "Z");
  const now = new Date();
  const mins = Math.floor((now - d) / 60000);
  if (mins < 60) return mins + "m ago";
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + "h ago";
  const days = Math.floor(hrs / 24);
  return days + "d ago";
}

const FLAG_PRESETS = [
  "Bad company",
  "Wrong role/seniority",
  "Wrong industry",
  "Score too high",
  "Already applied",
  "Not remote/NYC",
];

function renderJobCard(job) {
  const cat = job.category || "other_marketing_crypto";
  const salary = job.salary
    ? `<span class="salary-badge">${esc(job.salary)}</span>`
    : "";
  const summary = job.summary || job.reason || "";
  const summaryHtml = summary
    ? `<div class="job-summary">${esc(summary)}</div>`
    : "";
  const location = job.location || "Not specified";
  const fetched = timeAgo(job.fetched_at);
  const jk = esc(job.job_key);
  const flagged = job.flagged;

  const flagBtn = flagged
    ? `<button class="flag-btn flagged" disabled>Flagged</button>`
    : `<button class="flag-btn" onclick="toggleFlagForm('${jk}')">Flag</button>`;

  const presetBtns = FLAG_PRESETS.map(p =>
    `<button class="flag-preset" onclick="submitFlag('${jk}', '${esc(job.title)}', '${esc(job.company)}', '${p}')">${p}</button>`
  ).join("");

  return `
    <div class="job-card" id="card-${jk}">
      <div class="job-card-top">
        <a class="job-title" href="${esc(job.url)}" target="_blank" rel="noopener">${esc(job.title)}</a>
        <div style="display:flex;gap:8px;align-items:center;flex-shrink:0;">
          ${flagBtn}
          <span class="score-badge ${scoreClass(job.score)}">${job.score}/10</span>
        </div>
      </div>
      <div class="job-company">${esc(job.company)} ${salary}</div>
      <div class="job-meta">
        <span>${esc(location)}</span>
        <span>${esc(job.source || "")}</span>
        ${fetched ? `<span>${fetched}</span>` : ""}
      </div>
      ${summaryHtml}
      <span class="category-tag cat-${cat}">${CATEGORY_LABELS[cat] || cat}</span>
      <div class="flag-form" id="flag-${jk}">
        <div class="flag-presets">${presetBtns}</div>
        <div class="flag-input-row">
          <input class="flag-input" id="flag-input-${jk}" placeholder="Or type your own reason..." onkeydown="if(event.key==='Enter')submitFlagCustom('${jk}', '${esc(job.title)}', '${esc(job.company)}')">
          <button class="flag-submit" onclick="submitFlagCustom('${jk}', '${esc(job.title)}', '${esc(job.company)}')">Submit</button>
        </div>
      </div>
    </div>
  `;
}

function esc(s) {
  if (!s) return "";
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function groupByCategory(jobs) {
  const groups = {};
  for (const job of jobs) {
    const cat = job.category || "other_marketing_crypto";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(job);
  }
  return groups;
}

async function loadJobs() {
  const main = document.getElementById("main");
  let url = "/api/jobs?";
  if (currentHours) url += `hours=${currentHours}&`;
  if (currentCategory !== "all") url += `category=${currentCategory}&`;

  try {
    const resp = await fetch(url);
    const data = await resp.json();
    const jobs = data.jobs;

    if (!jobs.length) {
      main.innerHTML = `
        <div class="empty-state">
          <h2>No jobs found</h2>
          <p>No matching jobs for the current filters. Try a wider time window or click "Refresh Jobs" to pull new listings.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div class="status-bar">
        <span><span class="job-count">${jobs.length}</span> job${jobs.length === 1 ? "" : "s"} found</span>
      </div>
    `;

    if (currentCategory !== "all") {
      // Single category - just show cards
      html += jobs.map(renderJobCard).join("");
    } else {
      // Grouped by category
      const groups = groupByCategory(jobs);
      for (const cat of CATEGORY_ORDER) {
        if (groups[cat] && groups[cat].length) {
          html += `
            <div class="section-divider">
              <span>${CATEGORY_LABELS[cat] || cat}</span>
              <span class="count">${groups[cat].length}</span>
            </div>
          `;
          html += groups[cat].map(renderJobCard).join("");
        }
      }
      // Any remaining categories
      for (const cat of Object.keys(groups)) {
        if (!CATEGORY_ORDER.includes(cat) && groups[cat].length) {
          html += `
            <div class="section-divider">
              <span>${CATEGORY_LABELS[cat] || cat}</span>
              <span class="count">${groups[cat].length}</span>
            </div>
          `;
          html += groups[cat].map(renderJobCard).join("");
        }
      }
    }

    main.innerHTML = html;
  } catch (err) {
    main.innerHTML = `
      <div class="empty-state">
        <h2>Error loading jobs</h2>
        <p>${esc(err.message)}</p>
      </div>
    `;
  }
}

async function loadStats() {
  try {
    const resp = await fetch("/api/stats");
    const stats = await resp.json();
    document.getElementById("job-total").textContent = `${stats.total || 0} total jobs`;
    if (stats.last_refresh) {
      document.getElementById("last-refresh").textContent = `Last refresh: ${timeAgo(stats.last_refresh)}`;
    }
    if (stats.last_result) {
      const el = document.getElementById("last-result");
      el.textContent = stats.last_result;
      el.style.color = stats.last_result.startsWith("Error") ? "var(--red)" : "var(--text-muted)";
    }
    // Update refresh button state
    const btn = document.getElementById("refresh-btn");
    if (stats.refresh_running) {
      btn.disabled = true;
      btn.textContent = "Refreshing...";
      btn.classList.add("spinning");
      setTimeout(loadStats, 3000);
    } else {
      btn.disabled = false;
      btn.textContent = "Refresh Jobs";
      btn.classList.remove("spinning");
    }
  } catch (err) {
    // ignore stats errors
  }
}

async function triggerRefresh() {
  const btn = document.getElementById("refresh-btn");
  btn.disabled = true;
  btn.textContent = "Refreshing...";
  btn.classList.add("spinning");

  try {
    await fetch("/api/refresh", { method: "POST" });
    // Poll until done
    const poll = setInterval(async () => {
      const resp = await fetch("/api/stats");
      const stats = await resp.json();
      if (!stats.refresh_running) {
        clearInterval(poll);
        btn.disabled = false;
        btn.textContent = "Refresh Jobs";
        btn.classList.remove("spinning");
        loadJobs();
        loadStats();
      }
    }, 3000);
  } catch (err) {
    btn.disabled = false;
    btn.textContent = "Refresh Jobs";
    btn.classList.remove("spinning");
  }
}

function toggleFlagForm(jobKey) {
  const form = document.getElementById("flag-" + jobKey);
  if (form) form.classList.toggle("open");
}

async function submitFlag(jobKey, title, company, reason) {
  try {
    await fetch("/api/feedback", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({job_key: jobKey, title, company, reason}),
    });
    // Update UI: close form, mark as flagged
    const form = document.getElementById("flag-" + jobKey);
    if (form) form.classList.remove("open");
    const card = document.getElementById("card-" + jobKey);
    if (card) {
      const btn = card.querySelector(".flag-btn");
      if (btn) {
        btn.textContent = "Flagged";
        btn.classList.add("flagged");
        btn.disabled = true;
      }
    }
  } catch (err) {
    console.error("Flag failed:", err);
  }
}

function submitFlagCustom(jobKey, title, company) {
  const input = document.getElementById("flag-input-" + jobKey);
  const reason = input ? input.value.trim() : "";
  if (!reason) { input && input.focus(); return; }
  submitFlag(jobKey, title, company, reason);
}

// Initial load
loadJobs();
loadStats();
// Auto-refresh stats every 30s
setInterval(loadStats, 30000);
</script>
</body>
</html>"""


# ─── Main ──────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobBot Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--refresh", action="store_true", help="Refresh jobs on startup")
    parser.add_argument("--refresh-only", action="store_true", help="Refresh jobs and exit")
    args = parser.parse_args()

    if args.refresh or args.refresh_only:
        logger.info("Running initial job refresh...")
        result = refresh_jobs()
        logger.info(f"Refresh result: {result}")
        if args.refresh_only:
            raise SystemExit(0)

    logger.info(f"Starting dashboard on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
