# SEC Filing Scanner — Build Instructions

## What to Build
A Python CLI tool that:
1. Takes a list of ticker symbols
2. Fetches their latest 10-K filings from SEC EDGAR
3. Analyzes each filing with Claude CLI (Max plan — use `claude -p` subprocess, NOT API key)
4. Scores each company on 5 dimensions (0-10 each): SPECIFICITY, FINANCIAL_IMPACT, INTEGRATION_DEPTH, COMPETITIVE_MOAT, EXECUTION_EVIDENCE
5. Generates a final HTML report using the template in `report-template.html`

## Architecture
- `sec_scanner/fetcher.py` — SEC EDGAR API: get CIK by ticker, fetch latest 10-K filing URL, download and strip to clean text
- `sec_scanner/analyzer.py` — Run Claude CLI to analyze filing text, parse scores + findings
- `sec_scanner/reporter.py` — Inject real data into report-template.html (replace the hardcoded JS `data` array)
- `sec_scanner/cli.py` — Entry point: `sec-scanner MSFT NVDA AAPL` or `sec-scanner --file tickers.txt`
- `pyproject.toml` — Package setup with entry point

## Key Details
- SEC EDGAR full-text search: https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2024-01-01&forms=10-K
- CIK lookup: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=10&search_text=
- Use requests + BeautifulSoup for scraping
- Strip filings to max 80,000 chars (most AI-relevant sections)
- Claude CLI command: `claude -p --output-format text "PROMPT"`
- Always use Claude CLI subprocess (never anthropic API key)

## Claude Prompt for Analysis
```
You are analyzing a SEC 10-K filing for evidence of genuine AI adoption vs. AI washing.

Company: {ticker} — {company_name}
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

Output as JSON:
{
  "scores": {"SPECIFICITY": X, "FINANCIAL_IMPACT": X, "INTEGRATION_DEPTH": X, "COMPETITIVE_MOAT": X, "EXECUTION_EVIDENCE": X},
  "findings": ["...", "...", "..."],
  "flags": ["...", "...", "..."],
  "takeaway": "...",
  "verdict": "..."
}

FILING TEXT:
{filing_text}
```

## Report Generation
The report-template.html has a hardcoded JS `data` array. Replace it with real data.
Find: `const data = [` ... `];`
Replace with the actual scored companies.

## Entry Point
```bash
sec-scanner MSFT NVDA IBM  # analyze specific tickers
sec-scanner --output report.html MSFT NVDA  # custom output path
```

## Done Signal
When completely finished, run:
openclaw system event --text "Done: SEC Filing Scanner rebuilt — Python CLI that fetches real 10-Ks from EDGAR and generates HTML report" --mode now
