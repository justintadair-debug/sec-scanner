"""Score history tracking — stores every scan result for trend analysis."""

import sqlite3
import json
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent.parent / "scan_history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker       TEXT NOT NULL,
                company      TEXT,
                score        INTEGER NOT NULL,
                verdict      TEXT,
                disclosure_style TEXT,
                filing_date  TEXT,
                scanned_at   TEXT DEFAULT (date('now')),
                scores_json  TEXT,
                takeaway     TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON scan_history(ticker)")
        conn.commit()


def save_result(result: dict):
    init_db()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO scan_history
            (ticker, company, score, verdict, disclosure_style, filing_date, scores_json, takeaway)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["ticker"],
            result.get("company"),
            result["score"],
            result.get("verdict"),
            result.get("disclosure_style", "standard"),
            result.get("date"),
            json.dumps(result.get("scores", {})),
            result.get("takeaway"),
        ))
        conn.commit()


def get_history(ticker: str) -> list[dict]:
    """Return all scan history for a ticker, oldest first."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scan_history WHERE ticker = ? ORDER BY scanned_at ASC",
            (ticker.upper(),)
        ).fetchall()
        return [dict(r) for r in rows]


def get_trend(ticker: str) -> str:
    """Return trend string: 'improving', 'declining', 'stable', or 'new'."""
    history = get_history(ticker)
    if len(history) < 2:
        return "new"
    scores = [h["score"] for h in history[-3:]]  # last 3 scans
    if scores[-1] > scores[0] + 5:
        return "improving"
    elif scores[-1] < scores[0] - 5:
        return "declining"
    return "stable"


def get_all_tickers() -> list[str]:
    """Return all tickers that have been scanned."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ticker FROM scan_history ORDER BY ticker"
        ).fetchall()
        return [r["ticker"] for r in rows]
