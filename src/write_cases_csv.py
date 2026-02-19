from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# CSV schema - matching what i have in app.py
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
    # Keep multiple links readable
    return clean_ws(td.get_text(separator=" | ", strip=True))

def find_tracker_table(soup: BeautifulSoup) -> Tuple[BeautifulSoup | None, List[str]]:
    """
    Locate the tracker table by looking for a THEAD that includes
    "Case Name", "Filings", and "Date Case Filed".
    """
    for table in soup.find_all("table"):
        thead = table.find("thead")
        if not thead:
            continue

        header_tr = thead.find("tr")
        if not header_tr:
            continue

        headers = [
            clean_ws(th.get_text(" ", strip=True))
            for th in header_tr.find_all("th", recursive=False)
        ]

        if "Case Name" in headers and "Filings" in headers and "Date Case Filed" in headers:
            return table, headers

    return None, []

def scrape_rows() -> List[List[str]]:
    """
    Scrape the raw cell text rows from the tracker table.

    Column index mapping (based on your earlier debug):
      0 = Case Name
      1 = Filings
      2 = Date Case Filed
      3 = State AGs
      4 = Case Status
      5 = Issue
      6 = Executive Action
      7 = Last Case Update
      (8, 9 = summaries, which we're not using right now)
    """
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

        # We expect at least 8 columns (0..7 are required for our schema)
        if len(row_cells) < 8:
            continue

        rows.append(row_cells)

    return rows

def normalize_issue(v: str) -> str:
    """
    Issue should be a single top-level category.
    If formatting introduces separators like ' | ', keep only the first part.
    """
    v = clean_ws(v)
    if not v:
        return ""
    return v.split(" | ", 1)[0].strip()

def normalize_exec_action(v: str) -> str:
    """
    Executive Action: keep the top-level label, trimming anything that comes
    after ' | ' if present.
    """
    v = clean_ws(v)
    if not v:
        return ""
    return v.split(" | ", 1)[0].strip()

def build_cases(rows: List[List[str]]) -> List[Dict[str, str]]:
    """
    Convert raw scraped rows into a list of dicts matching CASES_CSV_COLS.
    """
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
    """
    Build filter option lists directly from the normalized cases.
    This keeps filters aligned with what app.py uses:
      - state_ags
      - case_status
      - issue_area
      - executive_action
    """
    state_ags = {c["state_ags"] for c in cases if c.get("state_ags")}
    statuses = {c["case_status"] for c in cases if c.get("case_status")}
    issues = {c["issue_area"] for c in cases if c.get("issue_area")}
    exec_actions = {c["executive_action"] for c in cases if c.get("executive_action")}

    return {
        "State AGs": sorted(state_ags),
        "Case Status": sorted(statuses),
        "Issue": sorted(issues),
        "Executive Action": sorted(exec_actions),
    }

def write_cases_csv(cases: List[Dict[str, str]], path: Path) -> None:
    """
    Write the normalized cases to data/processed/cases.csv in UTF-8.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CASES_CSV_COLS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(cases)

def write_filters_json(filters: Dict[str, List[str]], path: Path) -> None:
    """
    Write filter options to data/processed/filters.json in UTF-8.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

def main() -> None:
    raw_rows = scrape_rows()
    print(f"Found {len(raw_rows)} case rows (tbody)")

    cases = build_cases(raw_rows)

    base_dir = Path(__file__).parent
    cases_path = base_dir / "data" / "processed" / "cases.csv"
    filters_path = base_dir / "data" / "processed" / "filters.json"

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