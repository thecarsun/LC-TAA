
import csv
from pathlib import Path
from scrape_tracker import scrape_cases

OUT_PATH = Path("data/processed/cases.csv")

FIELDNAMES = [
    "case_name",
    "court",
    "filed_date",
    "last_case_update_date",
    "current_status",
    "state_ag_plaintiff",
    "issue_area",
    "executive_action",
    "case_url",
    "source",
    "scraped_at",
]

def write_csv(rows: list[dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    cases = scrape_cases()
    print(f"Writing {len(cases)} cases to {OUT_PATH}")
    write_csv(cases)
    print("Done.")
