from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("Litigation Tracker")

BASE_DIR = Path(__file__).parent
CASES_PATH = BASE_DIR / "data" / "processed" / "cases.csv"

# --- Debug (safe) ---
st.write("Working directory:", str(BASE_DIR))
st.write("data/processed exists?", (BASE_DIR / "data" / "processed").exists())
st.write("cases.csv exists?", CASES_PATH.exists())

if not CASES_PATH.exists():
    st.error("cases.csv not found. Expected at: data/processed/cases.csv")
    st.stop()

def read_csv_robust(path: Path) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")

df = read_csv_robust(CASES_PATH).fillna("")

# --- Dropdowns from CSV (works without filters.json) ---
state_ag = st.selectbox("State AGs", ["All"] + sorted(df["state_ags"].unique()))
case_status = st.selectbox("Case Status", ["All"] + sorted(df["case_status"].unique()))
issue = st.selectbox("Issue", ["All"] + sorted(df["issue_area"].unique()))
exec_action = st.selectbox("Executive Action", ["All"] + sorted(df["executive_action"].unique()))

# --- Filter ---
if state_ag != "All":
    df = df[df["state_ags"] == state_ag]
if case_status != "All":
    df = df[df["case_status"] == case_status]
if issue != "All":
    df = df[df["issue_area"] == issue]
if exec_action != "All":
    df = df[df["executive_action"] == exec_action]

# --- Display ---
visible_cols = ["case_name", "filings", "filed_date", "state_ags", "case_status", "last_case_update"]
st.dataframe(df[visible_cols], use_container_width=True)
