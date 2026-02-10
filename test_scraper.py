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

for row in table_rows[1:4]:
    cells = row.find_all("td")
    if cells:
        case_name = cells[0].text.strip()
        status = cells[1].text.strip()
        print(case_name, "|", status)