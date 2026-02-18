# write_cases.py (v5 runner)
# Purpose: run the v5 scraper and output BOTH artifacts your site needs:
#  - cases.csv (table data)
#  - filters.json (dropdown options)

from __future__ import annotations

import os
from pathlib import Path

# Import from your v5 scraper module
# Assumes these files are in the same folder, OR your PYTHONPATH/module path is set correctly.
from scrape_just_security_tracker import scrape, write_csv, build_filters, write_filters_json


def main() -> None:
    # Output directory (repo root by default)
    out_dir = Path(os.getenv("OUT_DIR", ".")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cases_path = out_dir / "cases.csv"
    filters_path = out_dir / "filters.json"

    rows = scrape()
    print(f"Scraped {len(rows)} rows")

    write_csv(rows, str(cases_path))
    print(f"Wrote {cases_path}")

    filters = build_filters(rows)
    write_filters_json(filters, str(filters_path))
    print(f"Wrote {filters_path}")

    # quick sanity check counts
    print("Filter option counts:")
    for k, v in filters.items():
        print(f" - {k}: {len(v)}")


if __name__ == "__main__":
    main()
