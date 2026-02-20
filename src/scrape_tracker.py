#v8
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Dict, List

from playwright.sync_api import sync_playwright

URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

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

ISSUE_OPTIONS = [
    "Civil Liberties and Rights",
    "Diversity, Equity, Inclusion, and Accessibility",
    "Environment",
    "Federalism",
    "Government Grants, Loans, and Assistance",
    "Immigration and Citizenship",
    "International Institutions",
    "Miscellaneous",
    "Removal of Information from Government Websites",
    "Structure of Government/Personnel",
    "Trade Law",
    "Transparency",
]


def load_page(browser):
    page = browser.new_page()
    for attempt in range(3):
        try:
            page.goto(URL, timeout=60000, wait_until="networkidle")
            page.wait_for_selector("#tablepress-42 tbody tr", timeout=30000)
            page.wait_for_timeout(2000)
            return page
        except Exception as e:
            print(f"  Retry {attempt + 1}: {e}")
            time.sleep(3)
    raise RuntimeError("Failed to load page after 3 attempts.")


def get_exec_action_options(browser) -> List[str]:
    page = load_page(browser)
    options = page.evaluate("""
        () => Array.from(document.querySelector('select.widget-6').options)
                   .map(o => o.value)
                   .filter(v => v !== '')
    """)
    page.close()
    return options


def scrape_by_filter(browser, select_class: str, value: str) -> Dict[str, str]:
    """Scrape case_name -> value mapping for a given filter."""
    page = load_page(browser)
    try:
        page.select_option(f"select.{select_class}", value=value)
        page.wait_for_timeout(3000)
        rows = page.query_selector_all("#tablepress-42 tbody tr:has(td)")
        result = {}
        for row in rows:
            tds = row.query_selector_all("td")
            if len(tds) < 6:
                continue
            result[tds[0].inner_text().strip()] = value
        return result
    except Exception as e:
        print(f"  Error scraping '{value}': {e}")
        return {}
    finally:
        page.close()


def scrape_issue_map(browser) -> Dict[str, str]:
    """Returns case_name -> issue_area for all 653 cases."""
    issue_map = {}
    for i, issue in enumerate(ISSUE_OPTIONS):
        print(f"[{i+1}/{len(ISSUE_OPTIONS)}] Issue: {issue[:60]}")
        result = scrape_by_filter(browser, "widget-5", issue)
        print(f"  -> {len(result)} rows")
        issue_map.update(result)
    return issue_map


def scrape_exec_map(browser) -> Dict[str, str]:
    """Returns case_name -> executive_action for all 653 cases."""
    exec_options = get_exec_action_options(browser)
    print(f"Found {len(exec_options)} executive actions")

    exec_map = {}
    for i, ea in enumerate(exec_options):
        print(f"[{i+1}/{len(exec_options)}] Exec: {ea[:60]}")
        result = scrape_by_filter(browser, "widget-6", ea)
        print(f"  -> {len(result)} rows")
        exec_map.update(result)

        # Save progress after each option
        with open("exec_map_progress.json", "w", encoding="utf-8") as f:
            json.dump(exec_map, f, ensure_ascii=False, indent=2)

    return exec_map


def scrape_all_cases(browser, issue_map: Dict[str, str]) -> List[Dict[str, str]]:
    """Scrape full row data using unfiltered table, tag with issue_map."""
    page = load_page(browser)
    try:
        rows = page.query_selector_all("#tablepress-42 tbody tr:has(td)")
        print(f"Total unfiltered rows: {len(rows)}")
        cases = []
        for row in rows:
            tds = row.query_selector_all("td")
            if len(tds) < 6:
                continue
            name = tds[0].inner_text().strip()
            cases.append({
                "case_name":        name,
                "filings":          tds[1].inner_text().strip(),
                "filed_date":       tds[2].inner_text().strip(),
                "state_ags":        tds[3].inner_text().strip() or "—",
                "case_status":      tds[4].inner_text().strip(),
                "last_case_update": tds[5].inner_text().strip(),
                "issue_area":       issue_map.get(name, ""),
                "executive_action": "",  # filled in after
            })
        return cases
    finally:
        page.close()


def write_cases_csv(cases: List[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CASES_CSV_COLS)
        w.writeheader()
        w.writerows(cases)


def write_filters_json(cases: List[Dict], path: Path) -> None:
    filters = {
        "State AGs":        sorted({c["state_ags"] for c in cases if c["state_ags"]}),
        "Case Status":      sorted({c["case_status"] for c in cases if c["case_status"]}),
        "Issue":            sorted({c["issue_area"] for c in cases if c["issue_area"]}),
        "Executive Action": sorted({c["executive_action"] for c in cases if c["executive_action"]}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)


def main():
    base = Path(__file__).parent.parent
    cases_path = base / "data" / "processed" / "cases.csv"
    filters_path = base / "data" / "processed" / "filters.json"

    # TEMP DEBUG
    print(f"base: {base}")
    print(f"cases_path: {cases_path}")
    print(f"cases_path exists: {cases_path.exists()}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        print("=== Step 1: Scraping issue areas ===")
        issue_map = scrape_issue_map(browser)
        print(f"Issue map: {len(issue_map)} cases\n")

        print("=== Step 2: Scraping executive actions ===")
        exec_map = scrape_exec_map(browser)
        print(f"Exec map: {len(exec_map)} cases\n")

        print("=== Step 3: Scraping full case data ===")
        cases = scrape_all_cases(browser, issue_map)

        browser.close()

    # Merge executive_action into cases
    for case in cases:
        case["executive_action"] = exec_map.get(case["case_name"], "")

    print(f"Total cases: {len(cases)}")

    write_cases_csv(cases, cases_path)
    print(f"Wrote {cases_path}")

    write_filters_json(cases, filters_path)
    print(f"Wrote {filters_path}")

    # Clean up temp file
    Path("exec_map_progress.json").unlink(missing_ok=True)
    print("Done.")


if __name__ == "__main__":
    main()