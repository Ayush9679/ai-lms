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
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter

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

    yield

    logger.info("AI-LMS shutting down")


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI-LMS — AI Learning Management System",
    description="""
## Enterprise-Grade AI Learning Management System

A production-quality backend built with FastAPI, PostgreSQL, and Google Gemini AI.

### Features
- 🔐 **JWT Authentication** with refresh tokens, email verification, and password reset
- 👥 **RBAC** with Student, Teacher, and Admin roles
- 📚 **Course Management** with lessons, videos, PDFs, and progress tracking
- ❓ **Quiz Engine** with MCQ, True/False, Subjective — manual and AI-generated
- 📝 **Assignment System** with file uploads and grading
- 🤖 **Gemini AI Integration**: Tutor chat, notes, summaries, flashcards, study plans
- 🔍 **Search** with full-text filtering, pagination, and sorting
- 📊 **Dashboards** for students, teachers, and admins
- 📁 **File Uploads** with MIME validation and size limits
- ⚡ **Rate Limiting** per IP with stricter AI endpoint limits

### Authentication
Use the **Authorize** button (🔒) to enter your Bearer token after logging in via `/api/v1/auth/login`.

### Quick Start
1. `POST /api/v1/auth/register` — Create an account
2. `POST /api/v1/auth/login` — Get your JWT token
3. Click **Authorize** and enter `<your_token>`
4. Explore the API!
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

# =============================================================================
# CORS
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/api/v1/health",
    tags=["⚕️ Health"],
    summary="API health check",
)
async def api_health() -> dict:
    return {"status": "healthy", "version": settings.APP_VERSION}
