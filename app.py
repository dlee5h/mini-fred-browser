import streamlit as st
import duckdb
import pandas as pd

conn = duckdb.connect("data/fred.duckdb", read_only=True)

@st.cache_data
def run_query(series_ids):
    placeholders = ",".join(["?"] * len(series_ids))
    q = f"""
        SELECT date, value, series_id
        FROM fred_data
        WHERE series_id IN ({placeholders})
        ORDER BY date
    """
    return conn.execute(q, series_ids).df()

st.title("Mini FRED Browser")

# Load available series
series_list = conn.execute(
    "SELECT DISTINCT series_id FROM fred_data ORDER BY series_id"
).df()["series_id"].tolist()

# Series selector
selected = st.multiselect(
    "Select FRED Series",
    options=series_list,
    key="series_picker"
)

# Query + chart
if selected:
    df = run_query(selected)
    st.line_chart(df, x="date", y="value", color="series_id")
else:
    st.write("Select a series to begin.")
