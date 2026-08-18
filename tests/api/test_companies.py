from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert "count" in response.json()

def test_get_company_valid():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    assert response.json()["profile"]["company_id"] == "TCS"

def test_get_company_invalid():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404
