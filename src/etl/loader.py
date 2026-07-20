import os
import sqlite3
import pandas as pd

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")

FILES = {
    "raw": [
        "companies.xlsx", "profitandloss.xlsx", "balancesheet.xlsx", 
        "cashflow.xlsx", "analysis.xlsx", "documents.xlsx", "prosandcons.xlsx"
    ],
    "supporting": [
        "sectors.xlsx", "market_cap.xlsx", "stock_prices.xlsx", 
        "financial_ratios.xlsx", "peer_groups.xlsx"
    ]
}

def run_etl():
    print("🚀 Starting ETL Processing Pipeline...")
    conn = sqlite3.connect(DB_PATH)
    
    for folder, files in FILES.items():
        for file in files:
            file_path = os.path.join(BASE_DIR, "data", folder, file)
            table_name = file.replace(".xlsx", "")
            
            if not os.path.exists(file_path):
                continue
                
            try:
                df = pd.read_excel(file_path)
                
                # FIX: If Pandas generates "unnamed" columns, it means there is a title banner. Skip row 1.
                if any("unnamed" in str(col).lower() for col in df.columns):
                    df = pd.read_excel(file_path, header=1)
                    
                df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(' ', '_')
                
                if 'id' in df.columns and 'company_id' not in df.columns:
                    df.rename(columns={'id': 'company_id'}, inplace=True)
                    
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                print(f"✅ Loaded {file} into table '{table_name}'")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
                
    conn.close()
    print("🎉 Pipeline complete. 'data/nifty100.db' is properly structured!")

if __name__ == "__main__":
    run_etl()