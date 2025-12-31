"""
sunny-2 API - Solar Generation Estimator
=========================================
High-precision solar diagnostics powered by Copernicus CDSE and Gemini 2.0
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.routers import analyses, api_keys, cron, estimate, geosearch, health, progress


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    from app.core.cache import cache
    from app.core.database import db
    from app.services.ai_consultant import ai_consultant

    # Startup
    print(f"🌞 Starting sunny-2 API v{settings.VERSION}")
    print(f"📡 Environment: {settings.ENVIRONMENT}")

    # Initialize database connection
    if db.is_configured:
        db.init()
        print("🗄️ Database connection initialized")
    else:
        print("⚠️ Database not configured (set DATABASE_URL)")

    # Initialize Redis cache
    if cache.is_configured:
        cache.init()
        print("📦 Redis cache initialized")
    else:
        print("⚠️ Redis not configured (set UPSTASH_REDIS_REST_URL)")

    # Initialize AI consultant (Gemini)
    if ai_consultant.is_configured:
        ai_consultant.init()
        print("🤖 AI Consultant (Gemini 2.0) initialized")
    else:
        print("⚠️ AI Consultant not configured (set GEMINI_API_KEY)")

    yield

    # Shutdown
    if db.is_configured:
        await db.close()
    print("🌙 Shutting down sunny-2 API")


app = FastAPI(
    title="sunny-2 API",
    description="""
## Solar Generation Estimator API

High-precision solar diagnostics powered by:
- 🛰️ **Copernicus CDSE** (ERA5-Land, CAMS) for satellite radiation data
- ☀️ **Pvlib** for scientific solar calculations
- 🤖 **Gemini 2.0** for proactive AI insights

### Features
- Real-time solar potential estimation
- Interactive interpolation models for tilt/orientation simulation
- Transparent AI-driven narratives with source citations
- Multi-country regulatory plugin support
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
# CORS_ORIGINS can be set as comma-separated string: "https://domain1.com,https://domain2.com"
# FRONTEND_URL is automatically added if set
cors_origins = settings.cors_origins_list.copy()
if settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deploys
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(estimate.router)
app.include_router(progress.router)
app.include_router(geosearch.router)
app.include_router(api_keys.router)
app.include_router(analyses.router)
app.include_router(cron.router)


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Root endpoint - API information."""
    return JSONResponse(
        content={
            "name": "sunny-2 API",
            "version": settings.VERSION,
            "description": "Solar Generation Estimator - Powered by Copernicus & Gemini 2.0",
            "docs": "/docs",
            "health": "/api/health",
        }
    )


def main() -> None:
    """Entry point for running the API server."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()

