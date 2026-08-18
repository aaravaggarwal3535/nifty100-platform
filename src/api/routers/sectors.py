import os
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter()
DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")

SECTOR_MAPPING = {
    'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS'],
    'Banking & Financials': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'BAJFINANCE'],
    'Automobile': ['TATAMOTORS', 'MARUTI', 'M&M', 'HEROMOTOCO', 'EICHERMOT', 'BAJAJ-AUTO'],
    'Oil & Gas / Energy': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'NTPC', 'POWERGRID'],
    'Pharmaceuticals': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'APOLLOHOSP'],
    'Metals & Mining': ['TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'COALINDIA', 'NMDC', 'VEDL'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND', 'BRITANNIA', 'DABUR', 'GODREJCP'],
    'Consumer Durables': ['TITAN', 'HAVELLS', 'VOLTAS', 'POLYCAB', 'DIXON', 'CROMPTON'],
    'Cement & Construction': ['ULTRACETCO', 'GRASIM', 'ACC', 'AMBUJACEM', 'DALBHARAT', 'LT'],
    'Telecom': ['BHARTIARTL', 'IDEA'],
    'Chemicals & Others': ['SRF', 'PIIND', 'UPL', 'AARTIIND']
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    return conn

@router.get("/sectors")
def get_sectors():
    sectors = []
    for s_name, tickers in SECTOR_MAPPING.items():
        sectors.append({
            "sector_name": s_name,
            "company_count": len(tickers),
            "median_roe": 15.5,
            "median_pe": 25.0,
            "median_de": 0.5
        })
    return {"sectors": sectors}

@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    if sector not in SECTOR_MAPPING:
        raise HTTPException(status_code=404, detail="Sector not found")
        
    tickers = SECTOR_MAPPING[sector]
    conn = get_db()
    placeholders = ",".join(["?"] * len(tickers))
    query = f"SELECT c.company_id, c.company_name, r.return_on_equity_pct, r.debt_to_equity FROM companies c JOIN computed_financial_ratios r ON c.company_id = r.company_id WHERE c.company_id IN ({placeholders}) AND r.year = (SELECT MAX(year) FROM computed_financial_ratios)"
    results = conn.execute(query, tickers).fetchall()
    conn.close()
    return {"sector": sector, "companies": results}