# single test scraper
# goal: confirm if I can extract just 1 row of data from the tracker as intended

import re
import requests
from bs4 import BeautifulSoup

url = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/" 
headers = {"User-Agent": "US Litigation Tracker Bot / GitHub: thecarsun"}

r = requests.get(url, headers=headers, timeout =30)
r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

table_rows = soup.select("table tr")
print(f"Found {len(table_rows)} rows")

for row in table_rows:
    cells = row.find_all("td")
    if not cells:
        continue

    # --- skip header ---
    filed_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""

    # --- skip empty or non-date ---
    
    if filed_date == "" or filed_date.lower() == "filed" or filed_date.startswith("Filed"):
        continue
    if len(filed_date) != 10 or filed_date[4] != "-" or filed_date[7] != "-":
        continue

  # --- Extract URL from column 0 (if present) ---
    case_cell = cells[0]
    a = case_cell.find("a")
    case_url = a["href"] if a and a.has_attr("href") else ""
    if case_url.startswith("/"):
        case_url = "https://www.justsecurity.org" + case_url

    # --- Extract court from parentheses in column 0 ---
    case_name_raw = case_cell.get_text(" ", strip=True)

    m = re.search(r"\(([^)]+)\)", case_name_raw)
    court = m.group(1).strip() if m else ""
    
    # Remove court parentheses from case name (keep docket for now)
    case_name = re.sub(r"\([^)]+\)", "", case_name_raw).strip()
    case_name = " ".join(case_name.split())

    print("---- FIRST REAL CASE ROW ----")
    print("Parsed fields:")
    print("case_name_raw:", case_name_raw)
    print("case_name:", case_name)
    print("court:", court)
    print("filed_date:", filed_date)
    print("case_url:", case_url if case_url else "(no link found)")

    print("\nColumns (truncated):")
    for i, cell in enumerate(cells):
        text = cell.get_text(" ", strip=True)
        print(f"Column {i}: {text[:120]}{'...' if len(text) > 120 else ''}")

    break 

else: 
     print("No valid case rows found (all rows looked like headers/malformed).")
     