import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/companies/{ticker}/documents")
def get_documents(ticker: str):
    return {
        "company": ticker.upper(),
        "documents": [
            {"year": 2024, "type": "Annual Report", "url": "https://example.com/ar2024.pdf", "is_url_valid": True},
            {"year": 2023, "type": "Annual Report", "url": "https://example.com/ar2023.pdf", "is_url_valid": True}
        ]
    }