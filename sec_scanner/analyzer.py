"""Run Claude CLI to analyze filing text and parse scores + findings."""

import json
import subprocess
import sys
from pathlib import Path

# Load project context once at import time
_CONTEXT_PATH = Path(__file__).parent.parent / "project_context.md"
_PROJECT_CONTEXT = _CONTEXT_PATH.read_text() if _CONTEXT_PATH.exists() else ""


PROMPT_TEMPLATE = """You are analyzing a SEC 10-K filing for evidence of genuine AI adoption vs. AI washing.

Company: {ticker} — {company}
Filing date: {date}

Score this company on these 5 dimensions (0-10 each):
1. SPECIFICITY: Are AI implementations specific (named products, use cases) or vague buzzwords?
2. FINANCIAL_IMPACT: Is there quantified revenue/cost impact from AI?
3. INTEGRATION_DEPTH: How deeply is AI woven into core business vs. bolt-on?
4. COMPETITIVE_MOAT: Does AI create defensible competitive advantage?
5. EXECUTION_EVIDENCE: Are there concrete deployments, partnerships, or milestones?

Also provide:
- 3 key findings (specific evidence from the filing)
- 2-3 red flags (concerns or gaps)
- 1 investment takeaway (2-3 sentences)
- Verdict: "Genuine AI Adopter" (score >= 60) or "Strong AI Washing" (score < 40) or "Mixed Signals" (40-59)
- disclosure_style: One of "verbose" | "conservative" | "standard"
  - "verbose": company explicitly details AI products, metrics, and strategy (e.g. NVDA, MSFT)
  - "conservative": company historically understates in filings vs. public reality (e.g. AAPL, JPM)
  - "standard": typical disclosure depth for their sector

Output as JSON:
{{
  "scores": {{"SPECIFICITY": X, "FINANCIAL_IMPACT": X, "INTEGRATION_DEPTH": X, "COMPETITIVE_MOAT": X, "EXECUTION_EVIDENCE": X}},
  "findings": ["...", "...", "..."],
  "flags": ["...", "...", "..."],
  "takeaway": "...",
  "verdict": "...",
  "disclosure_style": "..."
}}

IMPORTANT: Output ONLY the JSON object, no markdown code fences, no extra text.

FILING TEXT:
{filing_text}"""


def analyze_filing(filing: dict) -> dict | None:
    """Analyze a filing using Claude CLI subprocess.

    Args:
        filing: dict with keys ticker, company, date, text

    Returns:
        dict with keys: ticker, company, score, verdict, scores, findings, flags, takeaway, date
        Or None on failure.
    """
    from sec_scanner.cache import get_analysis, save_analysis

    # Check analysis cache — skip Claude call if same filing already scored
    url = filing.get("url", "")
    cached = get_analysis(filing["ticker"], filing["date"], url)
    if cached:
        print(f"  [{filing['ticker']}] Using cached analysis (score: {cached['score']})")
        return cached

    context_block = f"---\n{_PROJECT_CONTEXT}\n---\n\n" if _PROJECT_CONTEXT else ""
    prompt = context_block + PROMPT_TEMPLATE.format(
        ticker=filing["ticker"],
        company=filing["company"],
        date=filing["date"],
        filing_text=filing["text"],
    )

    print(f"  [{filing['ticker']}] Running Claude analysis...")

    try:
        result = subprocess.run(
            ["/Users/justinadair/bin/claude-wrapper", "-p", "--output-format", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"  [{filing['ticker']}] ERROR: Claude CLI failed: {result.stderr[:200]}")
            return None

        output = result.stdout.strip()

        # Strip markdown code fences if present
        if output.startswith("```"):
            lines = output.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            output = "\n".join(lines)

        parsed = json.loads(output)

    except subprocess.TimeoutExpired:
        print(f"  [{filing['ticker']}] ERROR: Claude CLI timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"  [{filing['ticker']}] ERROR: Could not parse Claude output as JSON: {e}")
        print(f"  [{filing['ticker']}] Raw output (first 500 chars): {output[:500]}")
        return None

    scores = parsed.get("scores", {})
    total_score = sum(scores.values()) * 2  # Each dimension 0-10, 5 dims = max 50, * 2 = max 100

    result = {
        "ticker": filing["ticker"],
        "company": filing["company"],
        "score": total_score,
        "verdict": parsed.get("verdict", "Unknown"),
        "scores": scores,
        "findings": parsed.get("findings", []),
        "flags": parsed.get("flags", []),
        "takeaway": parsed.get("takeaway", ""),
        "disclosure_style": parsed.get("disclosure_style", "standard"),
        "date": filing["date"],
    }

    # Cache the result so we don't re-run Claude on the same filing
    save_analysis(filing["ticker"], filing["date"], url, result)
    print(f"  [{filing['ticker']}] Analysis cached")

    return result
