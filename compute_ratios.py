import os
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "data", "nifty100.db")

def compute_financial_ratios():
    print("⚡ Extracting financial records from SQLite...")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Pull core time-series frames
    pl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    
    # 2. Harmonize data frames onto a unified master table via structural composite key
    merged = pd.merge(pl_df, bs_df, on=["company_id", "year"], suffixes=("_pl", "_bs"))
    merged = pd.merge(merged, cf_df, on=["company_id", "year"], suffixes=("", "_cf"))
    merged = pd.merge(merged, sec_df, on="company_id", how="left")
    
    # Sort chronologically to safely compute historical windows for growth metrics
    merged = merged.sort_values(by=["company_id", "year"]).reset_index(drop=True)
    
    # Pre-allocating lists to capture calculation tracking and outliers
    ratio_records = []
    allocation_records = []
    edge_cases_log = []
    
    print("📈 Processing granular KPI calculations...")
    
    # Helper to calculate CAGR with the specialized Section 23.1 Decision Table logic
    def calculate_cagr(df_group, column, periods):
        cagr_series = [None] * len(df_group)
        vals = df_group[column].values
        
        for i in range(len(df_group)):
            if i < periods:
                continue  # INSUFFICIENT history flag
            start_val = vals[i - periods]
            end_val = vals[i]
            
            if start_val <= 0 and end_val > 0:
                edge_cases_log.append(f"{df_group['company_id'].iloc[i]} at index {i}: TURNAROUND flag on {column}")
                continue
            elif start_val > 0 and end_val < 0:
                continue # DECLINE_TO_LOSS
            elif start_val <= 0 and end_val <= 0:
                continue # BOTH_NEGATIVE / ZERO_BASE
                
            # Valid forward computation range
            cagr_series[i] = ((end_val / start_val) ** (1 / periods) - 1) * 100
        return cagr_series

    # Grouping pipeline to evaluate across individual company groups
    for company_id, group in merged.groupby("company_id"):
        group = group.copy()
        
        # Safe calculations protecting denominator constraints
        sales = group["sales"].replace(0, np.nan)
        pat = group["net_profit"].replace(0, np.nan)
        assets = group["total_assets"].replace(0, np.nan)
        
        # Equity = Equity Capital + Reserves
        equity = group["equity_capital"] + group["reserves"]
        safe_equity = equity.apply(lambda x: np.nan if x <= 0 else x)
        
        # Total Capital Employed = Equity + Borrowings
        capital_employed = (equity + group["borrowings"]).apply(lambda x: np.nan if x <= 0 else x)
        
        # Core Operating Profit / EBIT Proxy
        ebit = group["operating_profit"] - group["depreciation"].fillna(0)
        
        # 3. Direct Key Performance Indicator Generation 
        group["net_profit_margin_pct"] = (group["net_profit"] / sales) * 100
        group["operating_profit_margin_pct"] = (group["operating_profit"] / sales) * 100
        group["return_on_equity_pct"] = (group["net_profit"] / safe_equity) * 100
        group["return_on_capital_employed_pct"] = (ebit / capital_employed) * 100
        group["asset_turnover"] = group["sales"] / assets
        
        # Leverage Rules (handling structural financial firms carve-out limits)
        is_financial = str(group["broad_sector"].iloc[0]).strip().lower() == "financials"
        group["debt_to_equity"] = group["borrowings"] / safe_equity.fillna(1)
        
        # Interest Coverage Ratio
        interest = group["interest"].fillna(0)
        group["interest_coverage"] = np.where(interest == 0, 999.0, (group["operating_profit"] + group["other_income"].fillna(0)) / interest.replace(0, 1))
        
        # Cash Flow & Capital Intensities
        group["free_cash_flow_cr"] = group["operating_activity"] + group["investing_activity"]
        group["capex_cr"] = group["investing_activity"].abs()
        group["cfo_to_pat_ratio"] = group["operating_activity"] / pat
        group["capex_intensity"] = (group["capex_cr"] / sales) * 100
        group["fcf_conversion_rate"] = (group["free_cash_flow_cr"] / group["operating_profit"].replace(0, np.nan)) * 100
        
        # 4. Multi-Period CAGR Metrics
        group["revenue_cagr_3yr"] = calculate_cagr(group, "sales", 3)
        group["revenue_cagr_5yr"] = calculate_cagr(group, "sales", 5)
        group["pat_cagr_3yr"] = calculate_cagr(group, "net_profit", 3)
        group["pat_cagr_5yr"] = calculate_cagr(group, "net_profit", 5)
        
        # 5. Capital Allocation Classification Engine Matrix (Section 13 Signs Matrix)
        for idx, row in group.iterrows():
            cfo_s = "+" if row["operating_activity"] >= 0 else "-"
            cfi_s = "+" if row["investing_activity"] >= 0 else "-"
            cff_s = "+" if row["financing_activity"] >= 0 else "-"
            
            # Map pattern classes
            if cfo_s == "+" and cfi_s == "-" and cff_s == "-":
                pattern = "Reinvestor / Shareholder Returns"
            elif cfo_s == "-" and cff_s == "+":
                pattern = "Distress Signal"
            else:
                pattern = "Operations Balanced Strategy"
                
            allocation_records.append({
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": cfo_s, "cfi_sign": cfi_s, "cff_sign": cff_s,
                "pattern_label": pattern
            })
            
        ratio_records.append(group)
        
    # Combine individual groups back together safely
    final_ratios_df = pd.concat(ratio_records, ignore_index=True)
    final_allocation_df = pd.DataFrame(allocation_records)
    
    # 6. Push data out to DB Engine Persistent Storage
    final_ratios_df.to_sql("computed_financial_ratios", conn, if_exists="replace", index=False)
    final_allocation_df.to_sql("capital_allocation", conn, if_exists="replace", index=False)
    
    # Write Out Logs
    with open(os.path.join(BASE_DIR, "ratio_edge_cases.log"), "w") as f:
        f.write("\n".join(edge_cases_log))
        
    conn.close()
    print(f"🎉 Ratio engine execution complete. Generated metrics for {len(final_ratios_df)} records.")

if __name__ == "__main__":
    compute_financial_ratios()