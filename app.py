# v8.3
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Litigation Tracker", layout="wide")
st.title("Litigation Tracker: Legal Challenges to Trump Administration Actions")
st.info("For the best experience, view this dashboard on a desktop browser.")

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

# ---- Last updated timestamp ----
last_run_path = BASE_DIR / "data" / "processed" / "last_run.txt"
if last_run_path.exists():
    last_run = pd.to_datetime(last_run_path.read_text(encoding="utf-8").strip())
    st.caption(f"Scraper last run: {last_run.strftime('%B %d, %Y')}")
else:
    latest_update = pd.to_datetime(df["last_case_update"], errors="coerce").max()
    st.caption(f"Data last updated: {latest_update.strftime('%B %d, %Y')}")

# ---- Status groups ----
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

# ---- Scorecard metrics (Responds to filters) ----
total   = len(filtered)
p_wins  = len(filtered[filtered["case_status"].isin(plaintiff_win_statuses)])
g_wins  = len(filtered[filtered["case_status"].isin(govt_win_statuses)])
pending = len(filtered[filtered["case_status"] == "Awaiting Court Ruling"])
decided = p_wins + g_wins
p_rate  = round((p_wins / decided) * 100) if decided > 0 else 0
g_rate  = round((g_wins / decided) * 100) if decided > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Cases",        total)
col2.metric("Plaintiff Wins",     p_wins)
col3.metric("Government Wins",    g_wins)
col4.metric("Awaiting Ruling",    pending)
col5.metric("Plaintiff Win Rate", f"{p_rate}%")
col6.metric("Govt Win Rate",      f"{g_rate}%")

st.divider()

# ---- Issue Area bar (full width) ----
st.subheader("Cases by Issue Area")
issue_counts = (
    filtered.groupby("issue_area")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=True)
)
fig = px.bar(
    issue_counts,
    x="count",
    y="issue_area",
    orientation="h",
    labels={"count": "Cases", "issue_area": ""},
    color="count",
    color_continuous_scale="Blues",
)
fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---- Case Status Breakdown (full width) ----
st.subheader("Case Status Breakdown")
status_counts = (
    filtered.groupby("case_status")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)
fig2 = px.pie(
    status_counts,
    names="case_status",
    values="count",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Set3,
)
fig2.update_traces(textposition="inside", textinfo="percent")
fig2.update_layout(
    margin=dict(t=0, b=0, l=0, r=0),
    height=450,
    legend=dict(orientation="h", font=dict(size=14)),
)
st.plotly_chart(fig2, use_container_width=True)

# ---- Top 10 Executive Actions (full width) ----
st.subheader("Top 10 Executive Actions")
exec_counts = (
    filtered[filtered["executive_action"] != ""]
    .groupby("executive_action")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=True)
    .tail(10)
)
exec_counts["label"] = exec_counts["executive_action"].str[:50] + "..."
fig3 = px.bar(
    exec_counts,
    x="count",
    y="label",
    orientation="h",
    labels={"count": "Cases", "label": ""},
    color="count",
    color_continuous_scale="Oranges",
)
fig3.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---- Heatmap (full width) ----
st.subheader("Heatmap: Issue Area vs Case Status")
heatmap_data = (
    filtered[
        (filtered["issue_area"] != "") &
        (filtered["case_status"] != "")
    ]
    .groupby(["issue_area", "case_status"])
    .size()
    .reset_index(name="count")
)
if not heatmap_data.empty:
    heatmap_pivot = heatmap_data.pivot(
        index="issue_area",
        columns="case_status",
        values="count"
    ).fillna(0)
    fig4 = px.imshow(
        heatmap_pivot,
        color_continuous_scale="RdYlGn",
        labels=dict(x="Case Status", y="Issue Area", color="Cases"),
        aspect="auto",
    )
    fig4.update_xaxes(tickangle=45)
    fig4.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Not enough data for heatmap with current filters.")

# ---- Cumulative cases over time ----
st.subheader("Cumulative Cases Filed Over Time")
timeline = filtered[filtered["filed_date"] != ""].copy()
if not timeline.empty:
    timeline["filed_date"] = pd.to_datetime(timeline["filed_date"], errors="coerce")
    timeline = timeline.dropna(subset=["filed_date"])
    timeline = timeline[timeline["filed_date"] >= "2025-01-01"]
    timeline = timeline.sort_values("filed_date")
    timeline["month"] = timeline["filed_date"].dt.to_period("M").astype(str)
    monthly = (
        timeline.groupby("month")
        .size()
        .reset_index(name="new_cases")
        .sort_values("month")
    )
    monthly["cumulative"] = monthly["new_cases"].cumsum()
    fig5 = px.line(
        monthly,
        x="month",
        y="cumulative",
        labels={"month": "Month", "cumulative": "Total Cases Filed"},
        markers=True,
    )
    fig5.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    fig5.update_xaxes(tickangle=45)
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("No date data available for current filters.")

st.divider()

# ---- Treemap: Issue Area -> Executive Action ----
st.subheader("Treemap: Cases by Issue Area and Executive Action")
treemap_data = filtered[
    (filtered["issue_area"] != "") &
    (filtered["executive_action"] != "")
].copy()
if not treemap_data.empty:
    treemap_data["exec_short"] = treemap_data["executive_action"].str[:40] + "..."
    fig6 = px.treemap(
        treemap_data,
        path=["issue_area", "exec_short"],
        color="issue_area",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig6.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
    st.plotly_chart(fig6, use_container_width=True)
else:
    st.info("Not enough data for treemap with current filters.")

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

# ---- Footer ----
st.divider()
st.caption(
    "Data sourced from [JustSecurity.org](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/). "
    "Please consider [supporting their work](https://www.justsecurity.org/donate/).  "
    "Dashboard built by [Car](https://github.com/thecarsun), [More about this dashboard](https://github.com/thecarsun/LC-TAA/blob/main/README.md)"
)