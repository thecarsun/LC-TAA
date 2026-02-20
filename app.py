# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Litigation Tracker", layout="wide")
st.title("Litigation Tracker: Legal Challenges to Trump Administration Actions")

BASE_DIR = Path(__file__).parent
CASES_PATH = BASE_DIR / "data" / "processed" / "cases.csv"

if not CASES_PATH.exists():
    st.error("cases.csv not found. Run `py src/scrape_tracker.py` first.")
    st.stop()

@st.cache_data
def load_data():
    df = pd.read_csv(CASES_PATH, encoding="utf-8-sig")
    return df.fillna("")

df = load_data()

# ---- Sidebar filters ----
st.sidebar.header("Filters")

def filter_options(col):
    return ["All"] + sorted([v for v in df[col].unique() if v])

state_ag    = st.sidebar.selectbox("State A.G.'s",    filter_options("state_ags"))
case_status = st.sidebar.selectbox("Case Status",      filter_options("case_status"))
issue       = st.sidebar.selectbox("Issue",            filter_options("issue_area"))
exec_action = st.sidebar.selectbox("Executive Action", filter_options("executive_action"))

# ---- Search box ----
search = st.text_input("Search keywords", placeholder="e.g. tariffs, ACLU, immigration, DOGE...")

# ---- Apply filters ----
filtered = df.copy()
if state_ag    != "All": filtered = filtered[filtered["state_ags"]       == state_ag]
if case_status != "All": filtered = filtered[filtered["case_status"]      == case_status]
if issue       != "All": filtered = filtered[filtered["issue_area"]       == issue]
if exec_action != "All": filtered = filtered[filtered["executive_action"] == exec_action]
if search:
    mask = (
        filtered["case_name"].str.contains(search, case=False, na=False) |
        filtered["issue_area"].str.contains(search, case=False, na=False) |
        filtered["executive_action"].str.contains(search, case=False, na=False) |
        filtered["case_status"].str.contains(search, case=False, na=False) |
        filtered["state_ags"].str.contains(search, case=False, na=False)
)
filtered = filtered[mask]

# ---- Bar chart: Cases by Issue Area ----
st.subheader("Cases by Issue Area")
issue_counts = (
    filtered.groupby("issue_area")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)
st.bar_chart(issue_counts.set_index("issue_area")["count"])

# ---- Summary ----
st.caption(f"Showing {len(filtered)} of {len(df)} cases")

# ---- Display table ----
st.dataframe(
    filtered[[
        "case_name",
        "filings",
        "filed_date",
        "state_ags",
        "case_status",
        "last_case_update",
    ]],
    use_container_width=True,
    hide_index=True,
)