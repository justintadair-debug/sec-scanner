"""Filing and analysis cache — skip re-fetching and re-analyzing unchanged filings."""

import json
import hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


def _filing_key(ticker: str, filing_date: str, filing_url: str) -> str:
    """Stable cache key: ticker + date + url hash."""
    url_hash = hashlib.md5(filing_url.encode()).hexdigest()[:8]
    return f"{ticker.upper()}_{filing_date}_{url_hash}"


def _analysis_key(ticker: str, filing_date: str, filing_url: str) -> str:
    return _filing_key(ticker, filing_date, filing_url) + "_analysis"


# ── Filing text cache ─────────────────────────────────────────────────────────

def get_filing(ticker: str, filing_date: str, filing_url: str) -> str | None:
    """Return cached filing text if available, else None."""
    path = CACHE_DIR / f"{_filing_key(ticker, filing_date, filing_url)}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def save_filing(ticker: str, filing_date: str, filing_url: str, text: str):
    """Cache filing text to disk."""
    path = CACHE_DIR / f"{_filing_key(ticker, filing_date, filing_url)}.txt"
    path.write_text(text, encoding="utf-8")


# ── Analysis result cache ─────────────────────────────────────────────────────

def get_analysis(ticker: str, filing_date: str, filing_url: str) -> dict | None:
    """Return cached analysis result if available, else None."""
    path = CACHE_DIR / f"{_analysis_key(ticker, filing_date, filing_url)}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_analysis(ticker: str, filing_date: str, filing_url: str, result: dict):
    """Cache analysis result to disk."""
    path = CACHE_DIR / f"{_analysis_key(ticker, filing_date, filing_url)}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def cache_stats() -> dict:
    """Return basic cache stats."""
    files = list(CACHE_DIR.glob("*.txt"))
    analyses = list(CACHE_DIR.glob("*_analysis.json"))
    return {
        "cached_filings": len(files),
        "cached_analyses": len(analyses),
        "cache_dir": str(CACHE_DIR),
    }


def clear_ticker(ticker: str):
    """Remove all cached data for a specific ticker (force re-fetch)."""
    removed = 0
    for f in CACHE_DIR.glob(f"{ticker.upper()}_*"):
        f.unlink()
        removed += 1
    return removed
