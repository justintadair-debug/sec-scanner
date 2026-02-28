"""SEC EDGAR API: fetch 10-K filings and extract clean text."""

import re
import time
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {
    "User-Agent": "SECScanner/1.0 (research@example.com)",
    "Accept-Encoding": "gzip, deflate",
}

# Rate limit: SEC asks for max 10 requests/second
_last_request_time = 0.0


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < 0.15:
        time.sleep(0.15 - elapsed)
    _last_request_time = time.time()


def get_cik(ticker: str) -> str | None:
    """Look up CIK number for a ticker symbol."""
    _throttle()
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "CIK": ticker,
        "type": "10-K",
        "dateb": "",
        "owner": "include",
        "count": "10",
        "search_text": "",
        "output": "atom",
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract CIK from the feed — look for accession numbers
    cik_match = re.search(r"CIK=(\d+)", resp.text)
    if cik_match:
        return cik_match.group(1).lstrip("0")

    # Try company search JSON endpoint as fallback
    _throttle()
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    resp2 = requests.get(tickers_url, headers=HEADERS, timeout=30)
    resp2.raise_for_status()
    tickers_data = resp2.json()
    for entry in tickers_data.values():
        if entry.get("ticker", "").upper() == ticker.upper():
            return str(entry["cik_str"])

    return None


def get_company_name(ticker: str) -> str:
    """Get company name from SEC company tickers JSON."""
    _throttle()
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    for entry in resp.json().values():
        if entry.get("ticker", "").upper() == ticker.upper():
            return entry.get("title", ticker)
    return ticker


def get_latest_10k_url(cik: str) -> tuple[str, str] | None:
    """Get the URL and filing date of the latest 10-K for a CIK.

    Returns (filing_url, filing_date) or None.
    """
    _throttle()
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])

    for i, form in enumerate(forms):
        if form in ("10-K", "10-K/A"):
            accession = accessions[i].replace("-", "")
            doc = primary_docs[i]
            filing_date = dates[i]
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"
            return filing_url, filing_date

    return None


def download_and_clean(url: str, max_chars: int = 80000) -> str:
    """Download a 10-K filing and strip it to clean text."""
    _throttle()
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script, style, and XBRL tags
    for tag in soup.find_all(["script", "style", "ix:nonfraction", "ix:nonnumeric",
                               "ix:header", "ix:hidden", "ix:references"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Clean up whitespace
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    text = "\n".join(lines)

    # Remove excessive repeated characters
    text = re.sub(r"[_=\-]{10,}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncate to max_chars
    if len(text) > max_chars:
        text = text[:max_chars]

    return text


def fetch_filing(ticker: str) -> dict | None:
    """Full pipeline: ticker -> clean filing text + metadata.

    Returns dict with keys: ticker, company, date, text, url
    Or None if filing could not be fetched.
    """
    print(f"  [{ticker}] Looking up CIK...")
    cik = get_cik(ticker)
    if not cik:
        print(f"  [{ticker}] ERROR: Could not find CIK")
        return None

    print(f"  [{ticker}] CIK={cik}, fetching company name...")
    company = get_company_name(ticker)

    print(f"  [{ticker}] Finding latest 10-K filing...")
    result = get_latest_10k_url(cik)
    if not result:
        print(f"  [{ticker}] ERROR: No 10-K filing found")
        return None

    filing_url, filing_date = result
    print(f"  [{ticker}] Downloading filing from {filing_date}...")
    text = download_and_clean(filing_url)
    print(f"  [{ticker}] Got {len(text):,} chars of clean text")

    return {
        "ticker": ticker.upper(),
        "company": company,
        "date": filing_date,
        "text": text,
        "url": filing_url,
    }
