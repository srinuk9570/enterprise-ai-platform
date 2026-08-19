"""
Chart generation routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from uuid import UUID

from src.presentation.api.dependencies import (
    get_dependencies,
    get_current_active_user,
)

router = APIRouter()


@router.post("")
async def create_chart(
    request: dict,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Create a new chart."""
    return {"message": "Chart created", "status": "ok"}


@router.get("")
async def list_charts(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """List user's charts."""
    return {"charts": [], "total": 0}


@router.get("/{chart_id}")
async def get_chart(
    chart_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Get a specific chart."""
    return {"id": str(chart_id)}


@router.get("/{chart_id}/export")
async def export_chart(
    chart_id: UUID,
    format: str = "png",
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Export chart in specified format."""
    return {"message": f"Exporting chart as {format}"}