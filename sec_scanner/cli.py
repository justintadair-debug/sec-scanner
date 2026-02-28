"""CLI entry point: sec-scanner MSFT NVDA AAPL"""

import argparse
import sys
import time
import requests

from sec_scanner.fetcher import fetch_filing
from sec_scanner.analyzer import analyze_filing
from sec_scanner.reporter import generate_report
from sec_scanner.history import save_result, get_history, get_trend

WORKLOG_URL = "http://localhost:8092/api/log"
WORKLOG_KEY = "wl-justin-2026"

def log_to_worklog(tickers, results, elapsed_hours):
    try:
        summary = ", ".join(f"{r['ticker']} {r['score']}/100" for r in results)
        requests.post(WORKLOG_URL, json={
            "project": "SEC Scanner",
            "description": f"Scanned {len(tickers)} companies: {summary}",
            "task_type": "scan",
            "actual_hours": round(elapsed_hours, 3),
            "manual_estimate": len(tickers) * 2.0,  # ~2hrs manual research per company
            "timestamp": int(time.time() * 1000),
            "metadata": {"tickers": tickers, "results": [{"ticker": r["ticker"], "score": r["score"]} for r in results]},
        }, headers={"X-WL-Key": WORKLOG_KEY}, timeout=3)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="sec-scanner",
        description="Scan SEC 10-K filings for genuine AI adoption vs. AI washing",
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        help="Ticker symbols to analyze (e.g., MSFT NVDA AAPL)",
    )
    parser.add_argument(
        "--file", "-f",
        help="Read tickers from a file (one per line)",
    )
    parser.add_argument(
        "--output", "-o",
        default="report.html",
        help="Output HTML report path (default: report.html)",
    )
    parser.add_argument(
        "--watchlist", "-w",
        action="store_true",
        help="Use watchlist.txt in the current directory",
    )
    parser.add_argument(
        "--history",
        metavar="TICKER",
        help="Show scan history for a ticker",
    )

    args = parser.parse_args()

    # Show history and exit
    if args.history:
        ticker = args.history.upper()
        history = get_history(ticker)
        if not history:
            print(f"No scan history for {ticker}")
        else:
            print(f"\n{ticker} — Scan History ({len(history)} scans)")
            print("-" * 50)
            for h in history:
                trend = "→"
                print(f"  {h['scanned_at']}  Score: {h['score']:3d}/100  {h['verdict']}  [{h.get('disclosure_style','standard')}]")
            trend = get_trend(ticker)
            print(f"\n  Trend: {trend.upper()}")
        return

    # Collect tickers
    tickers = list(args.tickers) if args.tickers else []
    if args.watchlist:
        import os
        wl_path = os.path.join(os.getcwd(), "watchlist.txt")
        if not os.path.exists(wl_path):
            wl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "watchlist.txt")
        if os.path.exists(wl_path):
            with open(wl_path) as f:
                for line in f:
                    t = line.strip().upper()
                    if t and not t.startswith("#"):
                        tickers.append(t)
            print(f"  Loaded {len(tickers)} tickers from watchlist.txt")
        else:
            print("ERROR: watchlist.txt not found")
            sys.exit(1)
    if args.file:
        with open(args.file) as f:
            for line in f:
                t = line.strip().upper()
                if t and not t.startswith("#"):
                    tickers.append(t)

    if not tickers:
        parser.error("No tickers provided. Use: sec-scanner MSFT NVDA or sec-scanner --file tickers.txt")

    # Deduplicate while preserving order
    seen = set()
    unique_tickers = []
    for t in tickers:
        t = t.upper()
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    tickers = unique_tickers

    run_start = time.time()

    print(f"\n{'='*60}")
    print(f"  SEC AI Adoption Scanner")
    print(f"  Analyzing {len(tickers)} companies: {', '.join(tickers)}")
    print(f"{'='*60}\n")

    # Phase 1: Fetch filings
    print("[1/3] Fetching 10-K filings from SEC EDGAR...\n")
    filings = []
    for ticker in tickers:
        filing = fetch_filing(ticker)
        if filing:
            filings.append(filing)
        else:
            print(f"  [{ticker}] SKIPPED — could not fetch filing\n")
    print()

    if not filings:
        print("ERROR: No filings could be fetched. Exiting.")
        sys.exit(1)

    # Phase 2: Analyze with Claude
    print(f"[2/3] Analyzing {len(filings)} filings with Claude...\n")
    results = []
    for filing in filings:
        result = analyze_filing(filing)
        if result:
            results.append(result)
            save_result(result)
            trend = get_trend(result["ticker"])
            style = result.get("disclosure_style", "standard")
            style_note = " ⚠ conservative filer" if style == "conservative" else ""
            trend_note = f" [{trend}]" if trend != "new" else ""
            print(f"  [{result['ticker']}] Score: {result['score']}/100 — {result['verdict']}{trend_note}{style_note}")
        else:
            print(f"  [{filing['ticker']}] SKIPPED — analysis failed")
    print()

    if not results:
        print("ERROR: No filings could be analyzed. Exiting.")
        sys.exit(1)

    # Phase 3: Generate report
    print(f"[3/3] Generating HTML report...\n")
    output = generate_report(results, args.output)
    print(f"  Report saved to: {output}")
    print(f"\n  {len(results)} companies analyzed.")
    print(f"  Genuine adopters: {sum(1 for r in results if r['score'] >= 60)}")
    print(f"  AI washing: {sum(1 for r in results if r['score'] < 40)}")
    print(f"  Mixed signals: {sum(1 for r in results if 40 <= r['score'] < 60)}")
    print()

    # Auto-log to WorkLog
    elapsed = (time.time() - run_start) / 3600
    log_to_worklog(tickers, results, elapsed)


if __name__ == "__main__":
    main()
