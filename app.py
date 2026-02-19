from pathlib import Path
import streamlit as st
import json
import pandas as pd
import streamlit as st

CASES_PATH = "processed/cases.csv"
FILTERS_PATH = "processed/filters.json"

st.write("Working directory:", Path.cwd())
st.write("processed/ exists?", Path("processed").exists())
if Path("processed").exists():
    st.write("processed/ files:", [p.name for p in Path("processed").iterdir()])

st.write("cases.csv exists?", CASES_PATH.exists())
st.write("filters.json exists?", FILTERS_PATH.exists())

st.set_page_config(layout="wide")
st.title("Litigation Tracker")


def read_csv_robust(path: str) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")

def read_json_robust(path: str) -> dict:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)

# ---- Load once (robust) ----
df = read_csv_robust(CASES_PATH).fillna("")
filters = read_json_robust(FILTERS_PATH)

# Optional: debug (remove later)
# st.write("Columns:", list(df.columns))

# ---- Dropdowns ----
state_ag = st.selectbox("State AGs", ["All"] + filters.get("State AGs", []))
case_status = st.selectbox("Case Status", ["All"] + filters.get("Case Status", []))
issue = st.selectbox("Issue", ["All"] + filters.get("Issue", []))
exec_action = st.selectbox("Executive Action", ["All"] + filters.get("Executive Action", []))

# ---- Filter df by existing CSV columns ----
if state_ag != "All":
    df = df[df["state_ags"] == state_ag]

if case_status != "All":
    df = df[df["case_status"] == case_status]

if issue != "All":
    df = df[df["issue_area"] == issue]

if exec_action != "All":
    df = df[df["executive_action"] == exec_action]

# ---- Display (website columns) ----
visible_cols = [
    "case_name",
    "filings",
    "filed_date",
    "state_ags",
    "case_status",
    "last_case_update",
]
st.dataframe(df[visible_cols], use_container_width=True)
