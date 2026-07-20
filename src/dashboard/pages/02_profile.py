# src/dashboard/pages/02_profile.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.db import load_query, get_all_tickers

st.set_page_config(page_title="Company Profile", page_icon="🏢", layout="wide")

st.title("🏢 Company Profile & History")
st.markdown("---")

def render_profile():
    tickers = get_all_tickers()
    if not tickers:
        st.error("No companies found in database.")
        return
        
    # 1. Selection Sidebar
    selected_ticker = st.sidebar.selectbox("Select Company Ticker", tickers)
    
    # 2. Fetch Company Master Data
    co_query = "SELECT * FROM companies WHERE company_id = ?"
    company = load_query(co_query, (selected_ticker,)).iloc[0]
    
    # Render Header Card
    st.header(company["company_name"])
    st.caption(f"Sector: {company.get('broad_sector', 'N/A')} | NSE: {company['company_id']}")
    st.write(company.get("about_company", "Description not available."))
    
    st.markdown("---")
    
    # 3. Fetch Latest KPIs
    kpi_query = """
    SELECT * FROM computed_financial_ratios 
    WHERE company_id = ? ORDER BY year DESC LIMIT 1
    """
    kpis = load_query(kpi_query, (selected_ticker,))
    
    if not kpis.empty:
        latest = kpis.iloc[0]
        st.subheader(f"Latest Financial Health ({latest['year']})")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Return on Equity", f"{latest['return_on_equity_pct']:.1f}%")
        c2.metric("Op. Profit Margin", f"{latest['operating_profit_margin_pct']:.1f}%")
        c3.metric("Debt to Equity", f"{latest['debt_to_equity']:.2f}x")
        c4.metric("Free Cash Flow", f"₹{latest['free_cash_flow_cr']:,.0f} Cr")
        
    st.markdown("---")
    
    # 4. Fetch 10-Year P&L Trend
    pl_query = """
    SELECT year, sales, net_profit 
    FROM profitandloss 
    WHERE company_id = ? ORDER BY year ASC
    """
    pl_df = load_query(pl_query, (selected_ticker,))
    
    if not pl_df.empty:
        st.subheader("10-Year Revenue & Profit Trend")
        
        # Dual-axis chart using Plotly Graph Objects
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pl_df["year"], y=pl_df["sales"], name="Revenue (₹ Cr)", marker_color='#3498db'))
        fig.add_trace(go.Scatter(x=pl_df["year"], y=pl_df["net_profit"], name="Net Profit (₹ Cr)", mode='lines+markers', marker_color='#e74c3c', yaxis='y2'))
        
        fig.update_layout(
            yaxis=dict(title="Revenue (₹ Cr)"),
            yaxis2=dict(title="Net Profit (₹ Cr)", overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=40, b=20, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

render_profile()