# v7 scrape_tracker.py
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import List, Dict

from playwright.sync_api import sync_playwright

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

CASES_CSV_COLS = [
    "case_name",
    "filings",
    "filed_date",
    "state_ags",
    "case_status",
    "issue_area",
    "executive_action",
    "last_case_update",
]


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def scrape_rows() -> List[List[str]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading page...")
        page.goto(TRACKER_URL, timeout=60000, wait_until="networkidle")

        # Wait for the table to appear
        print("Waiting for table...")
        page.wait_for_selector("table", timeout=30000)

        # Give JS a moment to fully populate rows
        page.wait_for_timeout(3000)

        rows = []
        table = page.query_selector("table")
        if not table:
            raise RuntimeError("No table found after JS load.")

        tbody = table.query_selector("tbody")
        if not tbody:
            raise RuntimeError("Table has no tbody.")

        trs = tbody.query_selector_all("tr")
        print(f"Found {len(trs)} rows in tbody")

        for tr in trs:
            tds = tr.query_selector_all("td")
            if len(tds) < 8:
                continue
            cells = [clean_ws(td.inner_text()) for td in tds]
            rows.append(cells)

        browser.close()
    return rows


def normalize(v: str) -> str:
    v = clean_ws(v)
    return v.split("\n")[0].strip() if v else ""


def build_cases(rows: List[List[str]]) -> List[Dict[str, str]]:
    out = []
    for r in rows:
        out.append({
            "case_name": r[0],
            "filings": r[1],
            "filed_date": r[2],
            "state_ags": r[3] if r[3] else "—",
            "case_status": r[4],
            "issue_area": normalize(r[5]),
            "executive_action": normalize(r[6]),
            "last_case_update": r[7],
        })
    return out


def write_cases_csv(cases, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CASES_CSV_COLS)
        w.writeheader()
        w.writerows(cases)


def build_filters(cases) -> Dict[str, List[str]]:
    return {
        "State AGs": sorted({c["state_ags"] for c in cases if c["state_ags"]}),
        "Case Status": sorted({c["case_status"] for c in cases if c["case_status"]}),
        "Issue": sorted({c["issue_area"] for c in cases if c["issue_area"]}),
        "Executive Action": sorted({c["executive_action"] for c in cases if c["executive_action"]}),
    }


def main():
    rows = scrape_rows()
    print(f"Scraped {len(rows)} rows")

    cases = build_cases(rows)

    base = Path(__file__).parent.parent  # go up from src/
    write_cases_csv(cases, base / "data" / "processed" / "cases.csv")

    filters = build_filters(cases)
    filters_path = base / "data" / "processed" / "filters.json"
    filters_path.parent.mkdir(parents=True, exist_ok=True)
    with open(filters_path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

    print("Done.")


if __name__ == "__main__":
    main()
```
