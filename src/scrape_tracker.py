#v6

from __future__ import annotations
import csv
import json
import re
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# Website table columns you want to show
CASES_CSV_COLS = [
    "Case Name",
    "Filings",
    "Date Case Filed",
    "State AGs",
    "Case Status",
    "Last Case Update",
]

# Filter dropdowns (top of page)
FILTER_FIELDS = ["State AGs", "Case Status", "Issue", "Executive Action"]


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def cell_text(td) -> str:
    # Keep multi-link filings readable
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
    """
    Returns raw row cells as a list of strings, preserving column index positions.
    This is the safest way since you've already verified which column index means what.
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

        # Convert cells to text
        row_cells = [cell_text(td) for td in tds]

        # Expecting at least 8 columns based on your printout (0..9 exist, but 0..7 are critical)
        if len(row_cells) < 8:
            continue

        rows.append(row_cells)

    # +1 header row on your print is expected; here we return only body rows (cases)
    return rows


def build_cases(rows: List[List[str]]) -> List[Dict[str, str]]:
    """
    Map the raw cells to the website table columns (what you want in cases.csv).
    Verified mapping from your debug output:
      0 Case Name
      1 Filings
      2 Date Case Filed
      3 State AGs
      4 Case Status
      7 Last Case Update (date)
    """
    cases: List[Dict[str, str]] = []
    for r in rows:
        cases.append({
            "Case Name": r[0],
            "Filings": r[1],
            "Date Case Filed": r[2],
            "State AGs": r[3] if r[3] else "—",
            "Case Status": r[4],
            "Last Case Update": r[7],
        })
    return cases


def normalize_issue(v: str) -> str:
    # Issue is intended to be a single category (site shows small set)
    v = clean_ws(v)
    if not v:
        return ""
    # If formatting introduces " | ", keep the first
    return v.split(" | ", 1)[0].strip()


def normalize_exec_action(v: str) -> str:
    # Based on your actual scrape: Column 6 is already a single label like "Accessibility"
    v = clean_ws(v)
    if not v:
        return ""
    return v.split(" | ", 1)[0].strip()


def build_filters(rows: List[List[str]]) -> Dict[str, List[str]]:
    """
    Verified mapping from your debug output:
      Issue           = col 5
      Executive Action= col 6
      State AGs       = col 3
      Case Status     = col 4
    """
    issues = set()
    exec_actions = set()
    state_ags = set()
    statuses = set()

    for r in rows:
        state_ags.add(r[3] if r[3] else "—")
        statuses.add(r[4])

        issue = normalize_issue(r[5])
        if issue:
            issues.add(issue)

        ea = normalize_exec_action(r[6])
        if ea:
            exec_actions.add(ea)

    # Remove empties if any
    state_ags.discard("")
    statuses.discard("")
    issues.discard("")
    exec_actions.discard("")

    return {
        "State AGs": sorted(state_ags),
        "Case Status": sorted(statuses),
        "Issue": sorted(issues),
        "Executive Action": sorted(exec_actions),
    }


def write_cases_csv(cases: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CASES_CSV_COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(cases)


def write_filters_json(filters: Dict[str, List[str]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


def main() -> None:
    raw_rows = scrape_rows()
    print(f"Found {len(raw_rows)} case rows (tbody)")

    cases = build_cases(raw_rows)
    write_cases_csv(cases, "cases.csv")
    print("Wrote cases.csv")

    filters = build_filters(raw_rows)
    write_filters_json(filters, "filters.json")
    print("Wrote filters.json")

    print("Filter option counts:")
    for k, v in filters.items():
        print(f" - {k}: {len(v)}")


if __name__ == "__main__":
    main()
