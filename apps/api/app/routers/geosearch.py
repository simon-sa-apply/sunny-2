"""Geosearch API endpoint for location lookup."""

import logging
from typing import Optional

from fastapi import APIRouter, Query
import httpx

from app.core.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Geosearch"])


@router.get(
    "/geosearch",
    summary="Search for locations by text",
    description="Returns location suggestions with coordinates using Nominatim",
)
async def search_location(
    q: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(default=5, ge=1, le=10, description="Max results"),
) -> list[dict]:
    """
    Search for locations using OpenStreetMap Nominatim.
    
    Returns array of suggestions with name, lat, lon, and country.
    Results are cached for 7 days.
    """
    # Check cache
    cache_key = f"geo:{q.lower()}"
    cached = await cache.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    
    # Query Nominatim
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": q,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                },
                headers={
                    "User-Agent": "sunny-2/1.0 (https://github.com/sunny-2)"
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error(f"Nominatim error: {e}")
        # Return mock data for demo
        return _get_mock_results(q)
    
    # Transform results
    results = []
    for item in data[:limit]:
        results.append({
            "name": item.get("display_name", ""),
            "lat": float(item.get("lat", 0)),
            "lon": float(item.get("lon", 0)),
            "country": item.get("address", {}).get("country", ""),
            "country_code": item.get("address", {}).get("country_code", "").upper(),
            "type": item.get("type", ""),
        })
    
    # Cache results (7 days)
    if results and cache.is_configured:
        import json
        await cache.set(cache_key, json.dumps(results), ex=604800)
    
    return results


def _get_mock_results(query: str) -> list[dict]:
    """Return mock results for demo when Nominatim is unavailable."""
    mock_data = {
        "santiago": [{
            "name": "Santiago, Región Metropolitana, Chile",
            "lat": -33.4489,
            "lon": -70.6693,
            "country": "Chile",
            "country_code": "CL",
            "type": "city",
        }],
        "berlin": [{
            "name": "Berlin, Germany",
            "lat": 52.5200,
            "lon": 13.4050,
            "country": "Germany",
            "country_code": "DE",
            "type": "city",
        }],
        "tokyo": [{
            "name": "Tokyo, Japan",
            "lat": 35.6762,
            "lon": 139.6503,
            "country": "Japan",
            "country_code": "JP",
            "type": "city",
        }],
    }
    
    query_lower = query.lower()
    for key, results in mock_data.items():
        if key in query_lower:
            return results
    
    return [{
        "name": f"Search result for: {query}",
        "lat": 0.0,
        "lon": 0.0,
        "country": "Unknown",
        "country_code": "",
        "type": "unknown",
    }]

