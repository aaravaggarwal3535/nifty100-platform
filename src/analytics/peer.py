# src/analytics/peer.py
import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")
PEER_GROUPS_PATH = os.path.join(BASE_DIR, "data", "supporting", "peer_groups.xlsx")
OUTPUT_EXCEL = os.path.join(BASE_DIR, "output", "peer_comparison.xlsx")
RADAR_DIR = os.path.join(BASE_DIR, "reports", "radar_charts")

os.makedirs(RADAR_DIR, exist_ok=True)

# 2. Define the axes and their display labels dynamically
RADAR_METRICS = {
    "return_on_equity_pct": "ROE",
    "return_on_capital_employed_pct": "ROCE",
    "net_profit_margin_pct": "NPM",
    "debt_to_equity": "D/E (Inv)",
    "free_cash_flow_cr": "FCF",
    "pat_cagr_5yr": "PAT CAGR",
    "revenue_cagr_5yr": "Rev CAGR",
    "eps_cagr_5yr": "EPS CAGR"
}

def load_peer_data():
    """Loads latest ratios per company and maps them using the SQLite peer_groups table."""
    conn = sqlite3.connect(DB_PATH)
    peers_df = pd.read_sql_query("SELECT company_id, peer_group_name AS peer_group, is_benchmark FROM peer_groups", conn)
    
    query = """
    SELECT r.*, c.company_name 
    FROM computed_financial_ratios r
    JOIN companies c ON r.company_id = c.id
    INNER JOIN (
        SELECT company_id, MAX(year) as latest_year 
        FROM computed_financial_ratios 
        GROUP BY company_id
    ) max_dates ON r.company_id = max_dates.company_id AND r.year = max_dates.latest_year
    """
    ratios_df = pd.read_sql_query(query, conn)
    conn.close()
    
    peers_df["company_id"] = peers_df["company_id"].astype(str).str.strip().str.upper()
    ratios_df["company_id"] = ratios_df["company_id"].astype(str).str.strip().str.upper()
    
    merged_df = pd.merge(ratios_df, peers_df, on="company_id", how="inner")
    
    print(f"  ├─ Loaded {len(ratios_df)} unique company ratio profiles.")
    print(f"  ├─ Loaded {len(peers_df)} peer group mappings.")
    print(f"  └─ Successfully matched {len(merged_df)} companies into peer groups.")
    
    return merged_df

def compute_percentiles(df):
    ranked_df = df.copy()
    for metric in RADAR_METRICS.keys():
        if metric not in ranked_df.columns:
            continue
        ascending_order = False if metric == "debt_to_equity" else True
        col_name = f"{metric}_pctile"
        ranked_df[col_name] = ranked_df.groupby("peer_group")[metric].rank(pct=True, ascending=ascending_order).fillna(0)
    return ranked_df

def draw_radar_chart(company_row, group_avg, active_metrics, output_path):
    N = len(active_metrics)
    if N < 3: # Need at least 3 points for a polygon
        return
        
    values = [company_row[f"{m}_pctile"] for m in active_metrics]
    values += values[:1]
    
    avg_values = [group_avg[f"{m}_pctile"] for m in active_metrics]
    avg_values += avg_values[:1]
    
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    labels = [RADAR_METRICS[m] for m in active_metrics]
    plt.xticks(angles[:-1], labels, size=8)
    
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75], ["25th", "50th", "75th"], color="grey", size=7)
    plt.ylim(0, 1)
    
    ax.plot(angles, values, linewidth=2, linestyle='solid', label=company_row['company_id'], color='#1f77b4')
    ax.fill(angles, values, '#1f77b4', alpha=0.25)
    
    ax.plot(angles, avg_values, linewidth=1.5, linestyle='dashed', label='Peer Avg', color='#ff7f0e')
    
    plt.title(f"{company_row['company_name']} vs Peers", size=12, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    plt.close()

def run_peer_engine():
    print("📊 Initializing Peer Comparison Engine...")
    df = load_peer_data()
    
    if df.empty:
        print("⚠️ No peer mappings found. Check peer_groups.xlsx.")
        return
        
    print("🧮 Computing intra-group percentiles...")
    ranked_df = compute_percentiles(df)
    
    # Dynamically determine which metrics actually have percentile columns
    active_metrics = [m for m in RADAR_METRICS.keys() if f"{m}_pctile" in ranked_df.columns]
    pctile_cols = [f"{m}_pctile" for m in active_metrics]
    
    print("🕸️ Generating radar charts (this may take a moment)...")
    group_avgs = ranked_df.groupby("peer_group")[pctile_cols].mean().reset_index()
    
    for _, row in ranked_df.iterrows():
        ticker = row["company_id"]
        group = row["peer_group"]
        g_avg = group_avgs[group_avgs["peer_group"] == group].iloc[0]
        
        out_path = os.path.join(RADAR_DIR, f"{ticker}_radar.png")
        draw_radar_chart(row, g_avg, active_metrics, out_path)
        
    print(f"✔️ Saved {len(ranked_df)} radar charts to {RADAR_DIR}")
    
    print("📝 Exporting comparison workbook...")
    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        for group, group_df in ranked_df.groupby("peer_group"):
            display_cols = ["company_id", "company_name"] + active_metrics + pctile_cols
            
            # Sort by the first available metric (usually ROE)
            sort_metric = f"{active_metrics[0]}_pctile" if active_metrics else "company_id"
            display_df = group_df[display_cols].sort_values(by=sort_metric, ascending=False)
            
            display_df.to_excel(writer, sheet_name=group[:31], index=False)
            
    print(f"✅ Peer execution complete. Results saved to {OUTPUT_EXCEL}")

if __name__ == "__main__":
    run_peer_engine()