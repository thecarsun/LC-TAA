# single test scraper
# goal: confirm if I can extract just 1 row of data from the tracker as intended

import requests
from bs4 import BeautifulSoup

url = "https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/" 
headers = {"User-Agent": "US Litigation Tracker Bot / GitHub: thecarsun"}

r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

table_rows = soup.select("table tr")
print(f"Found {len(table_rows)} rows")

for row in table_rows:
    cells = row.find_all("td")
    if not cells:
        continue

    print("---- NEW ROW ----")

    for i, cell in enumerate(cells):
        print(f"Column {i}: {cell.get_text(strip=True)}")

    break  # Only inspect the first real row