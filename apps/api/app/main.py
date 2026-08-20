from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.router import router as api_router
from app.core.config import get_settings
from app.db.session import SessionLocal, create_schema
from app.services.demo_seed import seed_demo

settings = get_settings()
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=0.05,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_schema()
    if settings.data_mode == "demo" and not settings.is_production:
        async with SessionLocal() as session:
            await seed_demo(session, settings)
    yield


app = FastAPI(
    title="EquityLens API",
    version="0.1.0",
    description="Explainable, deterministic equity research. For education and research only.",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-Id", "X-Anonymous-Id"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))[:80]
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


def error_payload(
    request: Request, code: str, message: str, details: object = None
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        }
    }


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> ORJSONResponse:
    return ORJSONResponse(
        error_payload(request, f"HTTP_{exc.status_code}", str(exc.detail)),
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    safe_details = [
        {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return ORJSONResponse(
        error_payload(request, "VALIDATION_ERROR", "Request validation failed", safe_details),
        status_code=422,
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> ORJSONResponse:
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    return ORJSONResponse(
        error_payload(request, "INTERNAL_ERROR", "The request could not be completed"),
        status_code=500,
    )


@app.get("/api/v1/health/live", tags=["health"])
async def health_live() -> dict[str, str]:
    return {"status": "alive", "version": app.version}


@app.get("/api/v1/health/ready", tags=["health"])
async def health_ready() -> ORJSONResponse:
    checks: dict[str, str] = {}
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except Exception:
        checks["database"] = "unavailable"
    try:
        redis = Redis.from_url(settings.redis_url, socket_connect_timeout=0.4, socket_timeout=0.4)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = "ready"
    except Exception:
        checks["redis"] = "unavailable"
    required_ready = checks["database"] == "ready" and (
        not settings.require_redis or checks["redis"] == "ready"
    )
    return ORJSONResponse(
        {"status": "ready" if required_ready else "not_ready", "checks": checks},
        status_code=200 if required_ready else 503,
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "EquityLens API", "docs": "/api/docs", "health": "/api/v1/health/ready"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")
