#v2 scraper: fixed header and mapping issue

import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


TRACKER_URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"
HEADERS = {"User-Agent": "US Litigation Tracker Bot / GitHub: thecarsun"}
SOURCE = "Just Security"


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def _is_iso_date(s: str) -> bool:
    # Expect YYYY-MM-DD
    return bool(s) and len(s) == 10 and s[4] == "-" and s[7] == "-"


def _find_tracker_table(soup: BeautifulSoup):
    """
    Find the tracker table by looking for header keywords.
    This avoids accidentally scraping other tables on the page.
    """
    for table in soup.select("table"):
        header_cells = table.select("tr th")
        if not header_cells:
            continue
        headers = [_norm(h.get_text(" ", strip=True)) for h in header_cells]

        # Heuristics: the tracker table should have these concepts
        if any("filed" in h for h in headers) and any("status" in h for h in headers):
            return table, headers

    return None, []


def scrape_cases() -> list[dict]:
    r = requests.get(TRACKER_URL, headers=HEADERS, timeout=30)

    # GitHub Actions runners often get blocked (403). Exit cleanly.
    if r.status_code == 403:
        print("Skipped scrape: received 403 Forbidden (likely GitHub runner blocked).")
        sys.exit(0)

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    table, headers = _find_tracker_table(soup)
    if table is None:
        raise RuntimeError("Could not locate the tracker table (no matching headers found).")

    # Build header -> column index map
    col = {h: i for i, h in enumerate(headers)}

    def get_cell_text(cells, header_key: str) -> str:
        """
        Fetch cell text by header name. Returns "" if header not found.
        """
        idx = col.get(_norm(header_key))
        if idx is None or idx >= len(cells):
            return ""
        return cells[idx].get_text(" ", strip=True)

    scraped_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    cases: list[dict] = []

    # Prefer tbody rows if present
    rows = table.select("tbody tr") or table.select("tr")

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        # Filed date (header-based)
        filed_date = get_cell_text(cells, "filed date") or get_cell_text(cells, "filed")
        filed_date = filed_date.strip()
        if not _is_iso_date(filed_date):
            continue  # skip header-like/malformed rows

        # Case cell (usually first column)
        case_cell = cells[0]
        case_name_raw = case_cell.get_text(" ", strip=True)

        # Court is inside parentheses in the case cell (based on your observed pattern)
        m = re.search(r"\(([^)]+)\)", case_name_raw)
        court = m.group(1).strip() if m else ""

        # Remove "(court)" portion from displayed case name
        case_name = re.sub(r"\([^)]+\)", "", case_name_raw).strip()
        case_name = " ".join(case_name.split())  # normalize whitespace

        # URL inside case cell (CourtListener link typically)
        a = case_cell.find("a")
        case_url = a["href"] if a and a.has_attr("href") else ""
        if case_url.startswith("/"):
            case_url = "https://www.justsecurity.org" + case_url

        # Other fields (header-based)
        executive_action = get_cell_text(cells, "executive action")
        current_status = get_cell_text(cells, "case status") or get_cell_text(cells, "status")
        issue_main = get_cell_text(cells, "issue")
        issue_sub = get_cell_text(cells, "issue area")
        last_case_update_date = get_cell_text(cells, "last case update") or get_cell_text(
            cells, "last case update date"
        )

        issue_area = ", ".join([x for x in [issue_main, issue_sub] if x])

        # Normalize State AG Plaintiffs: treat as a tag, not an executive action
        state_ag_plaintiff = False
        ea = executive_action.strip().lower()
        if "state ag" in ea and "plaintiff" in ea:
            state_ag_plaintiff = True
            executive_action = ""

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
    data = scrape_cases()
    print(f"Extracted {len(data)} cases")
    for row in data[:3]:
        print(row)
