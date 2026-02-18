#v1.1 app

import pandas as pd
import streamlit as st
from pathlib import Path
import re   

st.set_page_config(page_title="Litigation Tracker Dashboard", layout="wide")

DATA_PATH = Path("data/processed/cases.csv")

st.title("Litigation Tracker Dashboard")

if not DATA_PATH.exists():
    st.error(f"CSV not found at: {DATA_PATH}. Run your scraper to generate it.")
    st.stop()

df = pd.read_csv(DATA_PATH)

def normalize_text(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"\s+", " ", s)              # collapse whitespace
    s = re.sub(r"[^a-z0-9\s:/.-]", " ", s)  # strip odd punctuation but keep docket chars
    return s.strip()

df["search_text"] = (
    df["case_name"].fillna("")
    + " " + df["court"].fillna("")
    + " " + df["current_status"].fillna("")
    + " " + df["issue_area"].fillna("")
    + " " + df["executive_action"].fillna("")
).apply(normalize_text)


# --- Basic cleanup ---
df["filed_date"] = pd.to_datetime(df["filed_date"], errors="coerce")
df["last_case_update_date"] = pd.to_datetime(df["last_case_update_date"], errors="coerce")

# Sidebar filters
st.sidebar.header("Filters")
st.sidebar.caption("Search supports multiple keywords (e.g., 'immigration texas').")


# Search
search = st.sidebar.text_input("Search case name")


# Status filter
status_options = sorted([x for x in df["current_status"].dropna().unique()])
selected_status = st.sidebar.multiselect("Case status", status_options, default=status_options)

# Issue filter
issue_options = sorted([x for x in df["issue_area"].dropna().unique()])
selected_issues = st.sidebar.multiselect("Issue area", issue_options, default=issue_options)

# Executive action filter (allow blanks)
exec_options = sorted([x for x in df["executive_action"].fillna("").unique()])
selected_exec = st.sidebar.multiselect("Executive action", exec_options, default=exec_options)

ag_filter = st.sidebar.selectbox(
    "State AG",
    ["All cases", "State AG Plaintiffs only"],
    index=0
)


# Date range filter (filed date)
min_date = df["filed_date"].min()
max_date = df["filed_date"].max()

date_range = st.sidebar.date_input(
    "Filed date range",
    value=(min_date.date() if pd.notna(min_date) else None,
           max_date.date() if pd.notna(max_date) else None),
)

filtered = df[
    df["current_status"].isin(selected_status)
    & df["issue_area"].isin(selected_issues)
    & df["executive_action"].fillna("").isin(selected_exec)
].copy()

if ag_filter == "State AG Plaintiffs only":
    filtered = filtered[filtered["state_ag_plaintiff"].astype(str).str.lower() == "true"]

# Apply search
if search:
    terms = [t for t in normalize_text(search).split() if t]
    for t in terms:
        filtered = filtered[filtered["search_text"].str.contains(t, na=False)]


# Apply date range
if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered["filed_date"] >= start) & (filtered["filed_date"] <= end)]

# Top metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total cases", len(df))
c2.metric("Filtered cases", len(filtered))
c3.metric("Unique courts", filtered["court"].nunique())

st.divider()

# Chart: cases by status
st.subheader("Cases by Issue Area")

# Split comma-separated issue_area into individual tags
issues = (
    filtered["issue_area"]
    .fillna("")
    .astype(str)
    .str.split(",")
    .explode()
    .str.strip()
)

issues = issues[issues != ""]  # drop blanks

issue_counts = issues.value_counts()

st.bar_chart(issue_counts)

top_n = st.slider("Show top N issue areas", 5, 50, 20)
st.bar_chart(issue_counts.head(top_n))



st.divider()

# Table view
st.subheader("Cases")

# Sort most recently filed first
filtered_sorted = filtered.sort_values("filed_date", ascending=False)
st.dataframe(filtered_sorted, use_container_width=True)

