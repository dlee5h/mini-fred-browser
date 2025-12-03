import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import os

last_updated_file = os.path.join(os.path.dirname(__file__), "..", "data", "last_updated.txt")
if os.path.exists(last_updated_file):
    last = open(last_updated_file).read()
    st.caption(f"Last updated (UTC): {last}")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up ONE folder to project root
db_path = os.path.join(BASE_DIR, "data", "fred.duckdb")

con = duckdb.connect(db_path)


st.title("Mini FRED Browser")

# Dropdown
series_list = con.execute("SELECT DISTINCT series_id FROM facts").df()["series_id"].tolist()
selected = st.selectbox("Select a Series", series_list)

# Query
df = con.execute("""
    SELECT date, value
    FROM facts
    WHERE series_id = ?
    ORDER BY date
""", [selected]).df()

# Chart
fig, ax = plt.subplots(figsize=(12,4))
ax.plot(df["date"], df["value"])
ax.set_title(selected)
st.pyplot(fig)

# Data download
st.download_button(
    "Download CSV",
    df.to_csv(index=False),
    file_name=f"{selected}.csv"
)

