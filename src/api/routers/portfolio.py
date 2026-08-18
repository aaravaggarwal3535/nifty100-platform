import os
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()
STATS_FILE = os.path.join(os.getcwd(), "output", "portfolio_stats.csv")

@router.get("/portfolio/stats")
def get_portfolio_stats():
    if not os.path.exists(STATS_FILE):
        raise HTTPException(status_code=404, detail="Stats file not found")
    df = pd.read_csv(STATS_FILE, index_col=0)
    return {"metrics": df.to_dict(orient="index")}