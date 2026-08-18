from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    assert len(response.json()["sectors"]) == 11

def test_get_sector_companies():
    response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code == 200
    assert response.json()["sector"] == "IT"
