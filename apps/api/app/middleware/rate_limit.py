"""
Rate Limiting Middleware using SlowAPI.

Provides tiered rate limiting based on:
- Anonymous users (no API key): Strictest limits
- Free tier API keys: Standard limits
- Pro tier API keys: Higher limits

Also includes internal rate limiters for external API calls.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.middleware.auth import get_api_key_or_ip
from app.core.config import settings
from app.core.metrics import log_rate_limit_exceeded


# ===========================================
# API Rate Limiter (SlowAPI)
# ===========================================

# Create limiter with custom key function
limiter = Limiter(key_func=get_api_key_or_ip)


def get_rate_limit_string(request: Request) -> str:
    """
    Get appropriate rate limit based on request authentication.
    
    Returns rate limit string for SlowAPI.
    """
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        # Anonymous - strictest limits
        return f"{settings.RATE_LIMIT_ANONYMOUS}/minute"
    
    # TODO: Check database for API key tier
    # For MVP, all authenticated users get standard limit
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Handle rate limit exceeded errors with RFC 7807 format."""
    identifier = get_api_key_or_ip(request)
    log_rate_limit_exceeded(identifier, str(exc.detail))
    
    retry_after = getattr(exc, "retry_after", 60)
    
    return JSONResponse(
        status_code=429,
        content={
            "type": "https://api.sunny-2.com/errors/rate-limit-exceeded",
            "title": "Too Many Requests",
            "status": 429,
            "detail": f"Rate limit exceeded: {exc.detail}. Please wait before retrying.",
            "instance": str(request.url),
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
        },
    )


# ===========================================
# Internal Rate Limiter for External APIs
# ===========================================

@dataclass
class InternalRateLimiter:
    """
    Rate limiter for internal use (external API calls).
    
    Uses a simple token bucket algorithm with sliding window.
    Thread-safe using asyncio locks.
    
    Usage:
        limiter = InternalRateLimiter(name="copernicus", max_calls=10, window_seconds=60)
        await limiter.acquire()  # Blocks until rate limit allows
        await external_api.call()
    """
    
    name: str
    max_calls: int
    window_seconds: int
    
    # Internal state
    _calls: list[datetime] = field(default_factory=list, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _waiting: int = field(default=0, init=False)
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a call.
        
        Blocks if rate limit is exceeded until window resets.
        """
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Clean old entries
            self._calls = [t for t in self._calls if t > window_start]
            
            if len(self._calls) < self.max_calls:
                # Under limit, allow immediately
                self._calls.append(now)
                return
            
            # Calculate wait time
            oldest_call = min(self._calls)
            wait_seconds = (oldest_call + timedelta(seconds=self.window_seconds) - now).total_seconds()
            
            if wait_seconds > 0:
                self._waiting += 1
                # Release lock while waiting
                self._lock.release()
                try:
                    await asyncio.sleep(wait_seconds)
                finally:
                    await self._lock.acquire()
                    self._waiting -= 1
            
            # Re-check after waiting
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            self._calls = [t for t in self._calls if t > window_start]
            self._calls.append(now)
    
    async def try_acquire(self) -> bool:
        """
        Try to acquire permission without blocking.
        
        Returns:
            True if acquired, False if rate limit exceeded
        """
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Clean old entries
            self._calls = [t for t in self._calls if t > window_start]
            
            if len(self._calls) < self.max_calls:
                self._calls.append(now)
                return True
            
            return False
    
    def get_status(self) -> dict:
        """Get current rate limiter status."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        recent_calls = [t for t in self._calls if t > window_start]
        
        return {
            "name": self.name,
            "max_calls": self.max_calls,
            "window_seconds": self.window_seconds,
            "current_calls": len(recent_calls),
            "remaining": max(0, self.max_calls - len(recent_calls)),
            "waiting": self._waiting,
        }


# ===========================================
# Semaphore Manager for Concurrency Control
# ===========================================

@dataclass
class SemaphoreManager:
    """
    Manages semaphores for limiting concurrent operations.
    
    Usage:
        manager = SemaphoreManager(name="copernicus", max_concurrent=5)
        async with manager.acquire():
            await external_api.call()
    """
    
    name: str
    max_concurrent: int
    
    _semaphore: asyncio.Semaphore = field(init=False)
    _active: int = field(default=0, init=False)
    _waiting: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    
    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def acquire(self):
        """Acquire semaphore for concurrent operation."""
        async with self._lock:
            self._waiting += 1
        
        await self._semaphore.acquire()
        
        async with self._lock:
            self._waiting -= 1
            self._active += 1
        
        return self
    
    async def release(self):
        """Release semaphore."""
        async with self._lock:
            self._active -= 1
        self._semaphore.release()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
        return False
    
    def get_status(self) -> dict:
        """Get current semaphore status."""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active": self._active,
            "waiting": self._waiting,
            "available": self.max_concurrent - self._active,
        }


# ===========================================
# Pre-configured Rate Limiters and Semaphores
# ===========================================

# Rate limiter for Copernicus API (10 calls/minute)
copernicus_rate_limiter = InternalRateLimiter(
    name="copernicus",
    max_calls=settings.RATE_LIMIT_COPERNICUS,
    window_seconds=60,
)

# Rate limiter for PVGIS API (20 calls/minute)
pvgis_rate_limiter = InternalRateLimiter(
    name="pvgis",
    max_calls=settings.RATE_LIMIT_PVGIS,
    window_seconds=60,
)

# Semaphore for Copernicus concurrent calls
copernicus_semaphore = SemaphoreManager(
    name="copernicus",
    max_concurrent=settings.MAX_CONCURRENT_COPERNICUS,
)

# Semaphore for PVGIS concurrent calls
pvgis_semaphore = SemaphoreManager(
    name="pvgis",
    max_concurrent=settings.MAX_CONCURRENT_PVGIS,
)

# Semaphore for database concurrent queries
db_semaphore = SemaphoreManager(
    name="database",
    max_concurrent=settings.MAX_CONCURRENT_DB,
)


def get_all_rate_limiters() -> dict:
    """Get all rate limiters for monitoring."""
    return {
        "copernicus": copernicus_rate_limiter.get_status(),
        "pvgis": pvgis_rate_limiter.get_status(),
    }


def get_all_semaphores() -> dict:
    """Get all semaphores for monitoring."""
    return {
        "copernicus": copernicus_semaphore.get_status(),
        "pvgis": pvgis_semaphore.get_status(),
        "database": db_semaphore.get_status(),
    }

