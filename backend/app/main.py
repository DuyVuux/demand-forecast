from __future__ import annotations
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .utils.logger import get_logger, setup_logging
from .routers import forecast
from .routers import sku_forecast_router
from .routers import analysis, auth

setup_logging()
logger = get_logger("app")

app = FastAPI(title="Demand Forecast API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> dict:
    return {
        "message": "Demand Forecast API",
        "endpoints": [
            "/forecast/sku",
            "/forecast/product",
            "/forecast/product_customer",
            "/forecast/product-customer/randomforest",
            "/analysis/upload",
            "/analysis/status/{job_id}",
            "/analysis/summary?job_id=...",
            "/analysis/quality?job_id=...",
            "/analysis/insights?job_id=...",
            "/analysis/correlation?job_id=...",
            "/analysis/columns/{name}?job_id=...",
            "/analysis/export/json?job_id=...",
            "/analysis/export/csv?job_id=...",
        ],
        "docs": "/docs",
    }


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("DB initialized")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = perf_counter()
    try:
        response = await call_next(request)
        duration = (perf_counter() - start) * 1000
        logger.info(
            f"{request.client.host} {request.method} {request.url.path} -> {response.status_code} ({duration:.1f} ms)"
        )
        return response
    except Exception as e:  # noqa: BLE001
        duration = (perf_counter() - start) * 1000
        logger.exception(
            f"Exception on {request.method} {request.url.path} after {duration:.1f} ms: {e}"
        )
        raise


app.include_router(forecast.router)
app.include_router(sku_forecast_router.router)
app.include_router(auth.router)
app.include_router(analysis.router)


if __name__ == "__main__":
    import uvicorn
    # Run directly with the app object to avoid import path issues
    uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)
