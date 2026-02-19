
from pathlib import Path
import pandas as pd

from scrape_tracker import scrape_cases

OUT_PATH = Path("data/processed/cases.csv")

# Keep column order consistent with your schema/CSV header
COLUMNS = [
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


def write_cases_csv(cases: list[dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(cases)

    # Ensure all expected columns exist
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNS]
    df.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows to {OUT_PATH}")


if __name__ == "__main__":
    cases = scrape_cases(debug=False)

    # If scrape was blocked/skipped or returned nothing, do NOT overwrite existing CSV
    if not cases:
        print("No cases scraped. Exiting without writing CSV.")
        raise SystemExit(0)

    write_cases_csv(cases)
