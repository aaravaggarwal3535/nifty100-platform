import os
import sqlite3
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

router = APIRouter()
DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")
TEARSHEETS_DIR = os.path.join(os.getcwd(), "reports", "tearsheets")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    # Return rows as dictionaries instead of tuples for instant JSON serialization
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    return conn

@router.get("/")
def get_all_companies(
    sector: Optional[str] = None, 
    search: Optional[str] = None
):
    conn = get_db()
    query = """
        SELECT c.company_id, c.company_name, 
               r.return_on_equity_pct as roe_pct, r.return_on_capital_employed_pct as roce_pct
        FROM companies c
        LEFT JOIN computed_financial_ratios r ON c.company_id = r.company_id
        WHERE r.year = (SELECT MAX(year) FROM computed_financial_ratios WHERE company_id = c.company_id)
    """
    params = []

    if search:
        query += " AND (c.company_id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    # Execute query
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    return {"count": len(results), "data": results}

@router.get("/{ticker}")
def get_company_profile(ticker: str):
    conn = get_db()
    company = conn.execute("SELECT * FROM companies WHERE company_id = ?", (ticker.upper(),)).fetchone()
    
    if not company:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
        
    latest_ratios = conn.execute(
        "SELECT * FROM computed_financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", 
        (ticker.upper(),)
    ).fetchone()
    conn.close()
    
    return {"profile": company, "latest_kpis": latest_ratios}

# Helper function for historical data endpoints
def fetch_history(ticker: str, table_name: str, from_year: Optional[str], to_year: Optional[str]):
    conn = get_db()
    query = f"SELECT * FROM {table_name} WHERE company_id = ?"
    params = [ticker.upper()]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
        
    query += " ORDER BY year ASC"
    results = conn.execute(query, params).fetchall()
    conn.close()
    return results

@router.get("/{ticker}/pl")
def get_profit_and_loss(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    return {"company_id": ticker.upper(), "history": fetch_history(ticker, "profitandloss", from_year, to_year)}

@router.get("/{ticker}/bs")
def get_balance_sheet(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    return {"company_id": ticker.upper(), "history": fetch_history(ticker, "balancesheet", from_year, to_year)}

@router.get("/{ticker}/cashflow")
def get_cashflow(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    return {"company_id": ticker.upper(), "history": fetch_history(ticker, "cashflow", from_year, to_year)}

@router.get("/{ticker}/ratios")
def get_ratios(ticker: str, year: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM computed_financial_ratios WHERE company_id = ?"
    params = [ticker.upper()]
    
    if year:
        query += " AND year = ?"
        params.append(year)
        
    query += " ORDER BY year ASC"
    results = conn.execute(query, params).fetchall()
    conn.close()
    return {"company_id": ticker.upper(), "data": results}

@router.get("/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    file_path = os.path.join(TEARSHEETS_DIR, f"{ticker.upper()}_tearsheet.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Tearsheet PDF not found for this company")
        
    return FileResponse(
        path=file_path, 
        media_type="application/pdf", 
        filename=f"{ticker.upper()}_Tearsheet.pdf"
    )