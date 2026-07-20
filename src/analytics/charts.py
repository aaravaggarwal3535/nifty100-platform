# src/analytics/charts.py
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
CHARTS_DIR = os.path.join(BASE_DIR, "assets", "charts")

# Ensure the output directory exists
os.makedirs(CHARTS_DIR, exist_ok=True)

def generate_charts():
    print("📊 Initializing Automated Chart Generator...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        ratios_df = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
        companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    finally:
        conn.close()

    print(f"⚙️ Generating charts for {len(companies_df)} companies...")
    
    count = 0
    for _, company in companies_df.iterrows():
        comp_id = company['company_id']
        # Sanitize the company name so it can be safely used as a file name
        comp_name = str(company['company_name']).replace("/", "_").replace("\\", "_")
        
        comp_data = ratios_df[ratios_df['company_id'] == comp_id].sort_values('year')
        
        if comp_data.empty:
            continue
            
        plt.figure(figsize=(8, 5))
        
        # Plot Revenue (sales) and Net Profit
        if 'sales' in comp_data.columns:
            plt.plot(comp_data['year'], comp_data['sales'], marker='o', label='Revenue', color='#1f77b4', linewidth=2)
        if 'net_profit' in comp_data.columns:
            plt.plot(comp_data['year'], comp_data['net_profit'], marker='s', label='Net Profit', color='#2ca02c', linewidth=2)
        
        plt.title(f"{comp_name} - Financial Trend", fontsize=12, fontweight='bold')
        plt.xlabel("Year")
        plt.ylabel("Amount (Cr)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        
        file_path = os.path.join(CHARTS_DIR, f"{comp_id}_chart.png")
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()
        count += 1
        
    print(f"✅ Successfully generated and saved {count} charts to {CHARTS_DIR}")

if __name__ == "__main__":
    generate_charts()