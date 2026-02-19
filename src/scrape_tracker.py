from __future__ import annotations
import csv
import json
import re
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# CSV columns must match the dict keys you write
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

FILTER_FIELDS = ["State AGs", "Case Status", "Issue", "Executive Action"]


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def cell_text(td) -> str:
    return clean_ws(td.get_text(separator=" | ", strip=True))


def find_tracker_table(soup: BeautifulSoup) -> Tuple[Beau
                                                     tifulSoup | None, List[str]]:
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
    table, _headers = find_tracker_table(soup)
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


def build_filters(rows: List[List[str]]) -> Dict[str, List[str]]:
    state_ags, statuses, issues, exec_actions = set(), set(), set(), set()

    for r in rows:
        if len(r) < 7:
            continue

        state_ags.add(r[3].strip() if r[3].strip() else "—")

        status = r[4].strip()
        if status:
            statuses.add(status)

        issue = normalize_issue(r[5])
        if issue:
            issues.add(issue)

        ea = normalize_exec_action(r[6])
        if ea:
            exec_actions.add(ea)

    return {
        "State AGs": sorted(state_ags),
        "Case Status": sorted(statuses),
        "Issue": sorted(issues),
        "Executive Action": sorted(exec_actions),
    }

def write_cases_csv(cases, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
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
