# src/analytics/ratios.py
import os
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")

def compute_ratios():
    print("🧮 Initializing Financial Ratio Engine (Sprint 2)...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    except Exception as e:
        print(f"❌ Database error. Did the ETL loader finish successfully? {e}")
        return
    
    # FIX: Standardize column names (lowercase, replace spaces) 
    # and ensure the ID column is consistently named 'company_id'
    for d in [pl, bs, cf]:
        d.columns = d.columns.str.strip().str.lower().str.replace(' ', '_')
        if 'id' in d.columns and 'company_id' not in d.columns:
            d.rename(columns={'id': 'company_id'}, inplace=True)
    
    # Merge tables on company_id and year
    try:
        df = pd.merge(pl, bs, on=["company_id", "year"], how="inner")
        df = pd.merge(df, cf, on=["company_id", "year"], how="inner")
    except KeyError as e:
        print(f"❌ Merge error: Could not find column {e} in the data.")
        print(f"Available columns: {list(pl.columns)}")
        return
    
    # Calculate True Equity using the exact database columns
    df['total_equity'] = df.get('equity_capital', 0) + df.get('reserves', 0)

    # Safely compute KPIs (avoiding division by zero)
    df['return_on_equity_pct'] = np.where(df['total_equity'] > 0, (df.get('net_profit', 0) / df['total_equity']) * 100, 0)
    
    df['return_on_capital_employed_pct'] = np.where((df['total_equity'] + df.get('borrowings', 0)) > 0, 
                                                    (df.get('operating_profit', 0) / (df['total_equity'] + df.get('borrowings', 1))) * 100, 0)
                                                    
    df['operating_profit_margin_pct'] = np.where(df.get('sales', 0) > 0, (df.get('operating_profit', 0) / df.get('sales', 1)) * 100, 0)
    
    df['net_profit_margin_pct'] = np.where(df.get('sales', 0) > 0, (df.get('net_profit', 0) / df.get('sales', 1)) * 100, 0)
    
    df['debt_to_equity'] = np.where(df['total_equity'] > 0, df.get('borrowings', 0) / df['total_equity'], 0)
    
    # Proxy for FCF since exact cash flow columns are missing from the DB schema
    df['free_cash_flow_cr'] = df.get('net_profit', 0) + df.get('depreciation', 0)
    
    # Fill missing CAGR columns required by the peer engine radar charts
    df['pat_cagr_5yr'] = 0.0 
    df['revenue_cagr_5yr'] = 0.0
    df['eps_cagr_5yr'] = 0.0

    # Save to SQLite
    df.to_sql("computed_financial_ratios", conn, if_exists="replace", index=False)
    conn.close()
    print(f"✅ Generated {len(df)} financial ratio records across all years.")

if __name__ == "__main__":
    compute_ratios()