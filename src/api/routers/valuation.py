import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/market-cap/{ticker}")
def get_market_cap(ticker: str):
    return {
        "company": ticker.upper(),
        "history": [
            {"year": 2024, "pe": 25.4, "pb": 4.1, "ev_ebitda": 15.2, "div_yield": 1.5},
            {"year": 2023, "pe": 22.1, "pb": 3.8, "ev_ebitda": 14.1, "div_yield": 1.6},
            {"year": 2022, "pe": 28.5, "pb": 4.5, "ev_ebitda": 17.5, "div_yield": 1.2},
        ]
    }