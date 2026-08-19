"""
Handler for asset-related commands.
"""
from typing import Optional, Tuple, List
from uuid import UUID
import logging
from dataclasses import fields

from src.application.commands import (
    GenerateImageCommand,
    CreateChartCommand,
)
from src.application.dtos import AssetDTO, ChartDataDTO
from src.domain.entities.chart_configuration import ChartConfiguration
from src.domain.services.llm_orchestration_service import LLMOrchestrationService
from src.domain.services.chart_generation_service import ChartGenerationService
from src.domain.value_objects.time_range import TimeRange
from src.domain.exceptions import (
    EntityNotFoundError,
    ImageGenerationFailedError,
    ChartGenerationFailedError,
    InvalidPromptError,
)
from src.shared.constants import ChartType, AssetType
from src.shared.enums import ExportFormat

logger = logging.getLogger(__name__)


class AssetCommandHandler:
    """
    Handler for asset-related commands.
    """
    
    def __init__(
        self,
        asset_repository,
        chart_config_repository,
        llm_service: LLMOrchestrationService,
        chart_service: ChartGenerationService,
        user_repository,
        event_bus=None,
    ):
        self.asset_repository = asset_repository
        self.chart_config_repository = chart_config_repository
        self.llm_service = llm_service
        self.chart_service = chart_service
        self.user_repository = user_repository
        self.event_bus = event_bus
    
    async def handle_generate_image(
        self,
        command: GenerateImageCommand,
    ) -> Tuple[Optional[AssetDTO], list[str]]:
        """
        Handle GenerateImageCommand.
        Returns (asset_dto, errors).
        
        FIXED: Ensures file_path is properly set on the AssetDTO.
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Check user exists
            user = await self.user_repository.get_by_id(command.user_id)
            if not user:
                raise EntityNotFoundError("User", str(command.user_id))
            
            # Generate images
            assets = []
            for i in range(command.num_images):
                # Prepare parameters
                parameters = {
                    "width": command.width,
                    "height": command.height,
                    **(command.parameters or {}),
                }
                
                # Add seed if provided
                if command.seed is not None:
                    parameters["seed"] = command.seed + i
                
                # Generate single image
                asset = await self.llm_service.generate_image(
                    user_id=command.user_id,
                    prompt=command.prompt,
                    negative_prompt=command.negative_prompt,
                    model_name=command.model_name,
                    parameters=parameters,
                    conversation_id=command.conversation_id,
                )
                
                # Log the file path for debugging
                logger.info(f"Generated asset ID: {asset.id}")
                logger.info(f"Asset file_path: {asset.file_path}")
                logger.info(f"Asset file_name: {asset.file_name}")
                logger.info(f"Asset file_size: {asset.file_size}")
                
                assets.append(asset)
            
            # Get the first asset (primary return value)
            primary_asset = assets[0]
            
            # Convert to DTO
            asset_dto = AssetDTO.from_entity(primary_asset)
            
            # ENSURE file_path is explicitly set in the DTO
            # This is a safety check in case the from_entity method doesn't copy it correctly
            if hasattr(asset_dto, 'file_path'):
                asset_dto.file_path = primary_asset.file_path
                asset_dto.file_name = primary_asset.file_name
                asset_dto.file_size = primary_asset.file_size
            else:
                # If DTO doesn't have these fields, recreate it with explicit values
                logger.warning("AssetDTO missing file_path fields, recreating DTO")
                
                # Build dictionary from entity
                dto_dict = {
                    "id": primary_asset.id,
                    "user_id": primary_asset.user_id,
                    "asset_type": primary_asset.asset_type,
                    "file_path": primary_asset.file_path,  # EXPLICITLY SET
                    "file_name": primary_asset.file_name,  # EXPLICITLY SET
                    "file_size": primary_asset.file_size,  # EXPLICITLY SET
                    "mime_type": primary_asset.mime_type,
                    "prompt": primary_asset.prompt,
                    "model_used": primary_asset.model_used,
                    "generation_params": primary_asset.generation_params,
                    "generation_time_ms": primary_asset.generation_time_ms,
                    "conversation_id": primary_asset.conversation_id,
                    "created_at": primary_asset.created_at,
                    "updated_at": primary_asset.updated_at,
                }
                
                # Filter to only fields that exist in AssetDTO
                field_names = [f.name for f in fields(AssetDTO)]
                filtered_dict = {k: v for k, v in dto_dict.items() if k in field_names}
                
                # Create new DTO
                asset_dto = AssetDTO(**filtered_dict)
            
            # Final verification
            logger.info(f"AssetDTO file_path: {getattr(asset_dto, 'file_path', 'MISSING')}")
            logger.info(f"AssetDTO file_name: {getattr(asset_dto, 'file_name', 'MISSING')}")
            
            # Publish event for all generated images
            if self.event_bus:
                await self.event_bus.publish("image.generated", {
                    "user_id": str(command.user_id),
                    "num_images": len(assets),
                    "asset_ids": [str(a.id) for a in assets],
                    "model_used": primary_asset.model_used,
                    "conversation_id": str(command.conversation_id) if command.conversation_id else None,
                })
            
            logger.info(f"Successfully generated {len(assets)} image(s) for user {command.user_id}")
            
            return asset_dto, []
            
        except EntityNotFoundError as e:
            logger.error(f"Entity not found: {e}")
            return None, [str(e)]
        except InvalidPromptError as e:
            logger.error(f"Invalid prompt: {e}")
            return None, [str(e)]
        except ImageGenerationFailedError as e:
            logger.error(f"Image generation failed: {e}")
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return None, [f"Internal server error: {str(e)}"]
    
    async def handle_create_chart(
        self,
        command: CreateChartCommand,
    ) -> Tuple[Optional[Tuple[AssetDTO, ChartDataDTO]], list[str]]:
        """
        Handle CreateChartCommand.
        Returns ((asset_dto, chart_data_dto), errors).
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Check user exists
            user = await self.user_repository.get_by_id(command.user_id)
            if not user:
                raise EntityNotFoundError("User", str(command.user_id))
            
            # Create time range if specified
            time_range = None
            if command.time_range_start and command.time_range_end:
                from datetime import datetime
                time_range = TimeRange(
                    start_date=datetime.fromisoformat(command.time_range_start),
                    end_date=datetime.fromisoformat(command.time_range_end),
                )
            
            # Create chart configuration
            config = ChartConfiguration(
                user_id=command.user_id,
                name=command.name,
                chart_type=command.chart_type,
                data_source=command.data_source,
                x_axis_column=command.x_axis_column,
                y_axis_columns=command.y_axis_columns,
                group_by_column=command.group_by_column,
                aggregation_function=command.aggregation_function,
                title=command.title,
                x_axis_label=command.x_axis_label,
                y_axis_label=command.y_axis_label,
                color_scheme=command.color_scheme,
                theme=command.theme,
                width=command.width,
                height=command.height,
                show_legend=command.show_legend,
                show_grid=command.show_grid,
                show_tooltips=command.show_tooltips,
                stacked=command.stacked,
                time_range=time_range,
                filters=command.filters,
                limit=command.limit,
                description=command.description,
                tags=command.tags,
            )
            
            # Save configuration
            saved_config = await self.chart_config_repository.add(config)
            
            # Generate chart
            export_format = ExportFormat(command.export_format)
            asset, chart_data = await self.chart_service.generate_chart(
                config=saved_config,
                user_id=command.user_id,
                export_format=export_format,
            )
            
            # Convert to DTOs
            asset_dto = AssetDTO.from_entity(asset)
            chart_data_dto = ChartDataDTO.from_chart_data(chart_data)
            
            # Ensure file_path is set on asset DTO
            if hasattr(asset_dto, 'file_path'):
                asset_dto.file_path = asset.file_path
                asset_dto.file_name = asset.file_name
                asset_dto.file_size = asset.file_size
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish("chart.generated", {
                    "user_id": str(command.user_id),
                    "chart_config_id": str(saved_config.id),
                    "chart_type": command.chart_type.value,
                    "asset_id": str(asset.id),
                })
            
            logger.info(f"Chart generated: {saved_config.id}")
            
            return (asset_dto, chart_data_dto), []
            
        except EntityNotFoundError as e:
            logger.error(f"Entity not found: {e}")
            return None, [str(e)]
        except ChartGenerationFailedError as e:
            logger.error(f"Chart generation failed: {e}")
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error creating chart: {e}", exc_info=True)
            return None, [f"Internal server error: {str(e)}"]
    
    async def delete_asset(self, asset_id: UUID, user_id: UUID) -> Tuple[bool, list[str]]:
        """
        Delete an asset.
        Returns (success, errors).
        """
        try:
            # Get asset
            asset = await self.asset_repository.get_by_id(asset_id)
            if not asset:
                raise EntityNotFoundError("Asset", str(asset_id))
            
            # Check permissions
            if asset.user_id != user_id:
                # Check if admin
                user = await self.user_repository.get_by_id(user_id)
                if not user or getattr(user, 'role', None) != "admin":
                    return False, ["You don't have permission to delete this asset"]
            
            # Delete file from filesystem
            import os
            file_path = asset.file_path
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted asset file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete asset file {file_path}: {e}")
            else:
                logger.warning(f"Asset file not found or no path: {file_path}")
            
            # Delete from repository
            success = await self.asset_repository.delete(asset_id)
            
            if success:
                logger.info(f"Asset deleted: {asset_id}")
                # Publish event
                if self.event_bus:
                    await self.event_bus.publish("asset.deleted", {
                        "user_id": str(user_id),
                        "asset_id": str(asset_id),
                        "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else str(asset.asset_type),
                    })
            else:
                logger.error(f"Failed to delete asset from repository: {asset_id}")
            
            return success, []
            
        except EntityNotFoundError as e:
            logger.error(f"Asset not found: {e}")
            return False, [str(e)]
        except Exception as e:
            logger.error(f"Error deleting asset: {e}", exc_info=True)
            return False, [f"Internal server error: {str(e)}"]
    
    async def get_asset(self, asset_id: UUID, user_id: UUID) -> Tuple[Optional[AssetDTO], list[str]]:
        """
        Get an asset by ID.
        Returns (asset_dto, errors).
        """
        try:
            # Get asset
            asset = await self.asset_repository.get_by_id(asset_id)
            if not asset:
                raise EntityNotFoundError("Asset", str(asset_id))
            
            # Check permissions
            if asset.user_id != user_id:
                # Check if admin
                user = await self.user_repository.get_by_id(user_id)
                if not user or getattr(user, 'role', None) != "admin":
                    return None, ["You don't have permission to view this asset"]
            
            # Convert to DTO
            asset_dto = AssetDTO.from_entity(asset)
            
            # Ensure file_path is set
            if hasattr(asset_dto, 'file_path'):
                asset_dto.file_path = asset.file_path
                asset_dto.file_name = asset.file_name
                asset_dto.file_size = asset.file_size
            
            return asset_dto, []
            
        except EntityNotFoundError as e:
            logger.error(f"Asset not found: {e}")
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error getting asset: {e}", exc_info=True)
            return None, [f"Internal server error: {str(e)}"]
    
    async def list_user_assets(
        self,
        user_id: UUID,
        asset_type: Optional[AssetType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AssetDTO], list[str]]:
        """
        List assets for a user.
        Returns (asset_dtos, errors).
        """
        try:
            # Get assets
            assets = await self.asset_repository.get_by_user_id(
                user_id=user_id,
                asset_type=asset_type,
                limit=limit,
                offset=offset,
            )
            
            # Convert to DTOs
            asset_dtos = []
            for asset in assets:
                dto = AssetDTO.from_entity(asset)
                # Ensure file_path is set
                if hasattr(dto, 'file_path'):
                    dto.file_path = asset.file_path
                    dto.file_name = asset.file_name
                    dto.file_size = asset.file_size
                asset_dtos.append(dto)
            
            return asset_dtos, []
            
        except Exception as e:
            logger.error(f"Error listing assets: {e}", exc_info=True)
            return [], [f"Internal server error: {str(e)}"]