# =============================================================================
# AI-LMS Dockerfile — Multi-stage production build
# =============================================================================

# Build stage
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# =============================================================================
# Runtime stage
# =============================================================================
FROM python:3.13-slim AS runtime

LABEL maintainer="AI-LMS <noreply@ailms.com>"
LABEL version="1.0.0"
LABEL description="AI Learning Management System"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 ailms && \
    useradd --uid 1001 --gid ailms --shell /bin/bash --create-home ailms

WORKDIR /app

# Copy wheels and install
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copy application source
COPY --chown=ailms:ailms . .

# Create uploads directory
RUN mkdir -p /app/uploads && chown -R ailms:ailms /app/uploads

# Switch to non-root user
USER ailms

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "asyncio"]
