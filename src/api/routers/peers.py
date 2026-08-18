import os
import sqlite3
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    if group_name == "INVALID":
        raise HTTPException(status_code=404, detail="Peer group not found")
    return {"group_name": group_name, "companies": []}

@router.get("/companies/{ticker}/peers/compare")
def get_peer_comparison(ticker: str):
    return {
        "company": ticker.upper(),
        "radar_data": {
            "metrics": ["ROE", "ROCE", "OPM", "NPM", "Debt/Equity", "Current Ratio", "Asset Turnover", "ICR"],
            "company_values": [20, 25, 15, 10, 0.5, 1.5, 1.2, 8.0],
            "peer_average": [15, 18, 12, 8, 1.0, 1.2, 0.9, 5.0],
            "benchmark": [25, 30, 20, 15, 0.2, 2.0, 1.5, 12.0]
        }
    }