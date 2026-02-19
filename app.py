from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
CASES_PATH = BASE_DIR / "data" / "processed" / "cases.csv"

df = pd.read_csv(CASES_PATH, encoding="utf-8").fillna("")

state_ag = st.selectbox("State AGs", ["All"] + sorted(df["state_ags"].unique()))
case_status = st.selectbox("Case Status", ["All"] + sorted(df["case_status"].unique()))
issue = st.selectbox("Issue", ["All"] + sorted(df["issue_area"].unique()))
exec_action = st.selectbox("Executive Action", ["All"] + sorted(df["executive_action"].unique()))

if state_ag != "All":
    df = df[df["state_ags"] == state_ag]
if case_status != "All":
    df = df[df["case_status"] == case_status]
if issue != "All":
    df = df[df["issue_area"] == issue]
if exec_action != "All":
    df = df[df["executive_action"] == exec_action]

visible_cols = ["case_name", "filings", "filed_date", "state_ags", "case_status", "last_case_update"]
st.dataframe(df[visible_cols], use_container_width=True)
