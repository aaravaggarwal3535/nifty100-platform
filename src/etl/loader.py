import os
import re
import sqlite3
import pandas as pd
import numpy as np

# 1. Define Project Structure Paths
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
SUPPORTING_DIR = os.path.join(BASE_DIR, "supporting datasets")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Core directories deployment
for folder in ["data", "src/etl", "src/analytics", "src/api", "src/dashboard", "tests", "reports/tearsheets", "reports/sector", "reports/portfolio"]:
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "nifty100.db")

# 2. Advanced Year Normalizer Function (Handles Section 23 specifications)
def normalize_year(year_val) -> str:
    if pd.isna(year_val):
        return "PARSE_ERROR"
    
    val_str = str(year_val).strip()
    
    # Pattern: Mar-23, Dec-22, Jun-23
    match_alpha = re.match(r'^([A-Za-z]+)[-\s](\d{2,4})$', val_str)
    if match_alpha:
        month_str, year_digits = match_alpha.groups()
        month_map = {"mar": "03", "dec": "12", "jun": "06", "sep": "09", "jan": "01"}
        month_num = month_map.get(month_str.lower()[:3], "03")
        year_num = f"20{year_digits}" if len(year_digits) == 2 else year_digits
        return f"{year_num}-{month_num}"
    
    # Pattern: 2023 or 23 (Assume standard March close for standalone integers)
    if val_str.isdigit():
        if len(val_str) == 4:
            return f"{val_str}-03"
        elif len(val_str) == 2:
            return f"20{val_str}-03"
            
    # Pattern: FY23 or FY2023
    match_fy = re.match(r'^FY\s*(\d{2,4})$', val_str, re.IGNORECASE)
    if match_fy:
        year_digits = match_fy.group(1)
        year_num = f"20{year_digits}" if len(year_digits) == 2 else year_digits
        return f"{year_num}-03"

    # Standard fallback if already formatted as YYYY-MM
    if re.match(r'^\d{4}-\d{2}$', val_str):
        return val_str
        
    return "PARSE_ERROR"

# 3. Clean Ticker / Company ID
def normalize_ticker(ticker_val) -> str:
    if pd.isna(ticker_val):
        return "MISSING"
    val = str(ticker_val).strip().upper()
    return val if 2 <= len(val) <= 12 else "REJECTED"

# 4. Ingestion Registry
core_files = {
    "companies": ("companies.xlsx", 1),
    "profitandloss": ("profitandloss.xlsx", 1),
    "balancesheet": ("balancesheet.xlsx", 1),
    "cashflow": ("cashflow.xlsx", 1),
    "analysis": ("analysis.xlsx", 1),
    "documents": ("documents.xlsx", 1),
    "prosandcons": ("prosandcons.xlsx", 1)
}

supp_files = {
    "sectors": ("sectors.xlsx", 0),
    "market_cap": ("market_cap.xlsx", 0),
    "stock_prices": ("stock_prices.xlsx", 0),
    "financial_ratios": ("financial_ratios.xlsx", 0),
    "peer_groups": ("peer_groups.xlsx", 0)
}

# Logs for audit report trail
validation_failures = []
audit_trail = []

print("🚀 Starting ETL Processing Pipeline...")

# Connect to target single-file database
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")

# Loop over files and load to dataframes
all_processed_tables = {}

for target_table, (filename, header_row) in {**core_files, **supp_files}.items():
    is_core = target_table in core_files
    folder_path = BASE_DIR if is_core else SUPPORTING_DIR
    full_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(full_path):
        print(f"⚠️ Warning: Reference path missing for {filename}")
        continue
        
    # Read payload checking metadata boundary row limits
    df = pd.read_excel(full_path, header=header_row)
    
    # Strip whitespaces from text column names
    df.columns = [str(c).strip() for c in df.columns]
    
    # Apply global Key Normalizations
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)
    elif "id" in df.columns and target_table in ["companies", "sectors"]:
        df["id"] = df["id"].apply(normalize_ticker)
        
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
    elif "Year" in df.columns: # Handle documents casing anomaly
        df["year"] = df["Year"].apply(normalize_year)
        df.drop(columns=["Year"], inplace=True)
        
    initial_rows = len(df)
    
    # --- Data Quality Checks & Validations (DQ Rules Engine) ---
    # DQ-08 Ticker/ID Filtering
    id_col = "id" if target_table in ["companies", "sectors"] else "company_id"
    if id_col in df.columns:
        invalid_ids = df[df[id_col].isin(["MISSING", "REJECTED"])]
        for _, row in invalid_ids.iterrows():
            validation_failures.append({
                "company_id": "UNKNOWN", "table": target_table, 
                "issue": "DQ-08: Invalid/Missing Ticker Format", "severity": "CRITICAL"
            })
        df = df[~df[id_col].isin(["MISSING", "REJECTED"])]

    # DQ-07 Year Filtering
    if "year" in df.columns:
        invalid_years = df[df["year"] == "PARSE_ERROR"]
        for _, row in invalid_years.iterrows():
            validation_failures.append({
                "company_id": row.get(id_col, "UNKNOWN"), "table": target_table, 
                "issue": f"DQ-07: Unparseable year layout", "severity": "CRITICAL"
            })
        df = df[df["year"] != "PARSE_ERROR"]

    # DQ-02 Deduplication implementation (Composite key constraints)
    if "company_id" in df.columns and "year" in df.columns:
        duplicates = df[df.duplicated(subset=["company_id", "year"], keep="last")]
        if len(duplicates) > 0:
            for _, row in duplicates.iterrows():
                validation_failures.append({
                    "company_id": row["company_id"], "table": target_table,
                    "issue": f"DQ-02: Duplicate time-series pair found for {row['year']}. Dropped older copy.",
                    "severity": "WARNING"
                })
            df = df.drop_duplicates(subset=["company_id", "year"], keep="last")

    # DQ-04 Balance Sheet Balancing Validation
    if target_table == "balancesheet":
        df["total_assets"] = pd.to_numeric(df["total_assets"], errors="coerce").fillna(0)
        df["total_liabilities"] = pd.to_numeric(df["total_liabilities"], errors="coerce").fillna(0)
        mismatches = df[abs(df["total_assets"] - df["total_liabilities"]) / df["total_assets"].replace(0, 1) > 0.01]
        for _, row in mismatches.iterrows():
            validation_failures.append({
                "company_id": row["company_id"], "table": target_table,
                "issue": f"DQ-04: Balance sheet variance mismatch at year {row['year']}", "severity": "WARNING"
            })

    # Save mapping back out directly to SQLite Database
    df.to_sql(target_table, conn, if_exists="replace", index=False)
    
    final_rows = len(df)
    rejected_count = initial_rows - final_rows
    audit_trail.append({
        "table": target_table, "rows_in": initial_rows, 
        "rows_out": final_rows, "rejected": rejected_count
    })
    print(f"✔️ Loaded {target_table} successfully ({final_rows} rows passed).")

# Write Quality Logs Out to Working Folder
pd.DataFrame(audit_trail).to_csv(os.path.join(BASE_DIR, "load_audit.csv"), index=False)
pd.DataFrame(validation_failures).to_csv(os.path.join(BASE_DIR, "validation_failures.csv"), index=False)

conn.close()
print("🎉 Sprint 1 Pipeline complete. 'data/nifty100.db' and quality diagnostic audit tracks are live.")