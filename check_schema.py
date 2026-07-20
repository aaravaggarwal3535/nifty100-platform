import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")

def check_schema():
    conn = sqlite3.connect(DB_PATH)
    
    try:
        print("🏢 COMPANIES TABLE COLUMNS:")
        print(pd.read_sql_query("PRAGMA table_info(companies)", conn)['name'].tolist())
        
        print("\n📈 PROFIT & LOSS COLUMNS:")
        print(pd.read_sql_query("PRAGMA table_info(profitandloss)", conn)['name'].tolist())
        
        print("\n⚖️ BALANCE SHEET COLUMNS:")
        print(pd.read_sql_query("PRAGMA table_info(balancesheet)", conn)['name'].tolist())
        
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()