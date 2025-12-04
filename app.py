import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
import uuid

# --- Paths ---
db_path = os.path.join("data", "fred.duckdb")
last_updated_path = os.path.join("data", "last_updated.txt")
saved_views_path = os.path.join("user_data", "saved_views.json")
os.makedirs(os.path.dirname(saved_views_path), exist_ok=True)

# --- Connect to DuckDB ---
conn = duckdb.connect(db_path, read_only=True)

# --- Cached query function ---
@st.cache_data(show_spinner=False)
def run_query(series_ids):
    if not series_ids:
        return pd.DataFrame(columns=["date", "value", "series_id"])
    placeholders = ",".join(["?"] * len(series_ids))
    q = f"""
        SELECT date, value, series_id
        FROM fred_data
        WHERE series_id IN ({placeholders})
        ORDER BY date
    """
    return conn.execute(q, series_ids).df()

# --- Transformations ---
def apply_transform(df, transform):
    df = df.copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if transform == "raw":
        return df
    elif transform == "pct_change_yoy":
        df["value"] = df["value"].pct_change(12) * 100
    elif transform == "pct_change_mom":
        df["value"] = df["value"].pct_change(1) * 100
    elif transform == "index_100":
        df["value"] = df["value"] / df["value"].iloc[0] * 100
    return df.dropna()

# --- Custom formulas ---
def combine_series(df1, df2, formula):
    merged = df1.merge(df2, on="date", suffixes=("_1", "_2"))
    if formula == "difference":
        merged["value"] = merged["value_1"] - merged["value_2"]
    elif formula == "ratio":
        merged["value"] = merged["value_1"] / merged["value_2"]
    return merged[["date", "value"]]

# --- Saved views ---
def load_saved_views():
    try:
        return json.load(open(saved_views_path))
    except:
        return {}

def save_view(name, config):
    views = load_saved_views()
    views[name] = config
    json.dump(views, open(saved_views_path, "w"), indent=2)

# --- Sidebar ---
st.sidebar.header("Controls")

# Load series list
series_list = conn.execute(
    "SELECT DISTINCT series_id FROM fred_data ORDER BY series_id"
).df()["series_id"].tolist()

selected = st.sidebar.multiselect(
    "Select Series (searchable)",
    options=series_list,
    default=[series_list[0]] if series_list else []
)

transform = st.sidebar.radio(
    "Transformation",
    ["raw", "pct_change_yoy", "pct_change_mom", "index_100"]
)

formula = st.sidebar.selectbox("Formula", ["none", "difference", "ratio"])
second_series = None
if formula != "none":
    second_series = st.sidebar.selectbox("Second Series", series_list)

theme = st.sidebar.radio("Theme", ["light", "dark"])
plt.style.use("dark_background" if theme=="dark" else "default")

# Save / Load Views
st.sidebar.markdown("---")
saved_views = load_saved_views()
save_name = st.sidebar.text_input("Save current view as:")
if st.sidebar.button("Save View") and save_name:
    config = {
        "selected": selected,
        "transform": transform,
        "formula": formula,
        "second_series": second_series,
        "theme": theme
    }
    save_view(save_name, config)
load_choice = st.sidebar.selectbox("Load Saved View", [""] + list(saved_views.keys()))
if load_choice:
    config = saved_views[load_choice]
    selected = config["selected"]
    transform = config["transform"]
    formula = config["formula"]
    second_series = config.get("second_series", None)
    theme = config.get("theme", "light")
    plt.style.use("dark_background" if theme=="dark" else "default")

# --- Title & Last Updated ---
st.title("Mini FRED Browser")
if os.path.exists(last_updated_path):
    with open(last_updated_path) as f:
        last = f.read()
    st.caption(f"Data last updated (UTC): {last}")

# --- Main content ---
if selected:
    # Fetch and transform data
    data_dict = {s: apply_transform(run_query([s]), transform) for s in selected}

    # Apply formula if requested
    if formula != "none" and second_series:
        data_dict["combined"] = combine_series(
            data_dict[selected[0]], data_dict[second_series], formula
        )
        plot_dict = {"Combined": data_dict["combined"]}
    else:
        plot_dict = data_dict

    # Multi-series chart
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = plt.cm.tab10.colors
    for i, (s, df) in enumerate(plot_dict.items()):
        ax.plot(df["date"], df["value"], label=s, color=colors[i % len(colors)])
    ax.set_title(" / ".join(plot_dict.keys()))
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    st.pyplot(fig)

    # Combine for table + CSV
    combined = pd.concat(
        [df.assign(series_id=s) for s, df in plot_dict.items()],
        ignore_index=True
    )
    st.download_button(
        "Download CSV",
        combined.to_csv(index=False),
        file_name="fred_export.csv"
    )

    st.dataframe(combined.head(50))

else:
    st.write("Select one or more series to begin.")
