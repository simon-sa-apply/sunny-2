"""API Keys management endpoints."""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field

from app.repositories.api_keys_repository import api_keys_repository

router = APIRouter(prefix="/api/admin/keys", tags=["API Keys"])


# ============================================
# Request/Response Models
# ============================================

class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    owner_email: Optional[EmailStr] = None
    rate_limit_per_minute: int = Field(default=100, ge=1, le=10000)
    rate_limit_per_day: int = Field(default=10000, ge=1, le=1000000)
    expires_at: Optional[datetime] = None


class UpdateKeyRequest(BaseModel):
    """Request to update an API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class KeyResponse(BaseModel):
    """API key response (without full key)."""
    id: int
    key_prefix: str
    name: str
    description: Optional[str]
    owner_email: Optional[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    is_valid: bool
    last_used_at: Optional[str]
    total_requests: int
    expires_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class CreatedKeyResponse(BaseModel):
    """Response when creating a new key (includes full key)."""
    id: int
    key: str  # Full key - only shown once!
    name: str
    description: Optional[str]
    owner_email: Optional[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    expires_at: Optional[str]
    created_at: Optional[str]
    message: str = "Store this key securely - it won't be shown again!"


class StatsResponse(BaseModel):
    """API key statistics."""
    total_keys: int
    active_keys: int
    inactive_keys: int
    expired_keys: int
    total_requests: int


# ============================================
# Admin Auth Check (simple for MVP)
# ============================================

async def verify_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> bool:
    """
    Simple admin verification for MVP.
    
    In production, this would check against a database or use proper auth.
    For MVP, we use an environment variable or accept any key for demo.
    """
    # For MVP, we allow access if any admin key is provided
    # In production, this should be properly secured
    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Provide X-Admin-Key header.",
        )
    return True


# ============================================
# Endpoints
# ============================================

@router.post("", response_model=CreatedKeyResponse)
async def create_api_key(
    request: CreateKeyRequest,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> CreatedKeyResponse:
    """
    Create a new API key.
    
    **Important**: The full API key is only shown in this response.
    Store it securely - it cannot be retrieved again!
    
    Returns:
        The created API key with full key value
    """
    await verify_admin(x_admin_key)
    
    result = await api_keys_repository.create(
        name=request.name,
        description=request.description,
        owner_email=request.owner_email,
        rate_limit_per_minute=request.rate_limit_per_minute,
        rate_limit_per_day=request.rate_limit_per_day,
        expires_at=request.expires_at,
    )
    
    return CreatedKeyResponse(**result)


@router.get("", response_model=list[KeyResponse])
async def list_api_keys(
    include_inactive: bool = False,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> list[KeyResponse]:
    """
    List all API keys.
    
    Args:
        include_inactive: Whether to include deactivated keys
    
    Returns:
        List of API keys (without full key values)
    """
    await verify_admin(x_admin_key)
    
    keys = await api_keys_repository.list_all(include_inactive=include_inactive)
    return [KeyResponse(**k) for k in keys]


@router.get("/stats", response_model=StatsResponse)
async def get_api_key_stats(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> StatsResponse:
    """Get API key statistics."""
    await verify_admin(x_admin_key)
    
    stats = await api_keys_repository.get_stats()
    return StatsResponse(**stats)


@router.get("/{key_id}", response_model=KeyResponse)
async def get_api_key(
    key_id: int,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> KeyResponse:
    """Get a specific API key by ID."""
    await verify_admin(x_admin_key)
    
    key = await api_keys_repository.get_by_id(key_id)
    if not key:
        raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
    
    return KeyResponse(**key)


@router.patch("/{key_id}", response_model=KeyResponse)
async def update_api_key(
    key_id: int,
    request: UpdateKeyRequest,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> KeyResponse:
    """
    Update an API key's settings.
    
    Only provided fields will be updated.
    """
    await verify_admin(x_admin_key)
    
    result = await api_keys_repository.update(
        key_id=key_id,
        name=request.name,
        description=request.description,
        rate_limit_per_minute=request.rate_limit_per_minute,
        rate_limit_per_day=request.rate_limit_per_day,
        is_active=request.is_active,
        expires_at=request.expires_at,
    )
    
    if not result:
        raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
    
    return KeyResponse(**result)


@router.post("/{key_id}/deactivate", response_model=KeyResponse)
async def deactivate_api_key(
    key_id: int,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> KeyResponse:
    """Deactivate an API key (soft delete)."""
    await verify_admin(x_admin_key)
    
    success = await api_keys_repository.deactivate(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
    
    key = await api_keys_repository.get_by_id(key_id)
    return KeyResponse(**key)


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
) -> dict[str, Any]:
    """
    Permanently delete an API key.
    
    **Warning**: This action cannot be undone!
    """
    await verify_admin(x_admin_key)
    
    success = await api_keys_repository.delete(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
    
    return {"message": f"API key {key_id} deleted successfully"}


# ============================================
# Key Validation Endpoint (for internal use)
# ============================================

@router.post("/validate")
async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> dict[str, Any]:
    """
    Validate an API key.
    
    This endpoint can be used by services to validate keys.
    """
    is_valid, key_info = await api_keys_repository.validate(x_api_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
        )
    
    # Record usage
    await api_keys_repository.record_usage(x_api_key)
    
    return {
        "valid": True,
        "key_info": {
            "name": key_info["name"] if key_info else None,
            "rate_limit_per_minute": key_info["rate_limit_per_minute"] if key_info else None,
        },
    }

