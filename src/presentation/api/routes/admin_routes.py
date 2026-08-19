"""
Admin routes for system management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from src.presentation.api.dependencies import (
    get_dependencies,
    get_admin_user,
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    period: str = "30d",
    current_user: dict = Depends(get_admin_user),
    deps = Depends(get_dependencies),
):
    """Get admin dashboard statistics."""
    return {
        "period": period,
        "users": {"total": 0, "active": 0},
        "conversations": {"total": 0},
        "assets": {"total": 0},
    }


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_admin_user),
    deps = Depends(get_dependencies),
):
    """List all users (admin only)."""
    return {"users": [], "total": 0}


@router.get("/api-keys")
async def list_api_keys(
    current_user: dict = Depends(get_admin_user),
    deps = Depends(get_dependencies),
):
    """List all API keys (admin only)."""
    return {"keys": []}


@router.post("/api-keys")
async def create_api_key(
    request: dict,
    current_user: dict = Depends(get_admin_user),
    deps = Depends(get_dependencies),
):
    """Create a new API key."""
    return {"message": "API key created"}


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_admin_user),
    deps = Depends(get_dependencies),
):
    """Revoke an API key."""
    return {"message": "API key revoked"}