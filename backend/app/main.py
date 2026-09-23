"""
CloudContextGuard FastAPI application.

Step 2 built the application wiring, database initialization, CORS, logging
and a health endpoint. Step 3 adds the security intelligence layer: the
IAM/VPC/resource-policy/risk engines, the central decision engine, the
access-control API and the dashboard aggregation - wired in via the routers
in ``app.api``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.api import access, catalog, database, dashboard, policies, security
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.db.database import SessionLocal, init_db, is_database_connected
from app.schemas.health import HealthResponse
from app.services.seed_service import ensure_contractor_identity, seed_if_empty

settings = get_settings()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("%s starting up (env=%s)", settings.APP_NAME, settings.APP_ENV)
    try:
        init_db()
        logger.info("Database initialized at %s", settings.database_path)
    except Exception:
        logger.exception("Database initialization failed")
        raise
    db = SessionLocal()
    try:
        if seed_if_empty(db):
            logger.info("Database was empty; seeded reference catalog")
        if ensure_contractor_identity(db):
            logger.info("Ensured contractor01/ContractorRole demonstration identity")
    except Exception:
        logger.exception("Database seeding failed")
        raise
    finally:
        db.close()
    yield
    logger.info("%s shutting down", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS: an explicit origin allowlist (the local Vite dev server), never
# "*". allow_credentials=True combined with a wildcard origin is both
# unsafe and rejected by browsers outright; an explicit allowlist is the
# correct pattern regardless of credentials, and is what lets the frontend
# (a different origin: 5173 vs the API's 8000) call this API at all.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Attach baseline defensive headers to every response.

    Deliberately minimal for a local single-page-app backend: these three
    are safe, low-complexity, and don't affect the API or the React
    frontend's normal operation (no inline framing or MIME-sniffing is
    relied upon anywhere in this app).
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


# Rate limiting: not implemented. This is a local, single-user simulation
# with no authentication boundary to protect against brute-forcing, so it
# has not been prioritized for this academic project. Rate limiting is a
# future production-hardening measure.

app.include_router(access.router)
app.include_router(catalog.router)
app.include_router(policies.router)
app.include_router(security.router)
app.include_router(dashboard.router)
app.include_router(database.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"},
    )


def _health_payload() -> tuple[HealthResponse, int]:
    db_connected = is_database_connected()
    status_code = 200 if db_connected else 503
    response = HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        service=f"{settings.APP_NAME} API",
        database="connected" if db_connected else "unavailable",
    )
    return response, status_code


@app.get("/api/health", response_model=HealthResponse)
async def api_health() -> JSONResponse:
    response, status_code = _health_payload()
    return JSONResponse(status_code=status_code, content=response.model_dump())


@app.get("/health", response_model=HealthResponse)
async def root_health() -> JSONResponse:
    response, status_code = _health_payload()
    return JSONResponse(status_code=status_code, content=response.model_dump())
