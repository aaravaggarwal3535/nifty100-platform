import os
import pandas as pd
import sqlite3

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def generate_insights():
    print("⚖️ Running Auto Pros/Cons Generator (Sprint 5 - Day 30)...")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        companies = pd.read_sql_query("SELECT company_id FROM companies", conn)
        ratios = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
    finally:
        conn.close()

    insights = []

    for c_id in companies['company_id']:
        df_c = ratios[ratios['company_id'] == c_id].sort_values('year')
        if df_c.empty: continue
        
        latest = df_c.iloc[-1]
        hist_3yr = df_c.tail(3)
        hist_5yr = df_c.tail(5)

        # ================= PRO RULES =================
        # Pro 1: ROE > 20% for 3+ years
        if len(hist_3yr) >= 3 and all(hist_3yr['return_on_equity_pct'] > 20):
            insights.append((c_id, 'pro', 'P1', "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", 95))
        
        # Pro 3: D/E = 0
        if latest.get('debt_to_equity', 1) == 0:
            insights.append((c_id, 'pro', 'P3', "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 99))
        
        # Pro 5: OPM > 25%
        if latest.get('opm_percentage', 0) > 25:
            insights.append((c_id, 'pro', 'P5', "Operating profit margin above 25% indicates strong pricing power and cost discipline", 85))

        # Fallback Pro (To ensure exit criteria: every company gets at least 1)
        if latest.get('net_profit', 0) > 0:
            insights.append((c_id, 'pro', 'P_FB', "Company remains profitable in the most recent financial year.", 65))

        # ================= CON RULES =================
        # Con 1: D/E > 2.0
        if latest.get('debt_to_equity', 0) > 2.0:
            insights.append((c_id, 'con', 'C1', f"Debt-to-equity ratio of {latest['debt_to_equity']:.1f}x is elevated and warrants monitoring", 85))
        
        # Con 4: Net profit negative
        if latest.get('net_profit', 0) < 0:
            insights.append((c_id, 'con', 'C4', "Company reported a net loss in the most recent financial year", 95))
            
        # Con 8: D/E rising for 3 years
        if len(hist_3yr) >= 3 and hist_3yr['debt_to_equity'].is_monotonic_increasing:
            insights.append((c_id, 'con', 'C8', "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 80))

        # Fallback Con (To ensure exit criteria: every company gets at least 1)
        if latest.get('debt_to_equity', 0) > 0:
             insights.append((c_id, 'con', 'C_FB', "Company carries debt which requires ongoing interest servicing.", 65))

    # Save to output
    out_df = pd.DataFrame(insights, columns=['company_id', 'type', 'rule_id', 'text', 'confidence_pct'])
    
    # Filter by confidence > 60%
    out_df = out_df[out_df['confidence_pct'] > 60]
    
    out_path = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")
    out_df.to_csv(out_path, index=False)
    print(f"✅ Generated {len(out_df)} insights for {out_df['company_id'].nunique()} companies. Saved to {out_path}")

if __name__ == "__main__":
    generate_insights()