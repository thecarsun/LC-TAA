# scrape_just_security_tracker.py
# v5.3 — CLEAN (no duplicate functions), stable table parse, site-aligned filters

from __future__ import annotations

import csv
import json
import re
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

WANTED_COLS = [
    "Case Name",
    "Filings",
    "Date Case Filed",
    "State A.G.'s",
    "Case Status",
    "Issue",
    "Executive Action",
    "Last Case Update",
]

FILTER_FIELDS = ["State A.G.'s", "Case Status", "Issue", "Executive Action"]


# ---------------- helpers ----------------

def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def cell_text(td) -> str:
    # Keep multi-item cells readable (Filings often has multiple links)
    return clean_ws(td.get_text(separator=" | ", strip=True))


def find_tracker_table(soup: BeautifulSoup) -> Tuple[BeautifulSoup | None, List[str]]:
    # Find the table whose THEAD header row contains key columns
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


# ---------------- scrape ----------------

def scrape() -> List[Dict[str, str]]:
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
        raise RuntimeError("Could not find the tracker table on the page (table structure may have changed).")

    idx = {h: i for i, h in enumerate(headers)}
    missing = [c for c in WANTED_COLS if c not in idx]
    if missing:
        raise RuntimeError(f"Expected columns not found in table header: {missing}\nFound headers: {headers}")

    tbody = table.find("tbody")
    if not tbody:
        raise RuntimeError("Tracker table has no <tbody> (structure may have changed).")

    rows_out: List[Dict[str, str]] = []

    # Use only direct td children to remember true column alignment
    for tr in tbody.find_all("tr", recursive=False):
        tds = tr.find_all("td", recursive=False)

        # If the row doesn't match header length, skip it (prevents misalignment pollution)
        if len(tds) != len(headers):
            continue

        full_row = {headers[i]: cell_text(tds[i]) for i in range(len(headers))}
        rows_out.append({col: full_row.get(col, "") for col in WANTED_COLS})

    return rows_out


# ---------------- outputs ----------------

def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=WANTED_COLS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def write_filters_json(filters: Dict[str, List[str]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


# ---------------- filter normalization ----------------

def normalize_state_ag(value: str) -> str:
    v = clean_ws(value)
    if not v:
        return "—"
    if v.lower() == "state a.g. plaintiffs":
        return "State A.G. Plaintiffs"
    return v


def normalize_issue(value: str) -> str:
    # Match the site's small Issue set: keep top-level label only
    v = clean_ws(value)
    if not v:
        return ""
    if " | " in v:
        v = v.split(" | ", 1)[0].strip()
    return v


def normalize_exec_action(value: str) -> str:
    # Match the site's dropdown more closely: top-level category before parentheses
    v = clean_ws(value)
    if not v:
        return ""
    head = v.split("(", 1)[0].strip()
    return head if head else v


def split_filter_values(field: str, value: str) -> List[str]:
    v = clean_ws(value)
    if field == "State A.G.'s":
        return [normalize_state_ag(v)]

    if not v:
        return []

    if field == "Issue":
        x = normalize_issue(v)
        return [x] if x else []

    if field == "Case Status":
        return [v]  # keep as-is (slashes '/' are meaningful)

    if field == "Executive Action":
        x = normalize_exec_action(v)
        return [x] if x else []

    return [v]


def build_filters(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    buckets: Dict[str, set] = {f: set() for f in FILTER_FIELDS}

    for r in rows:
        for f in FILTER_FIELDS:
            for token in split_filter_values(f, r.get(f, "")):
                buckets[f].add(token)

    return {f: sorted(buckets[f]) for f in FILTER_FIELDS}


# ---------------- main ----------------

def main() -> None:
    rows = scrape()
    write_csv(rows, "cases.csv")

    filters = build_filters(rows)
    write_filters_json(filters, "filters.json")

    # Debug: confirm you're close to the site's totals (650 is currently stated on the page)
    print(f"Rows scraped: {len(rows)}")
    print("Filter option counts:")
    for k in FILTER_FIELDS:
        print(f" - {k}: {len(filters.get(k, []))}")

    # Helpful peek
    print("\nFirst 15 Issue options:")
    for x in filters.get("Issue", [])[:15]:
        print(" -", x)

    print("\nFirst 15 Executive Action options:")
    for x in filters.get("Executive Action", [])[:15]:
        print(" -", x)


if __name__ == "__main__":
    main()
