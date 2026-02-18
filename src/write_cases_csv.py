#v4 
from scrape_just_security_tracker import scrape, write_csv, build_filters, write_filters_json

def main():
    rows = scrape()

    # 1) write the table data your website uses
    write_csv(rows, "cases.csv")
    print(f"Wrote cases.csv ({len(rows)} rows)")

    # 2) write dropdown filter options for the UI
    filters = build_filters(rows)
    write_filters_json(filters, "filters.json")
    print("Wrote filters.json")

if __name__ == "__main__":
    main()
