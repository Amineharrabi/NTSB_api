from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from .routes import download, data
import time
import logging
from typing import Dict


logger = logging.getLogger("ntsb_api.server")


app = FastAPI(
    title="NTSB API Proxy",
    version="1.0.0",
    description="Proxy wrapper around the NTSB aviation accident data API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
        },
    )

    return response


# Simple in-memory rate limiting (per-process, per-IP)
RATE_LIMIT_MAX_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_limit_store: Dict[str, Dict[str, float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    entry = _rate_limit_store.get(client_ip)
    if not entry or entry["reset"] <= now:
        _rate_limit_store[client_ip] = {"reset": now + RATE_LIMIT_WINDOW_SECONDS, "count": 0}
        entry = _rate_limit_store[client_ip]

    entry["count"] += 1
    if entry["count"] > RATE_LIMIT_MAX_REQUESTS:
        retry_after = max(0, int(entry["reset"] - now))
        return JSONResponse(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Try again later.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    response = await call_next(request)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "path": request.url.path,
        },
    )


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}


# Download (ZIP) and JSON endpoints
app.include_router(
    download.router,
    prefix="/api/v1/download",
    tags=["download"],
)
app.include_router(
    data.router,
    prefix="/api/v1",
    tags=["cases"],
)


def get_app() -> FastAPI:
    return app


def run_server() -> None:
    """Entry point for the `ntsb-server` console script."""
    import uvicorn

    uvicorn.run(
        "ntsb_api.server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )