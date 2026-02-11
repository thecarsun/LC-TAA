# canonical schema (v1)

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
| last_case_update_date | date (YYYY-MM-DD) | `2025-03-02` | “Last Case Update” date from source tracker |
| date_closed | date (YYYY-MM-DD) | `2025-03-02` | Closure date derived from `last_case_update_date` when status indicates closure (otherwise blank) |
| state_ag_plaintiff | boolean | `true` | indicates if the State Attorney General is listed as a plaintiff in the case |


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
- This schema is v1 and may expand over time (e.g., adding richer metadata, optional case summaries, or future LLM-generated fields).
Stay tuned....