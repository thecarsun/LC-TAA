#v4 

# v4 stable scrape + filters.json
# scrape_just_security_tracker.py

from __future__ import annotations

import csv
import json
import re
from typing import List, Dict, Tuple
import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# Your website table + the 4 filter fields (Issue & Executive Action are also table columns)
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


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def cell_text(td) -> str:
    # Keep multi-item cells readable (Filings often has multiple links)
    text = td.get_text(separator=" | ", strip=True)
    return clean_ws(text)


def find_tracker_table(soup: BeautifulSoup) -> Tuple[BeautifulSoup | None, List[str]]:
    # Find the table whose header row includes these key columns
    for table in soup.find_all("table"):
        ths = [clean_ws(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        if "Case Name" in ths and "Filings" in ths and "Date Case Filed" in ths:
            return table, ths
    return None, []


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

    # Map header -> column index
    idx = {h: i for i, h in enumerate(headers)}

    missing = [c for c in WANTED_COLS if c not in idx]
    if missing:
        raise RuntimeError(f"Expected columns not found in table header: {missing}\nFound: {headers}")

    rows_out: List[Dict[str, str]] = []
    tbody = table.find("tbody") or table

    for tr in tbody.find_all("tr"):
        tds = tr.find_all(["td", "th"])
        if not tds or len(tds) < len(headers):
            continue

        full_row = {h: cell_text(tds[i]) if i < len(tds) else "" for h, i in idx.items()}
        rows_out.append({col: full_row.get(col, "") for col in WANTED_COLS})

    return rows_out


def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=WANTED_COLS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def split_filter_values(field: str, value: str) -> List[str]:
    """
    Turn a scraped cell into filter tokens.
    - We used " | " as our separator, so split on that.
    - Also split on ';' and '/' which sometimes appear in multi-item cells.
    - For State A.G.'s we generally keep it as-is (often a single item).
    """
    value = clean_ws(value)
    if not value:
        return []

    if field == "State A.G.'s":
        return [value]  # don't split state names like "New York"

    parts = re.split(r"\s*\|\s*|\s*;\s*|\s*/\s*", value)
    parts = [p.strip() for p in parts if p.strip()]
    return parts


def build_filters(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    buckets: Dict[str, set] = {f: set() for f in FILTER_FIELDS}

    for r in rows:
        for f in FILTER_FIELDS:
            for token in split_filter_values(f, r.get(f, "")):
                buckets[f].add(token)

    # Stable order for dropdowns
    return {f: sorted(buckets[f]) for f in FILTER_FIELDS}


def write_filters_json(filters: Dict[str, List[str]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    rows = scrape()
    print(f"Scraped {len(rows)} rows")

    write_csv(rows, "cases.csv")
    print("Wrote cases.csv")

    filters = build_filters(rows)
    write_filters_json(filters, "filters.json")
    print("Wrote filters.json")
