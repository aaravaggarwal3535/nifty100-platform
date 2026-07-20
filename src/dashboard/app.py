# src/dashboard/app.py
import streamlit as st

# 1. Global Page Configuration (Must be the first Streamlit command)
st.set_page_config(
    page_title="Nifty 100 Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Main Landing Page UI
st.title("📈 Nifty 100 Financial Intelligence Platform")
st.markdown("---")

st.markdown("""
### Welcome to the Data Analytics Division's Internal Platform

This system transforms raw financial statement data into structured analytics intelligence for **Nifty 100 companies**. 

#### 🚀 Platform Capabilities:
* **Deep Financial Profiling:** 10+ years of clean P&L, Balance Sheet, and Cash Flow history.
* **Ratio Engine:** 50+ pre-computed KPIs, handling structural nuances (like NBFC leverage).
* **Investment Screener:** Multi-parameter threshold screening.
* **Peer Intelligence:** Percentile ranking within 11 distinct GICS-style industry groups.

**👈 Select an analytical module from the sidebar to begin.**
""")

st.info("CONFIDENTIAL · INTERNAL USE ONLY · v1.2")