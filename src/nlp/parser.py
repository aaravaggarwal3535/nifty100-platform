import os
import re
import pandas as pd
import sqlite3

BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DB_PATH = os.path.join(DATA_DIR, "nifty100.db")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_parser():
    print("🧠 Running NLP Analysis Text Parser (Sprint 5 - Day 29)...")
    
    # Smart search for the file anywhere inside the data directory
    file_path = None
    for root, dirs, files in os.walk(DATA_DIR):
        if "analysis.xlsx" in files:
            file_path = os.path.join(root, "analysis.xlsx")
            break
            
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Error: Could not find analysis.xlsx anywhere in {DATA_DIR}")
        return
        
    print(f"📂 Found analysis file at: {file_path}")
    df = pd.read_excel(file_path, header=1)
    
    # ... [Keep the rest of the function exactly the same from here down]
    # Ensure 'company_id' exists
    
    # Ensure 'company_id' exists
    if 'company_id' not in df.columns:
        # Fallback if the excel uses a different identifier column
        df['company_id'] = df.index + 1 
        
    target_fields = ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
    
    # Regex: Extracts period (group 1) and value (group 2)
    # Regex: Capture (TTM|Last Year|Number) and optional negative signs
    pattern = re.compile(r"(TTM|Last Year|\d+).*?(-?[\d.]+)%", re.IGNORECASE)

    parsed_records = []
    failed_records = []

    for index, row in df.iterrows():
        c_id = row['company_id']
        
        for field in target_fields:
            if field in df.columns:
                text_val = str(row[field])
                
                if text_val.strip() == "" or text_val.lower() == "nan":
                    continue
                    
                match = pattern.search(text_val)
                
                if match:
                    period_str = match.group(1).upper()
                    # Map TTM and Last Year to 1 year for database consistency
                    period = 1 if period_str in ["TTM", "LAST YEAR"] else int(period_str)
                    value = float(match.group(2))
                    
                    parsed_records.append({
                        "company_id": c_id,
                        "metric_type": field,
                        "period_years": period,
                        "value_pct": value
                    })
                else:
                    failed_records.append({
                        "company_id": c_id,
                        "metric_type": field,
                        "raw_text": text_val
                    })

    # 1. Save Parsed Data
    parsed_df = pd.DataFrame(parsed_records)
    parsed_out = os.path.join(OUTPUT_DIR, "analysis_parsed.csv")
    parsed_df.to_csv(parsed_out, index=False)
    print(f"✅ Successfully parsed {len(parsed_df)} data points. Saved to {parsed_out}")

    # 2. Save Failures
    failures_df = pd.DataFrame(failed_records)
    if not failures_df.empty:
        fail_out = os.path.join(OUTPUT_DIR, "parse_failures.csv")
        failures_df.to_csv(fail_out, index=False)
        print(f"⚠️ Failed to parse {len(failures_df)} entries. Logged to {fail_out}")

    # 3. Cross-Validation Stub
    # Note: Connects to the computed_financial_ratios table to check for divergence
    try:
        conn = sqlite3.connect(DB_PATH)
        ratios_df = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
        print("🔄 Cross-validation ready against Ratio Engine data.")
        conn.close()
    except Exception as e:
        print(f"Database validation skipped: {e}")

if __name__ == "__main__":
    run_parser()