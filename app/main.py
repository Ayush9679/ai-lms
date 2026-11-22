"""
AI-LMS Application Factory — FastAPI app with all middleware, routers, and lifespan.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.database import engine
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info(
        "AI-LMS starting",
        extra={
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
    )

    # Ensure upload directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    for subdir in ("image", "video", "document", "assignment", "other"):
        Path(settings.UPLOAD_DIR, subdir).mkdir(parents=True, exist_ok=True)

    try:
        yield
    finally:
        await engine.dispose()
        logger.info("AI-LMS shutting down")


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI-LMS — AI Learning Management System",
    description="""
Learning management API for accounts, courses, lessons, enrollments, quizzes,
assignments, dashboards, course search, uploads, and optional Gemini-backed study
operations. Email verification and password reset endpoints exist, but outbound
email delivery is not configured by this application.

Authenticate with a bearer token from `POST /api/v1/auth/login` using the Authorize
control. Health checks are available at `/health` and `/api/v1/health`.
    """,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# =============================================================================
# Rate Limiter
# =============================================================================
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# =============================================================================
# CORS
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# =============================================================================
# Request Logging
# =============================================================================
app.add_middleware(RequestLoggingMiddleware)

# =============================================================================
# Static Files (uploads)
# =============================================================================
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(upload_dir)), name="static")

# =============================================================================
# Exception Handlers
# =============================================================================
register_exception_handlers(app)

# =============================================================================
# API Routers
# =============================================================================
app.include_router(api_router, prefix="/api/v1")


# =============================================================================
# Health Check
# =============================================================================
@app.get(
    "/",
    tags=["⚕️ Health"],
    summary="Health check",
    description="Returns app status and version. Used by Docker health checks.",
)
async def health_check() -> dict:
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"], summary="Liveness check")
async def liveness_check() -> dict:
    return await health_check()


@app.get(
    "/api/v1/health",
    tags=["⚕️ Health"],
    summary="API health check",
)
async def api_health() -> dict:
    return {"status": "healthy", "version": settings.APP_VERSION}
