"""Application configuration using Pydantic Settings."""


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App Info
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS - Add your Vercel domain after deployment
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",  # Vercel preview deployments
    ]

    # Frontend URL (set in production)
    FRONTEND_URL: str = ""

    # Database (PostgreSQL + PostGIS)
    DATABASE_URL: str = ""

    # Cache (Redis/Upstash)
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # Copernicus CDSE
    COPERNICUS_API_KEY: str = ""
    COPERNICUS_API_SECRET: str = ""

    # Gemini AI
    GEMINI_API_KEY: str = ""

    # ===========================================
    # Rate Limiting Configuration
    # ===========================================
    RATE_LIMIT_PER_MINUTE: int = 100      # Default for authenticated users
    RATE_LIMIT_ANONYMOUS: int = 30        # Anonymous users (no API key)
    RATE_LIMIT_COPERNICUS: int = 10       # Calls to Copernicus per minute
    RATE_LIMIT_PVGIS: int = 20            # Calls to PVGIS per minute

    # ===========================================
    # Cache TTL Configuration
    # ===========================================
    REDIS_TTL_SECONDS: int = 3600         # Hot cache: 1 hour
    DB_CACHE_TTL_DAYS: int = 30           # Warm cache: 30 days
    CACHE_RADIUS_KM: float = 5.0          # Geospatial cache radius

    # ===========================================
    # Circuit Breaker Configuration
    # ===========================================
    CIRCUIT_FAILURE_THRESHOLD: int = 5    # Failures before opening circuit
    CIRCUIT_RECOVERY_TIMEOUT: int = 60    # Seconds before half-open
    CIRCUIT_HALF_OPEN_MAX_CALLS: int = 3  # Test calls in half-open state

    # ===========================================
    # Concurrency Limits
    # ===========================================
    MAX_CONCURRENT_COPERNICUS: int = 5    # Parallel requests to Copernicus
    MAX_CONCURRENT_PVGIS: int = 10        # Parallel requests to PVGIS
    MAX_CONCURRENT_DB: int = 20           # Parallel database queries

    # ===========================================
    # Cron Job Configuration
    # ===========================================
    CRON_SECRET: str = ""                 # Secret for authenticating cron jobs


settings = Settings()

