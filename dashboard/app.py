#v1 app

import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Litigation Tracker Dashboard", layout="wide")

DATA_PATH = Path("data/processed/cases.csv")

st.title("Litigation Tracker Dashboard")

if not DATA_PATH.exists():
    st.error(f"CSV not found at: {DATA_PATH}. Run your scraper to generate it.")
    st.stop()

df = pd.read_csv(DATA_PATH)

# Sidebar filters
st.sidebar.header("Filters")

status_options = sorted([x for x in df["current_status"].dropna().unique()])
selected_status = st.sidebar.multiselect("Case status", status_options, default=status_options)

# Issue area can be multi-value in one string; keep it simple for v1
issue_options = sorted([x for x in df["issue_area"].dropna().unique()])
selected_issues = st.sidebar.multiselect("Issue area", issue_options, default=issue_options)

exec_options = sorted([x for x in df["executive_action"].fillna("").unique()])
selected_exec = st.sidebar.multiselect("Executive action", exec_options, default=exec_options)

state_ag_only = st.sidebar.checkbox("State AG Plaintiff only", value=False)

filtered = df[
    df["current_status"].isin(selected_status)
    & df["issue_area"].isin(selected_issues)
    & df["executive_action"].fillna("").isin(selected_exec)
]

if state_ag_only and "state_ag_plaintiff" in filtered.columns:
    filtered = filtered[filtered["state_ag_plaintiff"].astype(str).str.lower() == "true"]

# Top metrics
col1, col2 = st.columns(2)
col1.metric("Total cases", len(df))
col2.metric("Filtered cases", len(filtered))

# Show table
st.dataframe(filtered, use_container_width=True)

