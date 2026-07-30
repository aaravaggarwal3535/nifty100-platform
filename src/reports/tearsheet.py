import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "reports", "tearsheets")
TEMP_DIR = os.path.join(BASE_DIR, "reports", "temp")
PROS_CONS_FILE = os.path.join(BASE_DIR, "output", "pros_cons_generated.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def generate_charts(company_id, df_ratios):
    # Temp paths
    rev_chart = os.path.join(TEMP_DIR, f"{company_id}_rev.png")
    
    # 1. Revenue & Profit Bar Chart (Simplified for template)
    plt.figure(figsize=(6, 3))
    plt.bar(df_ratios['year'], df_ratios.get('sales', 0), color='#1f77b4', label='Revenue')
    plt.plot(df_ratios['year'], df_ratios.get('net_profit', 0), color='#2ca02c', marker='o', label='Net Profit')
    plt.title('10-Year Revenue vs Profit')
    plt.legend()
    plt.tight_layout()
    plt.savefig(rev_chart)
    plt.close()
    
    return rev_chart

def build_tearsheet(company_id, company_name):
    print(f"📄 Generating Tearsheet for {company_id}...")
    
    # Fetch Data
    conn = sqlite3.connect(DB_PATH)
    df_ratios = pd.read_sql_query("SELECT * FROM computed_financial_ratios WHERE company_id = ?", conn, params=(company_id,))
    conn.close()
    
    if df_ratios.empty:
        print(f"⚠️ No data for {company_id}. Skipping.")
        return

    # Fetch Pros and Cons
    pros, cons = [], []
    if os.path.exists(PROS_CONS_FILE):
        pc_df = pd.read_csv(PROS_CONS_FILE)
        c_pc = pc_df[pc_df['company_id'] == company_id]
        pros = c_pc[c_pc['type'] == 'pro']['text'].tolist()
        cons = c_pc[c_pc['type'] == 'con']['text'].tolist()

    pdf_path = os.path.join(OUTPUT_DIR, f"{company_id}_tearsheet.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Custom Styles (WORDWRAP is handled natively by Paragraph)
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.white, alignment=1)
    pro_style = ParagraphStyle('Pro', parent=styles['Normal'], textColor=colors.green, spaceAfter=5)
    con_style = ParagraphStyle('Con', parent=styles['Normal'], textColor=colors.red, spaceAfter=5)

    elements = []

    # --- PAGE 1: Header & KPIs ---
    # Navy Header Bar
    header_data = [[Paragraph(f"{company_name} ({company_id}) - Financial Tearsheet", title_style)]]
    header_table = Table(header_data, colWidths=[535])
    header_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.navy), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # KPI Tiles (2 rows of 3)
    latest = df_ratios.iloc[-1]
    kpi_data = [
        [f"ROE: {latest.get('return_on_equity_pct', 0):.1f}%", f"D/E: {latest.get('debt_to_equity', 0):.2f}x", f"OPM: {latest.get('opm_percentage', 0):.1f}%"],
        [f"Net Profit: {latest.get('net_profit', 0)}", f"Sales: {latest.get('sales', 0)}", f"EPS: {latest.get('eps', 0)}"]
    ]
    kpi_table = Table(kpi_data, colWidths=[178, 178, 178], rowHeights=[40, 40])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, colors.white)
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 20))

    # Charts
    rev_chart_path = generate_charts(company_id, df_ratios)
    elements.append(Image(rev_chart_path, width=400, height=200))
    
    elements.append(PageBreak())

    # --- PAGE 2: Pros & Cons (Wordwrap enforced) ---
    elements.append(Paragraph("Fundamental Analysis (Pros & Cons)", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    for pro in pros:
        elements.append(Paragraph(f"• {pro}", pro_style))
    elements.append(Spacer(1, 10))
    
    for con in cons:
        elements.append(Paragraph(f"• {con}", con_style))

    doc.build(elements)
    print(f"✅ Saved: {pdf_path}")

def run_day_33():
    print("🖨️ Running PDF Tearsheet Generator (Sprint 5 - Day 33)...")
    # Test on 5 specific companies
    test_companies = {
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank Ltd",
        "RELIANCE": "Reliance Industries",
        "SUNPHARMA": "Sun Pharmaceuticals",
        "TATASTEEL": "Tata Steel"
    }
    
    for ticker, name in test_companies.items():
        build_tearsheet(ticker, name)
        
    print(f"🎉 Day 33 Complete. Check {OUTPUT_DIR} for the PDFs.")

def run_batch_tearsheets():
    print("⚡ Starting Full Batch Tearsheet Generation...")
    conn = sqlite3.connect(DB_PATH)
    companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    
    skipped = []
    generated_count = 0

    for _, row in companies_df.iterrows():
        c_id = row['company_id']
        c_name = row['company_name']
        
        # Check data history
        df_ratios = pd.read_sql_query("SELECT year FROM computed_financial_ratios WHERE company_id = ?", conn, params=(c_id,))
        
        if len(df_ratios) < 3:
            skipped.append({"company_id": c_id, "reason": f"Insufficient data history ({len(df_ratios)} years)"})
            continue
            
        try:
            build_tearsheet(c_id, c_name)
            generated_count += 1
        except Exception as e:
            print(f"❌ Failed to generate {c_id}: {e}")
            skipped.append({"company_id": c_id, "reason": str(e)})

    conn.close()

    # Save skipped list
    skipped_df = pd.DataFrame(skipped)
    skipped_path = os.path.join(BASE_DIR, "output", "skipped_tearsheets.csv")
    skipped_df.to_csv(skipped_path, index=False)
    
    print(f"\n✨ Batch Tearsheets Complete! Generated: {generated_count} | Skipped: {len(skipped)}")
    print(f"📝 Logged skipped tickers to {skipped_path}")

if __name__ == "__main__":
    run_batch_tearsheets()