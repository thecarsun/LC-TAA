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

# ---- Scorecard metrics ----
plaintiff_wins = [
    "Government Action Blocked",
    "Government Action Temporarily Blocked",
    "Government Action Blocked Pending Appeal",
    "Case Closed in Favor of Plaintiff",
    "Government Action Temporarily Blocked in Part; Temporary Block Denied in Part",
]
govt_wins = [
    "Temporary Block of Government Action Denied",
    "Government Action Not Blocked Pending Appeal",
    "Case Closed/Dismissed in Favor of Government",
]

total   = len(df)
p_wins  = len(df[df["case_status"].isin(plaintiff_wins)])
g_wins  = len(df[df["case_status"].isin(govt_wins)])
pending = len(df[df["case_status"] == "Awaiting Court Ruling"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cases",     total)
col2.metric("Plaintiff Wins",  p_wins)
col3.metric("Government Wins", g_wins)
col4.metric("Awaiting Ruling", pending)

st.divider()

# ---- Sidebar filters ----
st.sidebar.header("Filters")

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
        "case_url",
        "filings",
        "filed_date",
        "state_ags",
        "case_status",
        "last_case_update",
    ]],
    use_container_width=True,
    hide_index=True,
)