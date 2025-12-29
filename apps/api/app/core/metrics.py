"""
Metrics and Structured Logging for sunny-2 API.

Provides:
- Structured logging for analysis and debugging
- Request/response metrics collection
- External API call tracking
- Cache hit/miss statistics
- Circuit breaker state monitoring

For production, these metrics can be exported to:
- Prometheus (via prometheus_client)
- Datadog
- CloudWatch
- Any other observability platform
"""

import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("sunny2.metrics")


@dataclass
class MetricsCollector:
    """
    Centralized metrics collection for monitoring and alerting.
    
    Tracks:
    - API request counts and latencies
    - External service call statistics
    - Cache performance
    - Error rates
    
    Thread-safe using simple counters (for MVP).
    For production, use prometheus_client or similar.
    """
    
    # Request counters
    _request_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _request_latencies: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _error_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # External API metrics
    _external_calls: dict[str, dict[str, int]] = field(
        default_factory=lambda: defaultdict(lambda: {"success": 0, "error": 0})
    )
    _external_latencies: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    
    # Cache metrics
    _cache_hits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _cache_misses: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Rate limit metrics
    _rate_limit_hits: int = field(default=0)
    
    # Start time for uptime calculation
    _start_time: datetime = field(default_factory=datetime.now)
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
    ) -> None:
        """Record an API request."""
        key = f"{method}:{endpoint}"
        self._request_counts[key] += 1
        self._request_latencies[key].append(latency_ms)
        
        if status_code >= 400:
            self._error_counts[key] += 1
        
        # Keep only last 1000 latencies to prevent memory growth
        if len(self._request_latencies[key]) > 1000:
            self._request_latencies[key] = self._request_latencies[key][-1000:]
        
        # Log request
        log_level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            f"REQUEST | {method} {endpoint} | status={status_code} | latency={latency_ms:.2f}ms"
        )
    
    def record_external_call(
        self,
        service: str,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None,
    ) -> None:
        """Record a call to an external service."""
        if success:
            self._external_calls[service]["success"] += 1
        else:
            self._external_calls[service]["error"] += 1
        
        self._external_latencies[service].append(latency_ms)
        
        # Keep only last 100 latencies per service
        if len(self._external_latencies[service]) > 100:
            self._external_latencies[service] = self._external_latencies[service][-100:]
        
        # Log external call
        log_level = logging.INFO if success else logging.WARNING
        message = f"EXTERNAL | {service} | success={success} | latency={latency_ms:.2f}ms"
        if error:
            message += f" | error={error}"
        logger.log(log_level, message)
    
    def record_cache_hit(self, layer: str) -> None:
        """Record a cache hit."""
        self._cache_hits[layer] += 1
        logger.debug(f"CACHE | HIT | layer={layer}")
    
    def record_cache_miss(self, layer: str) -> None:
        """Record a cache miss."""
        self._cache_misses[layer] += 1
        logger.debug(f"CACHE | MISS | layer={layer}")
    
    def record_cache_error(self, layer: str) -> None:
        """Record a cache error (counts as miss)."""
        self._cache_misses[layer] += 1
        self._error_counts[f"cache:{layer}"] += 1
        logger.warning(f"CACHE | ERROR | layer={layer}")
    
    def record_rate_limit(self, identifier: str) -> None:
        """Record a rate limit hit."""
        self._rate_limit_hits += 1
        logger.warning(f"RATE_LIMIT | identifier={identifier}")
    
    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all collected metrics."""
        # Calculate cache hit rates
        cache_stats = {}
        for layer in set(self._cache_hits.keys()) | set(self._cache_misses.keys()):
            hits = self._cache_hits.get(layer, 0)
            misses = self._cache_misses.get(layer, 0)
            total = hits + misses
            cache_stats[layer] = {
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hits / total * 100, 2) if total > 0 else 0,
            }
        
        # Calculate external service stats
        external_stats = {}
        for service, counts in self._external_calls.items():
            total = counts["success"] + counts["error"]
            latencies = self._external_latencies.get(service, [])
            external_stats[service] = {
                "total_calls": total,
                "success": counts["success"],
                "errors": counts["error"],
                "success_rate": round(counts["success"] / total * 100, 2) if total > 0 else 0,
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                "p95_latency_ms": round(
                    sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 2
                ),
            }
        
        # Calculate request stats
        request_stats = {}
        for endpoint, count in self._request_counts.items():
            latencies = self._request_latencies.get(endpoint, [])
            errors = self._error_counts.get(endpoint, 0)
            request_stats[endpoint] = {
                "total": count,
                "errors": errors,
                "error_rate": round(errors / count * 100, 2) if count > 0 else 0,
                "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            }
        
        uptime = datetime.now() - self._start_time
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "requests": request_stats,
            "external_services": external_stats,
            "cache": cache_stats,
            "rate_limits_triggered": self._rate_limit_hits,
        }


# Global metrics instance
metrics = MetricsCollector()


@asynccontextmanager
async def track_request(endpoint: str, method: str):
    """
    Context manager for tracking request metrics.
    
    Usage:
        async with track_request("/api/estimate", "POST") as tracker:
            result = await do_something()
            tracker.set_status(200)
    """
    start_time = time.perf_counter()
    status_code = 200
    
    class Tracker:
        def set_status(self, code: int):
            nonlocal status_code
            status_code = code
    
    tracker = Tracker()
    
    try:
        yield tracker
    except Exception as e:
        status_code = 500
        raise
    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics.record_request(endpoint, method, status_code, latency_ms)


@asynccontextmanager
async def track_external_call(service: str):
    """
    Context manager for tracking external API calls.
    
    Usage:
        async with track_external_call("copernicus"):
            result = await copernicus_api.fetch(...)
    """
    start_time = time.perf_counter()
    success = True
    error_msg = None
    
    try:
        yield
    except Exception as e:
        success = False
        error_msg = str(e)[:100]  # Truncate error message
        raise
    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics.record_external_call(service, success, latency_ms, error_msg)


def log_solar_request(
    lat: float,
    lon: float,
    source: str,
    cache_hit: bool,
    latency_ms: float,
) -> None:
    """Log a solar data request with structured data."""
    logger.info(
        f"SOLAR_REQUEST | lat={lat:.4f} lon={lon:.4f} | "
        f"source={source} | cache_hit={cache_hit} | latency={latency_ms:.2f}ms"
    )


def log_rate_limit_exceeded(identifier: str, limit: str) -> None:
    """Log when rate limit is exceeded."""
    metrics.record_rate_limit(identifier)
    logger.warning(
        f"RATE_LIMIT_EXCEEDED | identifier={identifier} | limit={limit}"
    )


def log_circuit_breaker_event(
    breaker_name: str,
    event: str,
    details: Optional[dict] = None,
) -> None:
    """Log circuit breaker state changes."""
    details_str = f" | details={details}" if details else ""
    logger.warning(
        f"CIRCUIT_BREAKER | name={breaker_name} | event={event}{details_str}"
    )


def log_cache_operation(
    layer: str,
    operation: str,
    key: str,
    hit: bool,
    latency_ms: Optional[float] = None,
) -> None:
    """Log cache operations."""
    if hit:
        metrics.record_cache_hit(layer)
    else:
        metrics.record_cache_miss(layer)
    
    latency_str = f" | latency={latency_ms:.2f}ms" if latency_ms else ""
    logger.debug(
        f"CACHE | layer={layer} | op={operation} | key={key[:50]} | hit={hit}{latency_str}"
    )

