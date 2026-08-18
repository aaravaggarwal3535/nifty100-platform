import time
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
app.include_router(companies.router, prefix=f"{api_prefix}/companies", tags=["Companies"])
app.include_router(screener.router, prefix=f"{api_prefix}", tags=["Screener"])
app.include_router(sectors.router, prefix=f"{api_prefix}", tags=["Sectors"])
app.include_router(peers.router, prefix=f"{api_prefix}", tags=["Peers"])
app.include_router(valuation.router, prefix=f"{api_prefix}", tags=["Valuation"])
app.include_router(portfolio.router, prefix=f"{api_prefix}", tags=["Portfolio"])
app.include_router(documents.router, prefix=f"{api_prefix}", tags=["Documents"])
