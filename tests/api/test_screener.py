from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_screener_valid():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()["data"]
    if len(data) > 0:
        assert data[0]["return_on_equity_pct"] >= 15

def test_screener_invalid():
    response = client.get("/api/v1/screener?min_roe=-2000")
    assert response.status_code == 400
