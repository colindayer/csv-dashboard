"""CSV Dashboard — upload a spreadsheet, get something readable.

Run:  streamlit run app.py   ->  http://localhost:8501

Visual language borrowed from nas100_backtest/dashboard/app.py.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core import fmt, pick_columns, summarise

MAX_ROWS_CHARTED = 5000  # ponytail: downsample past this, charts get unreadable anyway

# Sidebar expanded: the controls are the product. A collapsed sidebar reads as "static report".
st.set_page_config(page_title="CSV Dashboard", page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""<style>
.block-container{padding-top:1.2rem;max-width:1500px}
code,.mono{font-family:'SF Mono',Menlo,monospace}
[data-testid="stMetricValue"]{font-family:'SF Mono',Menlo,monospace}
</style>""", unsafe_allow_html=True)

st.sidebar.header("Data")
upload = st.sidebar.file_uploader("CSV file", type=["csv", "tsv", "txt"])
st.sidebar.caption("Read-only. Nothing is stored or sent anywhere.")

SAMPLE = Path(__file__).with_name("sample_arts_programme.csv")

# A client opening a bare file-uploader sees nothing. Give them the demo first.
if upload is None and not st.session_state.get("demo"):
    st.title("CSV Dashboard")
    st.markdown(
        "Upload a CSV in the sidebar. You pick which column is the date, "
        "which numbers matter, and how to group them — the charts follow."
    )
    st.button("Show me with sample data", on_click=lambda: st.session_state.update(demo=True))
    st.stop()

source = upload if upload is not None else SAMPLE

# Untrusted input: anything here can be malformed. Fail with a sentence, not a stack trace.
try:
    df = pd.read_csv(source, sep=None, engine="python")
except Exception as e:
    st.error(f"Could not read that file: {e}")
    st.stop()

if df.empty or not len(df.columns):
    st.error("That file has no rows or no columns.")
    st.stop()

dates, numeric, categories = pick_columns(df)

if not numeric:
    st.error(
        "No numeric columns found, so there's nothing to chart. "
        f"Columns seen: {', '.join(map(str, df.columns[:20]))}"
    )
    st.stop()

name = upload.name if upload is not None else SAMPLE.name
st.title(name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title())
st.caption(f"{len(df):,} rows · {len(df.columns)} columns")

# If the file has a date column, plotting against it is what anyone wants. Default to it.
date_col = st.sidebar.selectbox("Date column", ["(row order)"] + dates, index=1 if dates else 0)
value_col = st.sidebar.selectbox("Value to track", numeric)
# Same reasoning as the date default: if there's an obvious way to break the numbers
# down, show it broken down. An ungrouped total is the least interesting view there is.
group_col = st.sidebar.selectbox("Group by", ["(none)"] + categories,
                                 index=1 if categories else 0)
agg = st.sidebar.selectbox("Aggregate", ["sum", "mean"],
                           help="How to combine rows that share a date or group.")
period = st.sidebar.selectbox("Period", ["Month", "Week", "Day"],
                              help="Buckets for the time chart. Monthly is what most "
                                   "funders and boards ask for.")
RULE = {"Day": "D", "Week": "W", "Month": "ME"}[period]

work = df.copy()
if date_col != "(row order)":
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
    work = work.dropna(subset=[date_col]).sort_values(date_col)
    if work.empty:
        st.error(f"No usable dates in '{date_col}'. Pick another column.")
        st.stop()

k = summarise(work[value_col])
if not k:
    st.error(f"'{value_col}' has no numeric values in it.")
    st.stop()

for c, (label, val, nd) in zip(st.columns(6), [
    ("Rows", k["count"], 0), ("Total", k["total"], 2), ("Average", k["mean"], 2),
    ("Median", k["median"], 2), ("Min", k["min"], 2), ("Max", k["max"], 2),
]):
    c.metric(label, fmt(val, nd))

if k["change_pct"] is not None:
    st.metric(f"Change in {value_col}, first to last", f"{k['change_pct']:+.1f}%")

st.divider()
by_time = date_col != "(row order)"

# Bucket by period, or sparse data (an event every week or two) draws a chart of
# disconnected fragments. Sum suits counts and money; mean suits prices and rates.
if by_time:
    bucket = pd.Grouper(key=date_col, freq=RULE)
    if group_col != "(none)":
        series = work.groupby([bucket, group_col])[value_col].agg(agg).unstack(group_col)
        # A group with no events in a bucket really did total zero — but it has no
        # meaningful average, so only fill when we're summing.
        if agg == "sum":
            series = series.fillna(0)
    else:
        series = work.groupby(bucket)[value_col].agg(agg)
else:
    series = work[value_col].reset_index(drop=True)

# ponytail: downsample AFTER aggregating, so totals stay honest. Resample by week/month
# if someone ever hands this ten years of daily rows.
if len(series) > MAX_ROWS_CHARTED:
    series = series.iloc[:: len(series) // MAX_ROWS_CHARTED + 1]

st.subheader(f"{value_col} over time ({agg} per {period.lower()})" if by_time
             else f"{value_col} by row")
st.line_chart(series)

if group_col != "(none)":
    st.subheader(f"{value_col} by {group_col}")
    st.bar_chart(work.groupby(group_col)[value_col].agg(agg).sort_values(ascending=False))

    # Every number at once, per group — this is the table a funder or a board asks for,
    # and it is the thing people currently build by hand.
    st.subheader(f"Summary by {group_col}")
    table = work.groupby(group_col)[numeric].agg(agg)
    table.insert(0, "rows", work.groupby(group_col).size())
    st.dataframe(table.style.format("{:,.2f}", subset=numeric), use_container_width=True)
    st.download_button("Download this summary as CSV", table.to_csv().encode(),
                       file_name=f"summary_by_{group_col}.csv", mime="text/csv")

with st.expander(f"All {len(df):,} rows"):
    st.dataframe(df, use_container_width=True)
