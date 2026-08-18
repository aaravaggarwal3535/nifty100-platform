import os
import sqlite3
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import zscore

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# The 10 Core KPIs for Heatmap and Stats
CORE_KPIS = [
    'return_on_equity_pct', 'return_on_capital_employed_pct', 
    'debt_to_equity', 'opm_percentage', 'net_profit_margin_pct', 
    'sales', 'net_profit', 'eps', 'free_cash_flow_cr', 'total_equity'
]

# Reusing Sector Mapping for Outlier Detection
SECTOR_MAPPING = {
    'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS'],
    'Banking & Financials': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'BAJFINANCE', 'BAJAJFINSV', 'PFC', 'RECLTD'],
    'Automobile': ['TATAMOTORS', 'MARUTI', 'M&M', 'HEROMOTOCO', 'EICHERMOT', 'BAJAJ-AUTO', 'BOSCHLTD', 'TVSMOTOR'],
    'Oil & Gas / Energy': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'NTPC', 'POWERGRID', 'COALINDIA', 'GAIL', 'ADANIGREEN'],
    'Pharmaceuticals': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP', 'MANKIND', 'LUPIN', 'ZYDUSLIFE'],
    'Metals & Mining': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'NMDC', 'VEDL'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'GODREJCP', 'COLPAL', 'VBL'],
    'Consumer Durables': ['TITAN', 'HAVELLS', 'VOLTAS', 'POLYCAB', 'DIXON', 'CROMPTON'],
    'Cement & Construction': ['ULTRACETCO', 'GRASIM', 'ACC', 'AMBUJACEM', 'DALBHARAT', 'LT'],
    'Telecom': ['BHARTIARTL', 'IDEA'],
    'Chemicals & Others': ['SRF', 'PIIND', 'UPL', 'AARTIIND', 'BERGEPAINT', 'PIDILITIND']
}

def get_sector(ticker):
    for sector, tickers in SECTOR_MAPPING.items():
        if ticker in tickers: return sector
    return "General Market"

def run_profiling():
    print("📊 Running Cluster Profiling & Statistics (Sprint 6 - Day 37)...")
    
    # 1. Fetch Latest Financial Data
    conn = sqlite3.connect(DB_PATH)
    df_ratios = pd.read_sql_query("SELECT * FROM computed_financial_ratios", conn)
    conn.close()

    latest_df = df_ratios.sort_values('year').drop_duplicates('company_id', keep='last').copy()
    latest_df['broad_sector'] = latest_df['company_id'].apply(get_sector)

    # 2. Cluster Profiling & Renaming
    cluster_file = os.path.join(OUTPUT_DIR, "cluster_labels.csv")
    if os.path.exists(cluster_file):
        clusters_df = pd.read_csv(cluster_file)
        merged_df = pd.merge(latest_df, clusters_df[['company_id', 'cluster_id']], on='company_id', how='inner')
        
        # Compute Mean and Median for profiling
        profile_features = ['return_on_equity_pct', 'debt_to_equity', 'opm_percentage']
        cluster_profiles = merged_df.groupby('cluster_id')[profile_features].agg(['mean', 'median'])
        print("\n🔍 Cluster Profiles (Mean & Median):")
        print(cluster_profiles.to_string())

        # Assign Descriptive Names (Dynamic rule-based approach)
        cluster_names = {}
        for cluster_id, row in cluster_profiles.iterrows():
            roe_mean = row[('return_on_equity_pct', 'mean')]
            de_mean = row[('debt_to_equity', 'mean')]
            
            if roe_mean > 20 and de_mean < 0.5:
                name = "High-Quality Compounders"
            elif de_mean > 1.5:
                name = "Distressed or Turnaround"
            elif roe_mean < 12 and de_mean < 1.0:
                name = "Defensive Value"
            elif roe_mean >= 15:
                name = "Emerging Growth"
            else:
                name = "Value Cyclicals"
            cluster_names[cluster_id] = name

        # Update cluster_labels.csv with real names
        clusters_df['cluster_name'] = clusters_df['cluster_id'].map(cluster_names)
        clusters_df.to_csv(cluster_file, index=False)
        print(f"\n✅ Updated cluster names in {cluster_file}")
    else:
        print("⚠️ cluster_labels.csv not found! Run Day 36 first.")
        merged_df = latest_df # Fallback

    # 3. Correlation Matrix Heatmap
    corr_matrix = merged_df[CORE_KPIS].corr(method='pearson')
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, square=True)
    plt.title("Pearson Correlation of 10 Core KPIs (Nifty 100)")
    plt.tight_layout()
    heatmap_path = os.path.join(REPORTS_DIR, "correlation_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()
    print(f"🔥 Correlation heatmap saved to {heatmap_path}")

    # 4. Outlier Detection (Z-Score > 3 per sector)
    outliers = []
    for sector, group in merged_df.groupby('broad_sector'):
        if len(group) < 3: continue # Not enough data for z-score
        
        for kpi in CORE_KPIS:
            # Safely calculate Z-scores avoiding NaNs and zero-variance
            valid_data = group[kpi].dropna()
            if len(valid_data) > 2 and valid_data.std() > 0:
                z_scores = zscore(valid_data)
                abs_z = np.abs(z_scores)
                
                # Find outliers
                outlier_indices = valid_data[abs_z > 3].index
                for idx in outlier_indices:
                    outliers.append({
                        'company_id': group.loc[idx, 'company_id'],
                        'broad_sector': sector,
                        'metric': kpi,
                        'value': group.loc[idx, kpi],
                        'z_score': round(zscore(valid_data)[valid_data.index == idx][0], 2)
                    })

    outlier_df = pd.DataFrame(outliers)
    outlier_path = os.path.join(OUTPUT_DIR, "outlier_report.csv")
    outlier_df.to_csv(outlier_path, index=False)
    print(f"🚨 Flagged {len(outlier_df)} statistical outliers. Saved to {outlier_path}")

    # 5. Portfolio Statistics (P10 to P90)
    stats_df = merged_df[CORE_KPIS].describe(percentiles=[0.10, 0.25, 0.50, 0.75, 0.90]).T
    stats_df = stats_df[['mean', 'std', '10%', '25%', '50%', '75%', '90%']]
    stats_path = os.path.join(OUTPUT_DIR, "portfolio_stats.csv")
    stats_df.to_csv(stats_path)
    print(f"📈 Portfolio stats (P10 to P90) saved to {stats_path}")

if __name__ == "__main__":
    run_profiling()