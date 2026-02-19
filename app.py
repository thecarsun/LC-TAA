import json
import pandas as pd
import streamlit as st

def read_csv_robust(path: str) -> pd.DataFrame:
    # Try common encodings first
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue

    # Last resort: load *something* and replace bad bytes
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")

def read_json_robust(path: str) -> dict:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue

    # Last resort
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)

# IMPORTANT: confirm paths
CASES_PATH = "processed/cases.csv"
FILTERS_PATH = "processed/filters.json"

df = read_csv_robust(CASES_PATH)
filters = read_json_robust(FILTERS_PATH)

st.write("Loaded cases from:", CASES_PATH)
st.write("Loaded filters from:", FILTERS_PATH)
st.write("Columns:", list(df.columns))
