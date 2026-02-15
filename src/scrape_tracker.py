#scraper that returns list of dicts that match my CSV header setup

import re
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"
HEADERS = {"User-Agent": "US Litigation Tracker Bot / GitHub: thecarsun"}
SOURCE = "Just Security"


def _is_iso_date(s: str) -> bool:
    # Expect YYYY-MM-DD
    return bool(s) and len(s) == 10 and s[4] == "-" and s[7] == "-"


def scrape_cases() -> list[dict]:
    r = requests.get(TRACKER_URL, headers=HEADERS, timeout=30)

    # If running on GitHub Actions and site blocks it

    if r.status_code == 403:
        print("Skipped scrape: received 403 Forbidden (likely GitHub runner blocked).")
        sys.exit(0)

    r.raise_for_status()


    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("table tr")

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    cases: list[dict] = []

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        # Expect filed_date in col 2
        filed_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        if not _is_iso_date(filed_date):
            continue  # skip header-like rows / malformed rows

        # Column 0: case name + (court) + docket, plus link
        case_cell = cells[0]
        case_name_raw = case_cell.get_text(" ", strip=True)

        m = re.search(r"\(([^)]+)\)", case_name_raw)
        court = m.group(1).strip() if m else ""

        case_name = re.sub(r"\([^)]+\)", "", case_name_raw).strip()
        case_name = " ".join(case_name.split())  # normalize whitespace

        a = case_cell.find("a")
        case_url = a["href"] if a and a.has_attr("href") else ""
        if case_url.startswith("/"):
            case_url = "https://www.justsecurity.org" + case_url

        # Column mapping from your discovery
        executive_action = cells[3].get_text(" ", strip=True) if len(cells) > 3 else ""
        current_status = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""
        issue_main = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""
        issue_sub = cells[6].get_text(" ", strip=True) if len(cells) > 6 else ""
        last_case_update_date = cells[7].get_text(" ", strip=True) if len(cells) > 7 else ""

        issue_area = ", ".join([x for x in [issue_main, issue_sub] if x])

        # v1: Normalize: "state ag plaintiffs" default false, treat as tag
        state_ag_plaintiff = False
        if executive_action.strip().lower() == "state ag plaintiffs":
            state_ag_plaintiff = True
            executive_action = ""

        cases.append(
            {
                "case_name": case_name,
                "court": court,
                "filed_date": filed_date,
                "last_case_update_date": last_case_update_date,
                "current_status": current_status,
                "state_ag_plaintiff": "false",
                "issue_area": issue_area,
                "executive_action": executive_action,
                "case_url": case_url,
                "source": Just Security,
                "scraped_at": scraped_at,
            }
        )

    return cases


if __name__ == "__main__":
    data = scrape_cases()
    print(f"Extracted {len(data)} cases")
    # Print a few samples
    for row in data[:3]:
        print(row)
