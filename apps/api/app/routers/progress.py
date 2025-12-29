"""Server-Sent Events (SSE) for progress updates."""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Progress"])

# In-memory progress store (use Redis in production)
_progress_store: dict[str, dict] = {}


def update_progress(request_id: str, status: str, percent: int, message: str) -> None:
    """Update progress for a request."""
    _progress_store[request_id] = {
        "status": status,
        "progress_percent": percent,
        "message": message,
    }


def get_progress(request_id: str) -> dict:
    """Get progress for a request."""
    return _progress_store.get(request_id, {
        "status": "unknown",
        "progress_percent": 0,
        "message": "Request not found",
    })


def clear_progress(request_id: str) -> None:
    """Clear progress for a completed request."""
    _progress_store.pop(request_id, None)


@router.get(
    "/estimate/{request_id}/progress",
    summary="Stream progress updates for an estimate request",
    description="Returns Server-Sent Events with progress updates",
)
async def stream_progress(request_id: str) -> StreamingResponse:
    """
    Stream progress updates via SSE.
    
    Events emitted:
    - connecting: Initial connection established
    - fetching_data: Fetching data from Copernicus
    - calculating: Running solar calculations
    - generating_insights: Generating AI insights
    - complete: Processing complete
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events."""
        try:
            # Initial connection event
            yield f"event: connecting\ndata: {json.dumps({'status': 'connecting', 'progress_percent': 0, 'message': 'Conectando...'})}\n\n"
            
            timeout_counter = 0
            max_timeout = 300  # 5 minutes
            
            while timeout_counter < max_timeout:
                progress = get_progress(request_id)
                
                yield f"data: {json.dumps(progress)}\n\n"
                
                if progress["status"] == "complete":
                    yield f"event: complete\ndata: {json.dumps(progress)}\n\n"
                    clear_progress(request_id)
                    break
                
                if progress["status"] == "error":
                    yield f"event: error\ndata: {json.dumps(progress)}\n\n"
                    clear_progress(request_id)
                    break
                
                await asyncio.sleep(0.5)
                timeout_counter += 0.5
            
            if timeout_counter >= max_timeout:
                yield f"event: timeout\ndata: {json.dumps({'status': 'timeout', 'message': 'Request timed out'})}\n\n"
                
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for {request_id}")
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Progress simulation for demo
async def simulate_progress(request_id: str) -> None:
    """Simulate progress updates for demo purposes."""
    stages = [
        ("fetching_data", 20, "Conectando con satélite Copernicus..."),
        ("fetching_data", 40, "Descargando datos de radiación..."),
        ("calculating", 60, "Calculando potencial solar..."),
        ("calculating", 75, "Generando modelo de interpolación..."),
        ("generating_insights", 90, "Preparando análisis..."),
        ("complete", 100, "¡Análisis completado!"),
    ]
    
    for status, percent, message in stages:
        update_progress(request_id, status, percent, message)
        await asyncio.sleep(0.5)

