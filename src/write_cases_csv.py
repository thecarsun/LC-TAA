# write_cases.py (v5.1 runner)
from __future__ import annotations

import os
from pathlib import Path

from scrape_just_security_tracker import (
    scrape,
    write_csv,
    build_filters,
    write_filters_json,
)

def main() -> None:
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

    # Debug / sanity checks against website expectations
    print("Filter option counts:")
    for k in ["State A.G.'s", "Case Status", "Issue", "Executive Action"]:
        print(f" - {k}: {len(filters.get(k, []))}")

    # Optional: show first few Issue options to confirm normalization worked
    print("\nFirst 20 Issue options:")
    for x in filters.get("Issue", [])[:20]:
        print(" -", x)

if __name__ == "__main__":
    main()
