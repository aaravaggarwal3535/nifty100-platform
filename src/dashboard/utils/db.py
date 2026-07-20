# src/dashboard/utils/db.py
import sqlite3
import pandas as pd
import os
import streamlit as st

# Traverse up from src/dashboard/utils to the root directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")

@st.cache_data(ttl=600)  # Caches results for 10 minutes
def load_query(query: str, params: tuple = ()) -> pd.DataFrame:
    """Safely loads data from SQLite using a parameterised query."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_all_tickers() -> list:
    """Returns a list of all company tickers for search dropdowns."""
    df = load_query("SELECT company_id FROM companies ORDER BY company_id")
    return df["company_id"].tolist() if not df.empty else []