# SEC Filing Scanner — AI-Washing Detector

> Scores S&P 500 companies 0–100 on whether their AI claims are real or just marketing.

Built with public EDGAR data. No paywalls. No insider access. Open methodology.

---

## Latest Scores (March 2026)

| Ticker | Company | Score | Verdict |
|--------|---------|-------|---------|
| 🟢 NVDA | NVIDIA | 96/100 | Genuine AI Adopter |
| 🟢 MSFT | Microsoft | 84/100 | Genuine AI Adopter |
| 🟢 GOOG | Alphabet | 82/100 | Genuine AI Adopter |
| 🟡 META | Meta | 74/100 | Genuine AI Adopter |
| 🟡 TSLA | Tesla | 72/100 | Genuine AI Adopter |
| 🟡 CRM | Salesforce | 64/100 | Genuine AI Adopter |
| 🟠 ORCL | Oracle | 56/100 | Mixed Signals |
| 🟠 IBM | IBM | 46/100 | Mixed Signals |
| 🔴 AMZN | Amazon | 36/100 | Strong AI Washing ⚠ |
| 🔴 AAPL | Apple | 22/100 | Strong AI Washing ⚠ |
| 🔴 NFLX | Netflix | 14/100 | Strong AI Washing |
| 🔴 JPM | JPMorgan | 14/100 | Strong AI Washing ⚠ |

⚠ *Conservative filer: deliberately understates AI in 10-Ks. Score reflects the filing language, not public reality.*

---

## What It Measures

Scores are based on analysis of annual 10-K filings from SEC EDGAR. Not press releases. Not earnings calls. The official legal document companies are held to.

**Scoring dimensions:**
- **Specificity** — Are AI claims backed by metrics, or vague buzzwords?
- **Consistency** — Does AI language match actual business operations?
- **Evidence** — Are there concrete examples of AI deployment?
- **Risk disclosure** — Does the company acknowledge AI risks honestly?
- **Forward guidance** — Are AI plans specific and measurable?

---

## Key Insight

Apple (22/100) and Amazon (36/100) aren't necessarily failing at AI — they're **conservative filers**. These companies deliberately understate capabilities in their 10-Ks as legal strategy. The score reflects the filing, not the company.

Nvidia (96/100) scores highest because their AI claims are specific, measurable, and backed by disclosed infrastructure metrics.

---

## How It Works

1. Fetches latest 10-K filing from SEC EDGAR (public API)
2. Extracts and cleans filing text (80K chars)
3. Runs Claude analysis across 5 scoring dimensions
4. Caches results — no redundant API calls
5. Generates HTML report

```bash
pip install sec-scanner
sec-scanner AAPL
sec-scanner --watchlist  # scan all tracked companies
```

---

## Tech Stack

- Python 3.11+
- SEC EDGAR public API (no key required)
- Claude AI (analysis engine)
- SQLite (scan history)
- Two-layer disk cache (filing text + analysis)

---

## Built By

Justin Adair | Part of the Neo AI portfolio

*Companion projects: [Say vs. Do](https://github.com/justintadair-debug/sayvdo) — multi-dimensional corporate truthfulness engine*
