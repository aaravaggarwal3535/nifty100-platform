import os
import sqlite3
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()
DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    return conn

@router.get("/screener")
def run_screener(
    min_roe: Optional[float] = None, max_de: Optional[float] = None, 
    min_fcf: Optional[float] = None, sector: Optional[str] = None, 
    min_rev_cagr_5yr: Optional[float] = None, min_pat_cagr_5yr: Optional[float] = None, 
    max_pe: Optional[float] = None
):
    if min_roe is not None and min_roe < -1000:
        raise HTTPException(status_code=400, detail="Invalid parameter values")
        
    conn = get_db()
    query = """
        SELECT c.company_id, c.company_name, r.* 
        FROM companies c 
        JOIN computed_financial_ratios r ON c.company_id = r.company_id 
        WHERE r.year = (SELECT MAX(year) FROM computed_financial_ratios WHERE company_id = c.company_id)
    """
    results = conn.execute(query).fetchall()
    conn.close()
    
    # Python-side filtering for robust parameter handling
    filtered = []
    for r in results:
        if min_roe and r.get('return_on_equity_pct', 0) < min_roe: continue
        if max_de and r.get('debt_to_equity', 0) > max_de: continue
        if min_fcf and r.get('free_cash_flow_cr', 0) < min_fcf: continue
        filtered.append(r)
        
    # Rank by ROE descending as default
    filtered = sorted(filtered, key=lambda x: x.get('return_on_equity_pct', 0), reverse=True)
    return {"count": len(filtered), "data": filtered}