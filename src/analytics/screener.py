import os
import sqlite3
import pandas as pd

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_screener():
    print("🔎 Running Investment Screener (Sprint 3)...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        ratios_df = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
        companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    finally:
        conn.close()
        
    latest_ratios = ratios_df.sort_values('year').groupby('company_id').tail(1)
    
    print(f"🔗 Attempting merge using exact columns: 'company_id' and 'company_name'...")
    
    try:
        # We explicitly define the columns we now know exist
        df = pd.merge(
            latest_ratios, 
            companies_df[['company_id', 'company_name']], 
            on='company_id', 
            how='inner'
        )
    except Exception as e:
        print(f"❌ Merge failed. Error: {e}")
        return
        
    # Apply screening thresholds (ROE > 15%, Debt/Equity < 1.0)
    screened_df = df[
        (df['return_on_equity_pct'] >= 15.0) & 
        (df['debt_to_equity'] <= 1.0)
    ]
    
    print(f"🎯 Screener identified {len(screened_df)} candidate companies out of {len(df)}.")
    
    out_path = os.path.join(OUTPUT_DIR, "screened_candidates.xlsx")
    screened_df.to_excel(out_path, index=False)
    print(f"✅ Screener results saved to {out_path}")

if __name__ == "__main__":
    run_screener()