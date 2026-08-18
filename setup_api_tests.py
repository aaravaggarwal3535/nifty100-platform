import os

os.makedirs(os.path.join("tests", "api"), exist_ok=True)

test_health = '''from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "companies" in response.json()["db_row_counts"]
'''

test_companies = '''from fastapi.testclient import TestClient
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
'''

test_screener = '''from fastapi.testclient import TestClient
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
'''

test_sectors = '''from fastapi.testclient import TestClient
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
'''

with open("tests/api/test_health.py", "w") as f: f.write(test_health)
with open("tests/api/test_companies.py", "w") as f: f.write(test_companies)
with open("tests/api/test_screener.py", "w") as f: f.write(test_screener)
with open("tests/api/test_sectors.py", "w") as f: f.write(test_sectors)

print("✅ API tests scaffolded in tests/api/")