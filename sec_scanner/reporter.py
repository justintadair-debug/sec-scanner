"""Inject real data into report-template.html."""

import json
import os
import re
from datetime import date


def generate_report(results: list[dict], output_path: str, template_path: str | None = None) -> str:
    """Generate HTML report from analysis results.

    Args:
        results: list of analysis result dicts
        output_path: where to write the HTML file
        template_path: path to report-template.html (auto-detected if None)

    Returns:
        The output file path.
    """
    if template_path is None:
        # Look for template relative to this file, then in cwd
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "..", "report-template.html"),
            os.path.join(os.getcwd(), "report-template.html"),
        ]
        for c in candidates:
            if os.path.exists(c):
                template_path = c
                break
        else:
            raise FileNotFoundError("Could not find report-template.html")

    with open(template_path, "r") as f:
        html = f.read()

    # Sort results by score descending
    results = sorted(results, key=lambda r: r["score"], reverse=True)

    # Build the JS data array
    js_entries = []
    for r in results:
        entry = {
            "ticker": r["ticker"],
            "company": r["company"],
            "score": r["score"],
            "verdict": r["verdict"],
            "date": r["date"],
            "scores": r["scores"],
            "findings": r["findings"],
            "flags": r["flags"],
            "takeaway": r["takeaway"],
            "disclosure_style": r.get("disclosure_style", "standard"),
        }
        js_entries.append(entry)

    js_data = "const data = " + json.dumps(js_entries, indent=2) + ";"

    # Replace the hardcoded data array (use lambda to avoid re escape issues)
    html = re.sub(
        r"const data = \[.*?\];",
        lambda m: js_data,
        html,
        flags=re.DOTALL,
    )

    # Update summary stats
    total = len(results)
    genuine = sum(1 for r in results if r["score"] >= 60)
    washing = sum(1 for r in results if r["score"] < 40)
    top = results[0] if results else None

    # Update header meta
    today = date.today().strftime("%b %Y")
    html = re.sub(
        r'// 10-K Filing Analysis — \d+ Companies — \w+ \d+',
        f'// 10-K Filing Analysis — {total} Companies — {today}',
        html,
    )

    # Update summary stat values
    # Companies Scanned
    html = re.sub(
        r'(<span class="stat-label">Companies Scanned</span>\s*<span class="stat-value blue">)\d+(</span>)',
        rf'\g<1>{total}\2',
        html,
    )

    # Genuine Adopters
    html = re.sub(
        r'(<span class="stat-label">Genuine Adopters</span>\s*<span class="stat-value green">)\d+(</span>)',
        rf'\g<1>{genuine}\2',
        html,
    )

    # AI Washing Caught
    html = re.sub(
        r'(<span class="stat-label">AI Washing Caught</span>\s*<span class="stat-value red">)\d+(</span>)',
        rf'\g<1>{washing}\2',
        html,
    )

    # Top Score
    if top:
        html = re.sub(
            r'(<span class="stat-label">Top Score</span>\s*<span class="stat-value yellow">)\d+(</span>)',
            rf'\g<1>{top["score"]}\2',
            html,
        )
        html = re.sub(
            r'(<span class="stat-label">Top Score</span>\s*<span class="stat-value yellow">\d+</span>\s*<span class="stat-sub">).*?(</span>)',
            rf'\1{top["ticker"]} — {top["company"]}\2',
            html,
        )

    # Remove hardcoded analyst notes (they're specific to the sample data)
    # Replace with a generic note based on actual results
    if results:
        top_washer = [r for r in results if r["score"] < 40]
        top_genuine = [r for r in results if r["score"] >= 60]

        notes = []
        if top_genuine:
            best = top_genuine[0]
            notes.append(
                f'<p><strong>{best["ticker"]} — Top Scorer ({best["score"]}/100).</strong> '
                f'{best["takeaway"]}</p>'
            )
        if top_washer:
            worst = top_washer[-1]
            notes.append(
                f'<p><strong>{worst["ticker"]} — Lowest Score ({worst["score"]}/100).</strong> '
                f'{worst["takeaway"]}</p>'
            )

        notes_html = "\n    ".join(notes)
        html = re.sub(
            r'(<div class="analyst-note-header">.*?</div>)\s*<p>.*?(?=\s*</div>\s*<!--\s*Methodology)',
            rf'\1\n    {notes_html}\n  ',
            html,
            flags=re.DOTALL,
        )

    with open(output_path, "w") as f:
        f.write(html)

    return output_path
