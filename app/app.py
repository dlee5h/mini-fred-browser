import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- CONNECT TO DATABASE ---
db_path = os.path.join(os.path.dirname(__file__), "..", "data", "fred.duckdb")
con = duckdb.connect(db_path)

# --- LOAD SERIES LIST ---
series_list = con.execute("SELECT DISTINCT series_id FROM facts").df()["series_id"].tolist()

# --- UI: MULTISELECT ---
selected_list = st.multiselect(
    "Select Series",
    options=series_list,
    default=[series_list[0]]
)

# --- FUNCTION TO GET ONE SERIES ---
def get_series(series_id):
    q = """
        SELECT date, value
        FROM facts
        WHERE series_id = ?
        ORDER BY date
    """
    return con.execute(q, [series_id]).df()

# --- FETCH DATA INTO A DICTIONARY ---
data = {}
for s in selected_list:
    data[s] = get_series(s)

# --- PLOT ---
fig, ax = plt.subplots(figsize=(12,5))

for series_id, df in data.items():
    ax.plot(df["date"], df["value"], label=series_id)

ax.legend()
st.pyplot(fig)
