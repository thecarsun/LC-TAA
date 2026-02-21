# Schema Documentation (v8)

## data/processed/cases.csv

Primary output file. One row per legal case tracked by JustSecurity.org.
Encoding: UTF-8 with BOM (`utf-8-sig`)

| Column | Type | Source | Description |
|---|---|---|---|
| `case_name` | string | Scraped | Full case name including court and docket number e.g. `National Association of the Deaf v. Trump (D.D.C.) 1:25-cv-01683` |
| `case_url` | string | Scraped | URL to the case on CourtListener or other court docket system |
| `filings` | string | Scraped | List of filings e.g. `Complaint`, `Amended Complaint` |
| `filed_date` | string (YYYY-MM-DD) | Scraped | Date the case was originally filed |
| `state_ags` | string | Scraped | Whether the case involves State A.G. plaintiffs. Value: `State A.G. Plaintiffs` or empty |
| `case_status` | string | Scraped | Current status of the case. See status values below |
| `issue_area` | string | Scraped via filter | Top-level issue category. Scraped by selecting each Issue filter dropdown option |
| `executive_action` | string | Scraped via filter | Specific executive action being challenged. Scraped by selecting each Executive Action filter dropdown option |
| `last_case_update` | string (YYYY-MM-DD) | Scraped | Date of the most recent update to the case |

---

## Case Status Values

| Status | Meaning |
|---|---|
| `Government Action Blocked` | Court permanently blocked the action |
| `Government Action Temporarily Blocked` | TRO or preliminary injunction in place |
| `Government Action Blocked Pending Appeal` | Block maintained while appeal is heard |
| `Case Closed in Favor of Plaintiff` | Case resolved, plaintiff won |
| `Government Action Temporarily Blocked in Part; Temporary Block Denied in Part` | Mixed ruling |
| `Temporary Block of Government Action Denied` | Court declined to block the action |
| `Government Action Not Blocked Pending Appeal` | Action allowed to proceed during appeal |
| `Case Closed/Dismissed in Favor of Government` | Case resolved, government won |
| `Awaiting Court Ruling` | Case pending, no ruling yet |
| `Case Closed` | Case closed without clear win/loss |

---

## data/processed/filters.json

Lookup file containing all valid filter option values. Used to populate sidebar dropdowns in `app.py`.

```json
{
  "State AGs": ["State A.G. Plaintiffs"],
  "Case Status": ["Awaiting Court Ruling", "Case Closed", ...],
  "Issue": ["Civil Liberties and Rights", "Environment", ...],
  "Executive Action": ["Alien Enemies Act Removals", "Ban on DEIA Initiatives", ...]
}
```

---

## Scraping Notes

- `issue_area` and `executive_action` are **not columns in the source table** — they are filter dropdown values on the JustSecurity page
- Each filter value is selected one at a time via Playwright, and the resulting visible rows are tagged with that value
- Total: 12 issue area loops + 121 executive action loops + 1 final full scrape
- Each case maps to exactly **one** issue area and **one** executive action (confirmed: 653 unique cases, 653 unique mappings)
- `case_url` is extracted from the `<a href>` tag inside the case name cell

---

## Source

Data sourced from:
**JustSecurity.org Litigation Tracker**
https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/

**PURPOSE**
Converts the data from the [Just Security.Org](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/)
tracker data into a canconical schema for analysis and into [Streamlit.io](https://streamlit.io/)

**PRIMARY DATA ARTIFACT**
- `data/processed/cases.csv` will be the canonical dataset consumed by the Streamlit.io dashboard.
- All scraped fields are normalized into the schema below.
- Derived metrics (e.g., days open) are computed in the dashboard layer and are not stored as canonical fields.

## Table: `cases` (One row per case)

### Required Fields

| Field | Type | Example | Description |
|------|------|---------|-------------|
| case_name | string | `State of X v. DHS` | Human-readable case title |
| court | string | `N.D. California` | Court where the case is filed / heard |
| filed_date | date (YYYY-MM-DD) | `2025-01-22` | Case filed date |
| current_status | string | `Open` | Current case status as shown in tracker |
| issue_area | string (CSV list) | `Immigration, Federal Funding` | Issue category/categories (comma-separated if multiple) |
| executive_action | string (CSV list) | `Executive Order 14123` | Executive action(s) associated with the case (comma-separated if multiple) |
| state_ags | string (CSV list) | `CA, NY, MA` | State Attorney General(s) involved (comma-separated if multiple) |
| case_url | string (URL) | `https://www.justsecurity.org/...` | Canonical URL for the case entry (or anchor/deeplink if available) |
| source | string | `Just Security` | Data source attribution (constant) |
| scraped_at | datetime (UTC ISO 8601) | `2026-02-10T23:15:00Z` | Timestamp when the data was scraped |

### Optional Fields
| Field | Type | Example | Description |
|------|------|---------|-------------|
| last_case_update_date | date (YYYY-MM-DD) | `2025-03-02` | “Last Case Update” date from tracker |
| date_closed | date (YYYY-MM-DD) | `2025-03-02` | Closure date derived from `last_case_update_date` when status indicates closure (otherwise blank) |

---

## Field Conventions

### Date formats
- `filed_date`, `last_case_update_date`, and `date_closed` use `YYYY-MM-DD`.
- `scraped_at` uses UTC ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`.

### Multi-value fields
The following fields may contain multiple values and are stored as comma-separated strings:
- `state_ags`
- `issue_area`
- `executive_action`

Example:
- `state_ags = "CA,NY,MA"`

---

## Derivations (computed, not stored)

The dashboard computes these values dynamically:
- `days_open`
  - If `date_closed` exists: `date_closed - filed_date`
  - Else: `today - filed_date`

---

## Rules & Assumptions

### Closure logic
- If `current_status` indicates a case is closed/resolved/dismissed, then:
  - `date_closed = last_case_update_date`
- Otherwise:
  - `date_closed` is blank

### Attribution
- `source` is always set to `Just Security`.
- This project stores structured metadata only and does not republish source content verbatim.

---

## Versioning
- This schema is v8 and may expand over time 