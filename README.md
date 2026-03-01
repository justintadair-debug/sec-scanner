# SEC Filing Scanner — AI-Washing Detector

> **Scores S&P 500 companies 0–100 on whether their AI claims are real or just marketing.**

Most companies say they're "leveraging AI." Few actually are. This tool reads their SEC filings and calls out the difference.

---

## Sample Scores

| Company | Score | Verdict |
|---|---|---|
| NVDA | 94 / 100 | 🟢 Genuine AI Adopter |
| MSFT | 82 / 100 | 🟢 Genuine AI Adopter |
| GOOG | 84 / 100 | 🟢 Genuine AI Adopter |
| META | 74 / 100 | 🟡 Strong |
| TSLA | 72 / 100 | 🟡 Strong |
| CRM | 64 / 100 | 🟡 Moderate |
| ORCL | 58 / 100 | 🟡 Moderate |
| AMZN | 52 / 100 | 🟠 Mixed |
| IBM | 46 / 100 | 🟠 Mixed |
| AAPL | 34 / 100 | 🔴 Conservative Filer |
| NFLX | 14 / 100 | 🔴 AI Washing |
| JPM | 14 / 100 | 🔴 AI Washing |

> **Key Insight:** Apple's 34/100 is not a failure — it's a deliberate strategy. Conservative filers like Apple intentionally understate AI in their 10-Ks to avoid regulatory and competitive exposure. The score reflects disclosure, not capability.

---

## How It Works

### 1. EDGAR Fetcher
Pulls 10-K annual reports directly from the SEC's public EDGAR database. No API key required.

### 2. Claude Analysis
Each filing is analyzed across 5 dimensions:
- **Specificity** — Are AI claims concrete or vague?
- **Financial Impact** — Is AI tied to measurable revenue/cost outcomes?
- **Integration Depth** — Is AI core to operations or bolted on?
- **Competitive Moat** — Does their AI create defensible advantage?
- **Execution Evidence** — Do they show results, not just plans?

### 3. Two-Layer Cache
- **Layer 1:** Raw filing text cached locally (avoid re-fetching EDGAR)
- **Layer 2:** Analysis results cached in SQLite (avoid re-running Claude)

Scoring a new company takes ~30 seconds. Re-scoring a cached company is instant.

---

## Tech Stack

- **Python** — Core pipeline
- **EDGAR API** — SEC filing retrieval (public, no key needed)
- **Claude AI** — Filing analysis and scoring
- **SQLite** — Two-layer caching

---

*Built by Justin Adair | Part of the Neo AI portfolio*
