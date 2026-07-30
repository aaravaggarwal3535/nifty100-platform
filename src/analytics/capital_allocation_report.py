import os
import pandas as pd
import sqlite3

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
CAP_ALLOC_FILE = os.path.join(OUTPUT_DIR, "capital_allocation.csv")
CF_INTEL_FILE = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")

def run_day_32():
    print("📊 Running Capital Allocation Report (Sprint 5 - Day 32)...")
    
    # 1. Verify / Rebuild Capital Allocation Data
    if not os.path.exists(CAP_ALLOC_FILE):
        print("⚠️ Sprint 2 capital_allocation.csv missing (likely from PC reset). Rebuilding...")
        conn = sqlite3.connect(DB_PATH)
        df_all = pd.read_sql_query("SELECT company_id, year, return_on_equity_pct, debt_to_equity FROM computed_financial_ratios ORDER BY company_id, year", conn)
        conn.close()
        
        # Rebuilding basic patterns to unblock the pipeline
        def assign_pattern(row):
            if row['return_on_equity_pct'] > 15 and row['debt_to_equity'] < 0.5: return 'Reinvestor'
            if row['return_on_equity_pct'] < 10 and row['debt_to_equity'] > 1.5: return 'Distress Signal'
            if row['debt_to_equity'] == 0: return 'Conservative'
            return 'Standard'
            
        df_all['pattern'] = df_all.apply(assign_pattern, axis=1)
        df_all.to_csv(CAP_ALLOC_FILE, index=False)
        df = df_all
    else:
        df = pd.read_csv(CAP_ALLOC_FILE)
        df = df.sort_values(['company_id', 'year'])

    # 2. Distribution Summary (Latest Year)
    latest_year_df = df.drop_duplicates(subset=['company_id'], keep='last')
    print("\n📈 Latest Year Pattern Distribution:")
    print(latest_year_df['pattern'].value_counts().to_string())

    # 3. Add to Cash Flow Intelligence File
    if os.path.exists(CF_INTEL_FILE):
        cf_df = pd.read_excel(CF_INTEL_FILE)
        
        # Map the latest pattern to the existing companies
        pattern_map = latest_year_df.set_index('company_id')['pattern'].to_dict()
        cf_df['capital_allocation_label'] = cf_df['company_id'].map(pattern_map).fillna("Unknown")
        
        cf_df.to_excel(CF_INTEL_FILE, index=False)
        print(f"\n✅ Updated {CF_INTEL_FILE} with capital allocation labels.")
    else:
        print(f"\n❌ Error: {CF_INTEL_FILE} not found. Did Day 31 run successfully?")

    # 4. Pattern Changes YoY
    changes = []
    for c_id, group in df.groupby('company_id'):
        if len(group) >= 2:
            prev = group.iloc[-2]['pattern']
            curr = group.iloc[-1]['pattern']
            if prev != curr:
                changes.append({
                    'company_id': c_id,
                    'previous_pattern': prev,
                    'current_pattern': curr
                })
                
    changes_df = pd.DataFrame(changes)
    changes_out = os.path.join(OUTPUT_DIR, "pattern_changes.csv")
    changes_df.to_csv(changes_out, index=False)
    print(f"🔄 Logged {len(changes_df)} year-over-year pattern changes to {changes_out}")

if __name__ == "__main__":
    run_day_32()