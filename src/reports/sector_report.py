import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
SECTOR_DIR = os.path.join(BASE_DIR, "reports", "sector")
os.makedirs(SECTOR_DIR, exist_ok=True)

# Standard Sector Mapping for Nifty 100 tickers (Fallback if DB lacks sector column)
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

def generate_sector_pdf(sector_name, tickers):
    conn = sqlite3.connect(DB_PATH)
    placeholders = ','.join(['?'] * len(tickers))
    
    query = f"""
        SELECT c.company_id, c.company_name, r.return_on_equity_pct, r.debt_to_equity, 
               r.opm_percentage, r.net_profit, r.sales, r.eps
        FROM companies c
        JOIN computed_financial_ratios r ON c.company_id = r.company_id
        WHERE c.company_id IN ({placeholders})
        AND r.year = (SELECT MAX(year) FROM computed_financial_ratios WHERE company_id = c.company_id)
    """
    df = pd.read_sql_query(query, conn, params=tickers)
    conn.close()

    if df.empty:
        return

    filename = sector_name.replace(" ", "_").replace("/", "_").lower()
    pdf_path = os.path.join(SECTOR_DIR, f"{filename}_report.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.white, alignment=1)
    
    elements = []

    # Navy Header
    header_data = [[Paragraph(f"Sector Intelligence Report: {sector_name}", title_style)]]
    header_table = Table(header_data, colWidths=[535])
    header_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.navy), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # Sector Medians
    median_roe = df['return_on_equity_pct'].median()
    median_de = df['debt_to_equity'].median()
    elements.append(Paragraph(f"Sector Overview ({len(df)} Companies): Median ROE = {median_roe:.1f}% | Median Debt/Equity = {median_de:.2f}x", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Company Summary Table
    table_data = [["Ticker", "Company Name", "ROE (%)", "D/E", "OPM (%)", "EPS"]]
    for _, r in df.iterrows():
        table_data.append([
            r['company_id'], 
            str(r['company_name'])[:20], 
            f"{r.get('return_on_equity_pct', 0):.1f}", 
            f"{r.get('debt_to_equity', 0):.2f}", 
            f"{r.get('opm_percentage', 0):.1f}", 
            f"{r.get('eps', 0):.1f}"
        ])

    comp_table = Table(table_data, colWidths=[70, 165, 70, 70, 80, 80])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke])
    ]))
    elements.append(comp_table)
    doc.build(elements)

def run_day_34_sectors():
    print("🏭 Generating 11 Sector Intelligence PDFs...")
    for sector, tickers in SECTOR_MAPPING.items():
        try:
            generate_sector_pdf(sector, tickers)
            print(f"  ✅ Sector generated: {sector}")
        except Exception as e:
            print(f"  ❌ Error generating sector {sector}: {e}")
    print(f"🎉 All sector reports saved to {SECTOR_DIR}")

if __name__ == "__main__":
    run_day_34_sectors()