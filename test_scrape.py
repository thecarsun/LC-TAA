# test_scrape.py
from playwright.sync_api import sync_playwright
import json
import time

URL = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/"

def get_page(browser):
    """Create a fresh page."""
    page = browser.new_page()
    return page

def load_url(page, retries=3):
    for attempt in range(retries):
        try:
            page.goto(URL, timeout=60000, wait_until="networkidle")
            page.wait_for_selector("#tablepress-42 tbody tr", timeout=30000)
            page.wait_for_timeout(2000)
            return True
        except Exception as e:
            print(f"    Retry {attempt+1}: {e}")
            time.sleep(3)
    return False

def get_exec_action_options(page):
    options = page.evaluate("""
        () => Array.from(document.querySelector('select.widget-6').options)
                   .map(o => o.value)
                   .filter(v => v !== '')
    """)
    return options

def scrape_exec_action(browser, exec_action):
    page = browser.new_page()
    try:
        if not load_url(page):
            return {}
        page.select_option("select.widget-6", value=exec_action)
        page.wait_for_timeout(3000)
        data_rows = page.query_selector_all("#tablepress-42 tbody tr:has(td)")
        result = {}
        for row in data_rows:
            tds = row.query_selector_all("td")
            if len(tds) < 6:
                continue
            name = tds[0].inner_text().strip()
            result[name] = exec_action
        return result
    except Exception as e:
        print(f"    Error: {e}")
        return {}
    finally:
        page.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Get options
    page = browser.new_page()
    load_url(page)
    exec_options = get_exec_action_options(page)
    page.close()
    print(f"Found {len(exec_options)} executive actions")

    # Load any previously saved progress
    try:
        with open("exec_map.json", "r", encoding="utf-8") as f:
            exec_map = json.load(f)
        print(f"Resuming from saved progress ({len(exec_map)} cases already mapped)")
    except FileNotFoundError:
        exec_map = {}

    for i, ea in enumerate(exec_options):
        # Skip already-processed options
        if ea in exec_map.values():
            print(f"[{i+1}/{len(exec_options)}] SKIP (already done): {ea[:60]}")
            continue

        print(f"[{i+1}/{len(exec_options)}] {ea[:60]}")
        result = scrape_exec_action(browser, ea)
        print(f"  -> {len(result)} rows")
        exec_map.update(result)

        # Save progress after every option
        with open("exec_map.json", "w", encoding="utf-8") as f:
            json.dump(exec_map, f, ensure_ascii=False, indent=2)

    browser.close()

print(f"\nDone. Total mapped: {len(exec_map)}")