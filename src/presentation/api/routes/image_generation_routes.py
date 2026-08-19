"""
Image generation routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID  # KEEP THIS IMPORT AT THE TOP
import os

from src.presentation.api.dependencies import (
    get_dependencies,
    get_current_active_user,
)
from src.application.commands import GenerateImageCommand
from src.presentation.api.schemas.response_schemas import (
    AssetResponse,
    AssetsListResponse,
)
from src.shared.config import settings

router = APIRouter()


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    negative_prompt: Optional[str] = Field(None, max_length=1000)
    model: Optional[str] = None
    width: int = Field(1024, ge=512, le=1024)
    height: int = Field(1024, ge=512, le=1024)
    num_images: int = Field(1, ge=1, le=1)
    seed: Optional[int] = None
    enhance_prompt: bool = True
    conversation_id: Optional[UUID] = None


@router.post("/generate")
async def generate_image(
    request: GenerateImageRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Generate an image using AI.
    """
    # Use configured image model if not specified
    model_name = request.model or settings.IMAGE_MODEL or "black-forest-labs/FLUX.1-dev"
    
    command = GenerateImageCommand(
        user_id=UUID(current_user["user_id"]),  # UUID is already imported at top
        prompt=request.prompt,
        negative_prompt=request.negative_prompt,
        model_name=model_name,
        parameters={
            "width": request.width,
            "height": request.height,
        },
        num_images=request.num_images,
        seed=request.seed,
        enhance_prompt=request.enhance_prompt,
        conversation_id=request.conversation_id,
    )
    
    asset_dto, errors = await deps.asset_command_handler.handle_generate_image(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    # Get the actual asset from repository to get the real file path
    asset = await deps.asset_repository.get_by_id(UUID(asset_dto.id))
    
    # Build response manually to ensure file_path is included
    response_data = {
        "success": True,
        "data": {
            "id": asset_dto.id,
            "user_id": asset_dto.user_id,
            "asset_type": asset_dto.asset_type,
            "file_name": asset_dto.file_name,
            "file_size": asset_dto.file_size,
            "formatted_file_size": asset_dto.formatted_file_size,
            "mime_type": asset_dto.mime_type,
            "created_at": asset_dto.created_at,
            "file_path": asset.file_path if asset else None,
            "title": asset_dto.title,
            "prompt": request.prompt,
            "model_used": asset_dto.model_used,
            "is_favorite": asset_dto.is_favorite,
            "file_url": f"/api/images/{asset_dto.id}",
        }
    }
    
    return response_data


@router.get("", response_model=AssetsListResponse)
async def list_images(
    skip: int = 0,
    limit: int = 50,
    is_favorite: Optional[bool] = None,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """List user's generated images."""
    from src.application.queries import GetUserAssetsQuery
    
    query = GetUserAssetsQuery(
        user_id=UUID(current_user["user_id"]),
        asset_type="image",
        skip=skip,
        limit=limit,
        is_favorite=is_favorite,
    )
    
    dtos, total, errors = await deps.analytics_query_handler.handle_get_user_assets(query)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return AssetsListResponse(
        assets=[d.to_dict() for d in dtos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{asset_id}")
async def get_image(
    asset_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Get image file."""
    asset = await deps.asset_repository.get_by_id(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if str(asset.user_id) != current_user["user_id"] and not asset.is_public:
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
    
    if not os.path.exists(asset.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file not found at: {asset.file_path}",
        )
    
    await deps.asset_repository.increment_view_count(asset_id)
    
    return FileResponse(
        asset.file_path,
        media_type=asset.mime_type,
        filename=asset.file_name,
    )


@router.get("/{asset_id}/info")
async def get_image_info(
    asset_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Get image metadata."""
    asset = await deps.asset_repository.get_by_id(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    return {
        "id": str(asset.id),
        "file_path": asset.file_path,
        "file_name": asset.file_name,
        "file_size": asset.file_size,
        "prompt": asset.prompt,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


@router.delete("/{asset_id}")
async def delete_image(
    asset_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Delete an image."""
    success, errors = await deps.asset_command_handler.delete_asset(
        asset_id=asset_id,
        user_id=UUID(current_user["user_id"]),
    )
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return {"message": "Image deleted successfully"}


@router.patch("/{asset_id}/favorite")
async def toggle_favorite(
    asset_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """Toggle favorite status of an image."""
    asset = await deps.asset_repository.get_by_id(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    if str(asset.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    asset.toggle_favorite()
    await deps.asset_repository.update(asset)
    
    return {"is_favorite": asset.is_favorite}