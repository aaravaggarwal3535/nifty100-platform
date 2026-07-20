# src/dashboard/pages/01_home.py
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.db import load_query

st.set_page_config(page_title="Platform Overview", page_icon="🏠", layout="wide")

st.title("🏠 Nifty 100 Portfolio Overview")
st.markdown("---")

def render_home():
    # 1. Fetch aggregate portfolio data for the latest year
    query = """
    SELECT r.return_on_equity_pct, r.debt_to_equity, r.free_cash_flow_cr, c.company_name 
    FROM computed_financial_ratios r 
    JOIN companies c ON r.company_id = c.company_id 
    INNER JOIN (
        SELECT company_id, MAX(year) as latest_year 
        FROM computed_financial_ratios 
        GROUP BY company_id
    ) max_dates ON r.company_id = max_dates.company_id AND r.year = max_dates.latest_year
    """
    df = load_query(query)
    
    if df.empty:
        st.warning("Data not found. Please ensure Sprint 2 (Ratio Engine) was executed.")
        return
        
    # 2. Compute Portfolio Metrics
    avg_roe = df["return_on_equity_pct"].mean()
    median_de = df["debt_to_equity"].median()
    total_fcf = df["free_cash_flow_cr"].sum()
    
    # 3. Render Top-Level KPI Tiles
    st.subheader("Market Health (Latest Year)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Average Nifty 100 ROE", value=f"{avg_roe:.1f}%")
    with col2:
        st.metric(label="Median Debt/Equity", value=f"{median_de:.2f}x")
    with col3:
        st.metric(label="Total Free Cash Flow", value=f"₹{total_fcf:,.0f} Cr")
        
    st.markdown("---")
    
    # 4. Render Sector Distribution Donut Chart
    st.subheader("Sector Distribution")
    sector_counts = df["company_name"].value_counts().reset_index()
    sector_counts.columns = ["Sector", "Company Count"]
    
    fig = px.pie(
        sector_counts, 
        values="Company Count", 
        names="Sector", 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig.update_layout(margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

render_home()