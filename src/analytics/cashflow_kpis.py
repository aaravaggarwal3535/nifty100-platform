import os
import pandas as pd
import sqlite3
import numpy as np

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def run_cashflow_intelligence():
    print("🕵️ Running Cash Flow Intelligence Module (Sprint 5 - Day 31)...")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        pl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        companies = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    finally:
        conn.close()

    # Merge P&L and Balance Sheet
    df = pd.merge(pl_df, bs_df, on=['company_id', 'year'], how='inner')
    df = df.sort_values(['company_id', 'year'])

    results = []
    distress_alerts = []

    for c_id, group in df.groupby('company_id'):
        if len(group) < 2: continue
        
        # 1. Proxies for Cash Flow (since raw table is missing)
        group['cfo_proxy'] = group.get('net_profit', 0) + group.get('depreciation', 0)
        group['cff_proxy'] = group.get('borrowings', 0).diff()
        group['capex_proxy'] = group.get('fixed_assets', 0).diff()
        
        latest = group.iloc[-1]
        hist_5yr = group.tail(5)

        # 2. CFO Quality Score (Avg CFO/PAT over 5 years)
        # Avoid division by zero by replacing 0 PAT with 1
        pat_safe = np.where(hist_5yr['net_profit'] == 0, 1, hist_5yr['net_profit'])
        cfo_pat_ratio = hist_5yr['cfo_proxy'] / pat_safe
        cfo_quality_score = cfo_pat_ratio.mean()
        
        if cfo_quality_score > 1.0: cfo_label = "High Quality"
        elif cfo_quality_score >= 0.5: cfo_label = "Moderate"
        else: cfo_label = "Accrual Risk"

        # 3. CapEx Intensity (Abs(CapEx) / Sales)
        sales_safe = latest.get('sales', 1) if latest.get('sales', 0) != 0 else 1
        capex_intensity = (abs(latest.get('capex_proxy', 0)) / sales_safe) * 100
        
        if capex_intensity > 8: capex_label = "Capital Intensive"
        elif capex_intensity >= 3: capex_label = "Moderate"
        else: capex_label = "Asset Light"

        # 4. Distress Signal & Deleveraging Flags
        cfo_latest = latest.get('cfo_proxy', 0)
        cff_latest = latest.get('cff_proxy', 0)
        
        distress_flag = True if (cfo_latest < 0 and cff_latest > 0) else False
        deleveraging_flag = True if (cff_latest < 0 and latest.get('borrowings', 0) < group.iloc[-2].get('borrowings', 0)) else False

        # Compile Results
        results.append({
            "company_id": c_id,
            "cfo_quality_score": round(cfo_quality_score, 2),
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": round(capex_intensity, 2),
            "capex_label": capex_label,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag
        })

        # Log Distress Alerts
        if distress_flag:
            distress_alerts.append({
                "company_id": c_id,
                "cfo_value": cfo_latest,
                "cff_value": cff_latest,
                "latest_net_profit": latest.get('net_profit', 0)
            })

    # Save Main Report
    results_df = pd.DataFrame(results)
    # Add basic dummy columns for Sprint 5 requirements we will fill in Day 32
    results_df['fcf_cagr_5yr'] = "Pending"
    results_df['fcf_conversion_pct'] = "Pending"
    results_df['capital_allocation_label'] = "Pending"
    
    out_excel = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")
    results_df.to_excel(out_excel, index=False)
    print(f"✅ Cash Flow Intelligence saved to {out_excel}")

    # Save Distress Alerts
    alerts_df = pd.DataFrame(distress_alerts)
    alerts_csv = os.path.join(OUTPUT_DIR, "distress_alerts.csv")
    alerts_df.to_csv(alerts_csv, index=False)
    print(f"🚨 Logged {len(alerts_df)} distress alerts to {alerts_csv}")

if __name__ == "__main__":
    run_cashflow_intelligence()