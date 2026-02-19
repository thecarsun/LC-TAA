from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# Final CSV schema (what app.py expects)
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

def cell_text(td) -> str:
    return clean_ws(td.get_text(separator=" | ", strip=True))

def find_tracker_table(soup: BeautifulSoup) -> Tuple[BeautifulSoup | None, List[str]]:
    for table in soup.find_all("table"):
        thead = table.find("thead")
        if not thead:
            continue
        header_tr = thead.find("tr")
        if not header_tr:
            continue

        headers = [clean_ws(th.get_text(" ", strip=True)) for th in header_tr.find_all("th", recursive=False)]
        if "Case Name" in headers and "Filings" in headers and "Date Case Filed" in headers:
            return table, headers

    return None, []

def scrape_rows() -> List[List[str]]:
    resp = requests.get(
        TRACKER_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LitigationTrackerBot/1.0)",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=30,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table, headers = find_tracker_table(soup)
    if table is None:
        raise RuntimeError("Could not find tracker table (page structure may have changed).")

    tbody = table.find("tbody")
    if not tbody:
        raise RuntimeError("Tracker table has no <tbody> (page structure may have changed).")

    rows: List[List[str]] = []
    for tr in tbody.find_all("tr", recursive=False):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue

        row_cells = [cell_text(td) for td in tds]
        # Expect at least 8 cols: 0..7 are what we need
        if len(row_cells) < 8:
            continue

        rows.append(row_cells)

    return rows

def normalize_issue(v: str) -> str:
    v = clean_ws(v)
    if not v:
        return ""
    return v.split(" | ", 1)[0].strip()

def normalize_exec_action(v: str) -> str:
    v = clean_ws(v)
    if not v:
        return ""
    return v.split(" | ", 1)[0].strip()

def build_cases(rows: List[List[str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for r in rows:
        out.append({
            "case_name": r[0],
            "filings": r[1],
            "filed_date": r[2],
            "state_ags": r[3] if r[3] else "—",
            "case_status": r[4],
            "issue_area": normalize_issue(r[5]),
            "executive_action": normalize_exec_action(r[6]),
            "last_case_update": r[7],
        })
    return out

def build_filters_from_cases(cases: List[Dict[str, str]]) -> Dict[str, List[str]]:
    return {
        "State AGs": sorted({c["state_ags"] for c in cases if c.get("state_ags")}),
        "Case Status": sorted({c["case_status"] for c in cases if c.get("case_status")}),
        "Issue": sorted({c["issue_area"] for c in cases if c.get("issue_area")}),
        "Executive Action": sorted({c["executive_action"] for c in cases if c.get("executive_action")}),
    }

def write_cases_csv(cases: List[Dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CASES_CSV_COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(cases)

def write_filters_json(filters: Dict[str, List[str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

def main() -> None:
    raw_rows = scrape_rows()
    print(f"Found {len(raw_rows)} case rows (tbody)")

    cases = build_cases(raw_rows)

    cases_path = Path("data/processed/cases.csv")
    filters_path = Path("data/processed/filters.json")

    write_cases_csv(cases, cases_path)
    print(f"Wrote {cases_path}")

    filters = build_filters_from_cases(cases)
    write_filters_json(filters, filters_path)
    print(f"Wrote {filters_path}")

    print("Filter option counts:")
    for k, v in filters.items():
        print(f" - {k}: {len(v)}")

if __name__ == "__main__":
    main()