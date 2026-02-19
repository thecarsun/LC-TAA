from pathlib import Path
import re
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("Litigation Tracker")

BASE_DIR = Path(__file__).parent
CASES_PATH = BASE_DIR / "data" / "processed" / "cases.csv"

# --- Debug: confirm paths ---
st.write("Working directory:", str(BASE_DIR))
st.write("data/processed exists?", (BASE_DIR / "data" / "processed").exists())
st.write("cases.csv exists?", CASES_PATH.exists())

if not CASES_PATH.exists():
    st.error("cases.csv not found. Expected at: data/processed/cases.csv")
    st.stop()

def read_csv_robust(path: Path) -> pd.DataFrame:
    """Try several encodings so the app doesn't crash on weird characters."""
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")

def normalize_cols(cols):
    """Normalize column names to snake_case lower, strip BOM, spaces, punctuation."""
    out = []
    for c in cols:
        c = str(c)
        c = c.replace("\ufeff", "")          # strip BOM if present
        c = c.strip()
        c = re.sub(r"[’']", "", c)           # remove apostrophes/smart quotes
        c = re.sub(r"[^0-9a-zA-Z]+", "_", c) # non-alnum -> underscore
        c = c.strip("_").lower()
        out.append(c)
    return out

# ---- Load and normalize ----
df = read_csv_robust(CASES_PATH)
df.columns = normalize_cols(df.columns)
df = df.fillna("")

# TEMP: show what columns we actually have
st.write("Columns:", list(df.columns))

# ---- Sanity check required columns ----
required = {
    "case_name",
    "filings",
    "filed_date",
    "state_ags",
    "case_status",
    "issue_area",
    "executive_action",
    "last_case_update",
}
missing = sorted(required - set(df.columns))
if missing:
    st.error(f"cases.csv is missing expected columns: {missing}")
    st.stop()

# ---- Dropdowns from CSV ----
state_ag = st.selectbox(
    "State A.G.'s",
    ["All"] + sorted(df["state_ags"].unique())
)

case_status = st.selectbox(
    "Case Status",
    ["All"] + sorted(df["case_status"].unique())
)

issue = st.selectbox(
    "Issue",
    ["All"] + sorted(df["issue_area"].unique())
)

exec_action = st.selectbox(
    "Executive Action",
    ["All"] + sorted(df["executive_action"].unique())
)

# ---- Apply filters ----
filtered = df.copy()

if state_ag != "All":
    filtered = filtered[filtered["state_ags"] == state_ag]

if case_status != "All":
    filtered = filtered[filtered["case_status"] == case_status]

if issue != "All":
    filtered = filtered[filtered["issue_area"] == issue]

if exec_action != "All":
    filtered = filtered[filtered["executive_action"] == exec_action]

# ---- Display table (website columns) ----
visible_cols = [
    "case_name",
    "filings",
    "filed_date",
    "state_ags",
    "case_status",
    "last_case_update",
]

st.dataframe(filtered[visible_cols], use_container_width=True)