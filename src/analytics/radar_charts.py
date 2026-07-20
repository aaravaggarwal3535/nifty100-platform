import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
RADAR_DIR = os.path.join(BASE_DIR, "assets", "radar_charts")

os.makedirs(RADAR_DIR, exist_ok=True)

def generate_radar_charts():
    print("🕸️ Initializing Radar Chart Generator...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        ratios_df = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
        companies_df = pd.read_sql_query("SELECT company_id, company_name FROM companies", conn)
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    finally:
        conn.close()

    # Get the latest year of data for each company
    latest_data = ratios_df.sort_values('year').groupby('company_id').tail(1)
    
    # Merge with company names
    df = pd.merge(latest_data, companies_df, on='company_id', how='inner')
    
    # Define the metrics we want to plot on the radar chart
    metrics = [
        'return_on_equity_pct', 
        'return_on_capital_employed_pct', 
        'operating_profit_margin_pct', 
        'net_profit_margin_pct'
    ]
    labels = ['ROE (%)', 'ROCE (%)', 'Op Margin (%)', 'Net Margin (%)']
    num_vars = len(labels)
    
    print(f"⚙️ Generating circular radar charts for {len(df)} companies...")
    
    count = 0
    for _, row in df.iterrows():
        comp_id = row['company_id']
        comp_name = str(row['company_name']).replace("/", "_").replace("\\", "_")
        
        # Extract values, cap them at 100 for visual consistency on the chart, and replace negatives with 0
        values = [max(0, min(100, row.get(m, 0))) for m in metrics]
        values += values[:1] # Repeat the first value to close the circle
        
        # Compute angle for each axis
        angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
        angles += angles[:1]
        
        # Initialize the spider plot
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        # Draw one axis per variable and add labels
        plt.xticks(angles[:-1], labels, color='grey', size=10)
        
        # Draw ylabels
        ax.set_rlabel_position(0)
        plt.yticks([25, 50, 75], ["25", "50", "75"], color="grey", size=8)
        plt.ylim(0, 100)
        
        # Plot data and fill area
        ax.plot(angles, values, linewidth=2, linestyle='solid', color='#1f77b4')
        ax.fill(angles, values, '#1f77b4', alpha=0.25)
        
        plt.title(f"{comp_name}\nPerformance Radar", size=14, color='black', y=1.1)
        
        # Save the chart
        file_path = os.path.join(RADAR_DIR, f"{comp_id}_radar.png")
        plt.savefig(file_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        count += 1
        
    print(f"✅ Successfully generated {count} radar charts in {RADAR_DIR}")

if __name__ == "__main__":
    generate_radar_charts()