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

# ---- Scorecard metrics (always full dataset) ----
plaintiff_win_statuses = [
    "Government Action Blocked",
    "Government Action Temporarily Blocked",
    "Government Action Blocked Pending Appeal",
    "Case Closed in Favor of Plaintiff",
    "Government Action Temporarily Blocked in Part; Temporary Block Denied in Part",
]
govt_win_statuses = [
    "Temporary Block of Government Action Denied",
    "Government Action Not Blocked Pending Appeal",
    "Case Closed/Dismissed in Favor of Government",
]

total   = len(df)
p_wins  = len(df[df["case_status"].isin(plaintiff_win_statuses)])
g_wins  = len(df[df["case_status"].isin(govt_win_statuses)])
pending = len(df[df["case_status"] == "Awaiting Court Ruling"])
decided = p_wins + g_wins
p_rate  = round((p_wins / decided) * 100) if decided > 0 else 0
g_rate  = round((g_wins / decided) * 100) if decided > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Cases",      total)
col2.metric("Plaintiff Wins",   p_wins)
col3.metric("Government Wins",  g_wins)
col4.metric("Awaiting Ruling",  pending)
col5.metric("Plaintiff Win Rate", f"{p_rate}%")
col6.metric("Govt Win Rate",    f"{g_rate}%")

st.divider()

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

st.caption(f"Showing {len(filtered)} of {len(df)} cases")

st.divider()

# ---- Charts row 1: Issue Area bar + Win Rate ----
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.subheader("Cases by Issue Area")
    issue_counts = (
        filtered.groupby("issue_area")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    st.bar_chart(issue_counts.set_index("issue_area")["count"], horizontal=True)

with chart_col2:
    st.subheader("Win Rate (filtered)")
    f_decided = len(filtered[filtered["case_status"].isin(plaintiff_win_statuses)]) + \
                len(filtered[filtered["case_status"].isin(govt_win_statuses)])
    f_p_wins  = len(filtered[filtered["case_status"].isin(plaintiff_win_statuses)])
    f_g_wins  = len(filtered[filtered["case_status"].isin(govt_win_statuses)])
    f_p_rate  = round((f_p_wins / f_decided) * 100) if f_decided > 0 else 0
    f_g_rate  = round((f_g_wins / f_decided) * 100) if f_decided > 0 else 0

    win_df = pd.DataFrame({
        "Party":      ["Plaintiffs", "Government"],
        "Win Rate %": [f_p_rate,     f_g_rate],
    })
    st.bar_chart(win_df.set_index("Party")["Win Rate %"])
    st.caption(f"Based on {f_decided} decided cases")

st.divider()

# ---- Charts row 2: Timeline + State AGs ----
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("Cases Filed Over Time")
    timeline = filtered[filtered["filed_date"] != ""].copy()
    if not timeline.empty:
        timeline["filed_date"] = pd.to_datetime(timeline["filed_date"], errors="coerce")
        timeline = timeline.dropna(subset=["filed_date"])
        timeline["month"] = timeline["filed_date"].dt.to_period("M").astype(str)
        monthly = (
            timeline.groupby("month")
            .size()
            .reset_index(name="count")
            .sort_values("month")
        )
        st.bar_chart(monthly.set_index("month")["count"])
    else:
        st.info("No date data available for current filter.")

st.divider()

# ---- Display table ----
st.subheader("Cases")
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
    column_config={
        "case_url":  st.column_config.LinkColumn("Case Link", display_text="View Case"),
        "case_name": st.column_config.TextColumn("Case Name"),
    },
    use_container_width=True,
    hide_index=True,
)