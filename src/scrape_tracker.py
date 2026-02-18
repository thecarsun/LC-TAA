# v5 — stable scrape + site-aligned filters + cases.csv + filters.json
# scrape_just_security_tracker.py

from __future__ import annotations

import csv
import json
import re
from typing import List, Dict, Tuple

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

# Website table + filter fields
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


# ---------- text helpers ----------

def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def cell_text(td) -> str:
    # Keep multi-item cells readable (Filings often has multiple links)
    text = td.get_text(separator=" | ", strip=True)
    return clean_ws(text)


# ---------- table discovery ----------

def find_tracker_table(soup: BeautifulSoup) -> Tuple[BeautifulSoup | None, List[str]]:
    """
    Finds the tracker table by looking for a header row containing key columns.
    Returns (table, headers_as_text).
    """
    for table in soup.find_all("table"):
        ths = [clean_ws(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        if "Case Name" in ths and "Filings" in ths and "Date Case Filed" in ths:
            return table, ths
    return None, []


# ---------- scrape ----------

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
        raise RuntimeError(f"Expected columns not found in table header: {missing}\nFound headers: {headers}")

    rows_out: List[Dict[str, str]] = []
    tbody = table.find("tbody") or table

    for tr in tbody.find_all("tr"):
        tds = tr.find_all(["td", "th"])
        if not tds or len(tds) < len(headers):
            continue

        # Build a full row keyed by *actual* header names
        full_row = {h: cell_text(tds[i]) if i < len(tds) else "" for h, i in idx.items()}

        # Emit only the columns we care about, in our chosen order
        rows_out.append({col: full_row.get(col, "") for col in WANTED_COLS})

    return rows_out


# ---------- outputs ----------

def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=WANTED_COLS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def write_filters_json(filters: Dict[str, List[str]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


# ---------- filter logic (site-aligned) ----------

def normalize_state_ag(value: str) -> str:
    """
    The site’s 'State A.G.'s' column often behaves like a flag (e.g., 'State A.G. Plaintiffs'),
    so normalize empties + casing.
    """
    v = clean_ws(value)
    if not v:
        return "—"
    if v.lower() == "state a.g. plaintiffs":
        return "State A.G. Plaintiffs"
    return v


def split_filter_values(field: str, value: str) -> List[str]:
    """
    IMPORTANT behavior:
    - NEVER split Issue or Case Status (slashes '/' are part of real labels)
    - ONLY split Executive Action (can be multi-valued)
    - Normalize State A.G.'s into stable buckets
    """
    v = clean_ws(value)

    if field == "State A.G.'s":
        return [normalize_state_ag(v)]

    if not v:
        return []

    # Keep as single labels (do not split on '/')
    if field in ("Case Status", "Issue"):
        return [v]

    # Executive Action: split on our scraped separator and semicolons.
    # (Do NOT split on '/' unless you confirm the site uses '/' as a delimiter there.)
    if field == "Executive Action":
        parts = re.split(r"\s*\|\s*|\s*;\s*", v)
        return [p.strip() for p in parts if p.strip()]

    return [v]


def build_filters(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
