import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
PORTFOLIO_DIR = os.path.join(BASE_DIR, "reports", "portfolio")
os.makedirs(PORTFOLIO_DIR, exist_ok=True)

# Reusing standard sector mapping
SECTOR_MAPPING = {
    'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS'],
    'Banking & Financials': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'BAJFINANCE', 'BAJAJFINSV', 'PFC', 'RECLTD'],
    'Automobile': ['TATAMOTORS', 'MARUTI', 'M&M', 'HEROMOTOCO', 'EICHERMOT', 'BAJAJ-AUTO', 'BOSCHLTD', 'TVSMOTOR'],
    'Oil & Gas / Energy': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'NTPC', 'POWERGRID', 'COALINDIA', 'GAIL', 'ADANIGREEN'],
    'Pharmaceuticals': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP', 'MANKIND', 'LUPIN', 'ZYDUSLIFE'],
    'Metals & Mining': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'NMDC', 'VEDL'],
    'FMCG': ['HUNVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'GODREJCP', 'COLPAL', 'VBL'],
    'Consumer Durables': ['TITAN', 'HAVELLS', 'VOLTAS', 'POLYCAB', 'DIXON', 'CROMPTON'],
    'Cement & Construction': ['ULTRACETCO', 'GRASIM', 'ACC', 'AMBUJACEM', 'DALBHARAT', 'LT'],
    'Telecom': ['BHARTIARTL', 'IDEA'],
    'Chemicals & Others': ['SRF', 'PIIND', 'UPL', 'AARTIIND', 'BERGEPAINT', 'PIDILITIND']
}

def get_sector(ticker):
    for sector, tickers in SECTOR_MAPPING.items():
        if ticker in tickers: return sector
    return "General Market"

def calculate_trend(curr, prev):
    if prev == 0 or pd.isna(prev) or pd.isna(curr): return "[FLAT]"
    change = (curr - prev) / abs(prev)
    if abs(change) <= 0.02: return "[FLAT]"
    elif change > 0: return "[UP]"
    else: return "[DOWN]"

def generate_portfolio_summary():
    print("📈 Generating Portfolio Summary PDF (Sprint 5 - Day 35)...")
    
    conn = sqlite3.connect(DB_PATH)
    companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies ORDER BY company_id ASC", conn)
    
    pdf_path = os.path.join(PORTFOLIO_DIR, "portfolio_summary.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.white, alignment=1)
    
    elements = []
    metrics = [
        ('sales', 'Revenue'), ('net_profit', 'Net Profit'), 
        ('eps', 'EPS'), ('return_on_equity_pct', 'ROE (%)'),
        ('opm_percentage', 'OPM (%)'), ('debt_to_equity', 'Debt/Equity')
    ]

    for _, row in companies_df.iterrows():
        c_id = row['company_id']
        c_name = row['company_name']
        sector = get_sector(c_id)
        
        df_ratios = pd.read_sql_query("SELECT * FROM computed_financial_ratios WHERE company_id = ? ORDER BY year ASC", conn, params=(c_id,))
        
        if len(df_ratios) < 2: continue
        
        latest = df_ratios.iloc[-1]
        previous = df_ratios.iloc[-2]

        # Header
        header = Table([[Paragraph(f"{c_name} ({c_id})", title_style)]], colWidths=[535])
        header.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.navy), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        elements.append(header)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Sector: {sector}", styles['Normal']))
        elements.append(Spacer(1, 15))

        # KPI Trend Table
        table_data = [["Metric", f"Previous ({previous['year']})", f"Latest ({latest['year']})", "Trend"]]
        
        for col, label in metrics:
            val_prev = previous.get(col, 0)
            val_curr = latest.get(col, 0)
            trend = calculate_trend(val_curr, val_prev)
            
            # Format to 2 decimal places cleanly
            table_data.append([
                label, 
                f"{val_prev:.2f}" if isinstance(val_prev, float) else str(val_prev),
                f"{val_curr:.2f}" if isinstance(val_curr, float) else str(val_curr),
                Paragraph(trend, styles['Normal'])
            ])

        kpi_table = Table(table_data, colWidths=[150, 120, 120, 100])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(kpi_table)
        elements.append(PageBreak())

    conn.close()
    doc.build(elements)
    print(f"✅ Portfolio Summary saved to {pdf_path}")

if __name__ == "__main__":
    generate_portfolio_summary()