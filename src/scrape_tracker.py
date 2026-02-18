# v3 scraper 

import re
import sys
from datetime import datetime, timezone
from collections import Counter

import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"
HEADERS = {"User-Agent": "US Litigation Tracker Bot / GitHub: thecarsun"}
SOURCE = "Just Security"


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def _is_iso_date(s: str) -> bool:
    return bool(s) and len(s) == 10 and s[4] == "-" and s[7] == "-"


def _find_tracker_table(soup: BeautifulSoup):
    """
    Find the main litigation tracker table by looking for expected headers.
    """
    for table in soup.select("table"):
        ths = table.select("tr th")
        if not ths:
            continue
        header_text = [_norm(th.get_text(" ", strip=True)) for th in ths]
        if any("filed" in h for h in header_text) and any("status" in h for h in header_text):
            return table
    return None


def scrape_cases(debug: bool = False) -> list[dict]:
    r = requests.get(TRACKER_URL, headers=HEADERS, timeout=30)

    # GitHub-hosted runners 403 blocked
    if r.status_code == 403:
        print("Skipped scrape: received 403 Forbidden (GitHub runner blocked).")
        sys.exit(0)

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    table = _find_tracker_table(soup)
    if table is None:
        raise RuntimeError("Could not locate the tracker table.")

    rows = table.select("tbody tr") or table.select("tr")

    # Determine the most common td length and skip weird rows (prevents mis-mapping)
    lengths = [len(row.find_all("td")) for row in rows if row.find_all("td")]
    if not lengths:
        return []

    expected_len = Counter(lengths).most_common(1)[0][0]
    if debug:
        print("Most common td lengths:", Counter(lengths).most_common(5))
        print("Expected td length:", expected_len)

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    cases: list[dict] = []

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        if len(cells) != expected_len:
            if debug:
                first = cells[0].get_text(" ", strip=True)[:120] if cells else ""
                print(f"Skipping odd row (td={len(cells)}): {first}")
            continue

        # --- Column positions (stable for "normal" rows)
        # 0 case, 1 filing, 2 filed date, 3 state ag's, 4 status, 5 issue, 6 issue2, 7 exec action, 8 last update, 9 summary, 10 updates...
        # BUT your earlier runs showed 10-ish columns; we only use the first 9 safely.

        case_cell = cells[0]
        case_name_raw = case_cell.get_text(" ", strip=True)

        # Court inside parentheses in case cell
        m = re.search(r"\(([^)]+)\)", case_name_raw)
        court = m.group(1).strip() if m else ""

        # Remove "(court)" portion but keep docket
        case_name = re.sub(r"\([^)]+\)", "", case_name_raw).strip()
        case_name = " ".join(case_name.split())

        # Case URL is usually CourtListener link in the case cell
        a = case_cell.find("a")
        case_url = a["href"] if a and a.has_attr("href") else ""
        if case_url.startswith("/"):
            case_url = "https://www.justsecurity.org" + case_url

        filed_date = cells[2].get_text(" ", strip=True) if len(cells) > 2 else ""
        if not _is_iso_date(filed_date):
            continue

        # STATE AG column (string; may be blank)
        state_ag = cells[3].get_text(" ", strip=True) if len(cells) > 3 else ""

        # Case Status
        current_status = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""

        # Issue is two columns in practice
        issue_main = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""
        issue_sub = cells[6].get_text(" ", strip=True) if len(cells) > 6 else ""
        issue_area = ", ".join([x for x in [issue_main, issue_sub] if x])

        # Executive Action
        executive_action = cells[7].get_text(" ", strip=True) if len(cells) > 7 else ""

        # Last Case Update date
        last_case_update_date = cells[8].get_text(" ", strip=True) if len(cells) > 8 else ""

        # --- Normalize State AG Plaintiffs
        # 1) If exec action cell contains "State AG Plaintiffs", treat as tag
        state_ag_plaintiff = False
        ea = executive_action.strip().lower()
        if "state ag" in ea and "plaintiff" in ea:
            state_ag_plaintiff = True
            executive_action = ""

        # 2) If the State AG column is populated, it likely indicates AG involvement
        # (You can tighten this later if needed.)
        if state_ag.strip():
            state_ag_plaintiff = True

        cases.append(
            {
                "case_name": case_name,
                "court": court,
                "filed_date": filed_date,
                "last_case_update_date": last_case_update_date,
                "current_status": current_status,
                "state_ag_plaintiff": str(state_ag_plaintiff).lower(),
                "issue_area": issue_area,
                "executive_action": executive_action,
                "case_url": case_url,
                "source": SOURCE,
                "scraped_at": scraped_at,
            }
        )

    return cases


if __name__ == "__main__":
    data = scrape_cases(debug=True)
    print(f"Extracted {len(data)} cases")
    for row in data[:3]:
        print(row)
