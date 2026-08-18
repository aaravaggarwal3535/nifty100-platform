import os
import time

BASE_DIR = os.getcwd()
API_DIR = os.path.join(BASE_DIR, "src", "api")
ROUTERS_DIR = os.path.join(API_DIR, "routers")

os.makedirs(ROUTERS_DIR, exist_ok=True)

# 1. Create Empty Dummy Routers
router_names = ["companies", "screener", "sectors", "peers", "valuation", "portfolio", "documents"]
for r_name in router_names:
    with open(os.path.join(ROUTERS_DIR, f"{r_name}.py"), "w") as f:
        f.write(f"from fastapi import APIRouter\n\nrouter = APIRouter()\n")

# 2. Write routers/health.py
health_code = """import sqlite3
import time
import os
from fastapi import APIRouter

router = APIRouter()
START_TIME = time.time()
DB_PATH = os.path.join(os.getcwd(), "data", "nifty100.db")

@router.get("/health")
def health_check():
uptime = round(time.time() - START_TIME, 2)
db_row_counts = {}

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Dynamically fetch all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        db_row_counts[table_name] = cursor.fetchone()[0]
        
    conn.close()
    db_status = "ok"
except Exception as e:
    db_status = f"error: {str(e)}"

return {
    "status": "ok",
    "version": "1.0.0",
    "uptime_seconds": uptime,
    "database": db_status,
    "db_row_counts": db_row_counts
}
"""
with open(os.path.join(ROUTERS_DIR, "health.py"), "w") as f:
    f.write(health_code)

# 3. Write main.py with Middleware
main_code = """import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import health, companies, screener, sectors, peers, valuation, portfolio, documents

app = FastAPI(title="Nifty 100 Financial API", version="1.0.0")

# CORS Middleware (Internal Use)
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
start_time = time.time()
response = await call_next(request)
process_time = time.time() - start_time
print(f"INFO:     {request.method} {request.url.path} - Completed in {process_time:.4f}s")
return response

# Include all routers
api_prefix = "/api/v1"
app.include_router(health.router, prefix=api_prefix, tags=["Health"])
app.include_router(companies.router, prefix=api_prefix, tags=["Companies"])
app.include_router(screener.router, prefix=api_prefix, tags=["Screener"])
app.include_router(sectors.router, prefix=api_prefix, tags=["Sectors"])
app.include_router(peers.router, prefix=api_prefix, tags=["Peers"])
app.include_router(valuation.router, prefix=api_prefix, tags=["Valuation"])
app.include_router(portfolio.router, prefix=api_prefix, tags=["Portfolio"])
app.include_router(documents.router, prefix=api_prefix, tags=["Documents"])
"""
with open(os.path.join(API_DIR, "main.py"), "w") as f:
    f.write(main_code)

print("✅ FastAPI structure successfully scaffolded in src/api/")

if __name__ == "__main__":
    pass