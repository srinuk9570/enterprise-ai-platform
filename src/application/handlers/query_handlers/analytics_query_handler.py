"""
Handler for analytics-related queries.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

from src.application.queries import (
    GetUserDashboardQuery,
    ExportChartDataQuery,
    GetUserAssetsQuery,
)
from src.application.dtos import AssetDTO, ChartDataDTO
from src.domain.exceptions import EntityNotFoundError
from src.shared.enums import ExportFormat

logger = logging.getLogger(__name__)


class AnalyticsQueryHandler:
    """
    Handler for analytics-related queries.
    """
    
    def __init__(
        self,
        user_repository,
        conversation_repository,
        asset_repository,
        chart_config_repository,
        chart_service,
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository
        self.asset_repository = asset_repository
        self.chart_config_repository = chart_config_repository
        self.chart_service = chart_service
    
    async def handle_get_user_dashboard(
        self,
        query: GetUserDashboardQuery,
    ) -> tuple[Optional[Dict[str, Any]], list[str]]:
        """
        Handle GetUserDashboardQuery.
        Returns (dashboard_data, errors).
        """
        # Validate query
        is_valid, errors = query.validate()
        if not is_valid:
            return None, errors
        
        try:
            dashboard = {
                "user_id": str(query.user_id),
                "period": query.period,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
            # Get user info
            user = await self.user_repository.get_by_id(query.user_id)
            if user:
                dashboard["user"] = {
                    "username": user.username,
                    "role": user.role.value,
                    "member_since": user.created_at.isoformat() if user.created_at else None,
                }
            
            days = query.get_days_from_period()
            start_date = datetime.utcnow() - timedelta(days=days) if days else None
            
            # Conversation stats
            if query.include_conversations:
                conversations = await self.conversation_repository.get_by_user_id(
                    user_id=query.user_id,
                    limit=1000,
                )
                
                # Filter by date if period specified
                if start_date:
                    conversations = [
                        c for c in conversations
                        if c.created_at and c.created_at >= start_date
                    ]
                
                dashboard["conversations"] = {
                    "total": len(conversations),
                    "active": len([c for c in conversations if c.status.value == "active"]),
                    "archived": len([c for c in conversations if c.status.value == "archived"]),
                    "total_tokens": sum(c.total_tokens for c in conversations),
                    "total_messages": sum(c.message_count for c in conversations),
                }
                
                # Recent conversations
                if query.include_recent_activity:
                    recent = conversations[:query.recent_conversations_limit]
                    dashboard["recent_conversations"] = [
                        {
                            "id": str(c.id),
                            "title": c.title,
                            "model_name": c.model_name,
                            "message_count": c.message_count,
                            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                        }
                        for c in recent
                    ]
            
            # Asset stats
            if query.include_assets:
                assets = await self.asset_repository.get_by_user_id(
                    user_id=query.user_id,
                    limit=1000,
                )
                
                if start_date:
                    assets = [
                        a for a in assets
                        if a.created_at and a.created_at >= start_date
                    ]
                
                images = [a for a in assets if a.asset_type.value == "image"]
                charts = [a for a in assets if a.asset_type.value == "chart"]
                
                dashboard["assets"] = {
                    "total": len(assets),
                    "images": len(images),
                    "charts": len(charts),
                    "total_size_bytes": sum(a.file_size for a in assets),
                    "favorites": len([a for a in assets if a.is_favorite]),
                }
                
                # Recent assets
                if query.include_recent_activity:
                    recent_assets = sorted(
                        assets,
                        key=lambda a: a.created_at or datetime.min,
                        reverse=True,
                    )[:query.recent_assets_limit]
                    
                    dashboard["recent_assets"] = [
                        {
                            "id": str(a.id),
                            "title": a.title or a.file_name,
                            "type": a.asset_type.value,
                            "file_name": a.file_name,
                            "created_at": a.created_at.isoformat() if a.created_at else None,
                        }
                        for a in recent_assets
                    ]
            
            # Usage stats
            if query.include_usage_stats:
                stats = await self.conversation_repository.get_conversation_stats(query.user_id)
                dashboard["usage"] = stats
            
            return dashboard, []
            
        except Exception as e:
            logger.error(f"Error getting user dashboard: {e}")
            return None, ["Internal server error"]
    
    async def handle_export_chart_data(
        self,
        query: ExportChartDataQuery,
    ) -> tuple[Optional[tuple[bytes, str, str]], list[str]]:
        """
        Handle ExportChartDataQuery.
        Returns ((data_bytes, filename, content_type), errors).
        """
        # Validate query
        is_valid, errors = query.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Get chart configuration
            config = await self.chart_config_repository.get_by_id(query.chart_config_id)
            if not config:
                raise EntityNotFoundError("ChartConfiguration", str(query.chart_config_id))
            
            # Check permissions
            if config.user_id != query.user_id:
                user = await self.user_repository.get_by_id(query.user_id)
                if not user or user.role != "admin":
                    return None, ["You don't have permission to export this chart"]
            
            # Apply time range if specified
            if query.time_range_start and query.time_range_end:
                from src.domain.value_objects.time_range import TimeRange
                config.time_range = TimeRange(
                    start_date=datetime.fromisoformat(query.time_range_start),
                    end_date=datetime.fromisoformat(query.time_range_end),
                )
            
            # Apply limit if specified
            if query.limit:
                config.limit = query.limit
            
            # Load and process data
            raw_data = await self.chart_service._load_data(config)
            chart_data = await self.chart_service._process_data(config, raw_data)
            
            # Export based on format
            export_format = ExportFormat(query.export_format)
            
            if export_format in [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.PDF]:
                # Render chart
                rendered = await self.chart_service._render_chart(config, chart_data, export_format)
                
                with open(rendered["file_path"], "rb") as f:
                    data_bytes = f.read()
                
                filename = f"chart_{config.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{query.get_file_extension()}"
                
            else:
                # Export data
                filename, data_bytes = await self.chart_service.export_chart_data(
                    chart_data=chart_data,
                    export_format=export_format,
                )
            
            return (data_bytes, filename, query.get_content_type()), []
            
        except EntityNotFoundError as e:
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error exporting chart data: {e}")
            return None, ["Internal server error"]
    
    async def handle_get_user_assets(
        self,
        query: GetUserAssetsQuery,
    ) -> tuple[List[AssetDTO], int, list[str]]:
        """
        Handle GetUserAssetsQuery.
        Returns (asset_dtos, total_count, errors).
        """
        # Validate query
        is_valid, errors = query.validate()
        if not is_valid:
            return [], 0, errors
        
        try:
            from src.shared.constants import AssetType
            
            asset_type = AssetType(query.asset_type) if query.asset_type else None
            
            # Get assets
            assets = await self.asset_repository.get_by_user_id(
                user_id=query.user_id,
                skip=query.skip,
                limit=query.limit,
                asset_type=asset_type,
            )
            
            # Apply additional filters
            filtered = []
            for asset in assets:
                # Tags filter
                if query.tags:
                    if not any(tag in asset.tags for tag in query.tags):
                        continue
                
                # Favorite filter
                if query.is_favorite is not None and asset.is_favorite != query.is_favorite:
                    continue
                
                # Public filter
                if query.is_public is not None and asset.is_public != query.is_public:
                    continue
                
                # Conversation filter
                if query.conversation_id and asset.conversation_id != query.conversation_id:
                    continue
                
                # Chart config filter
                if query.chart_config_id and asset.chart_configuration_id != query.chart_config_id:
                    continue
                
                # Date range filter
                if query.start_date:
                    start = datetime.fromisoformat(query.start_date)
                    if asset.created_at and asset.created_at < start:
                        continue
                
                if query.end_date:
                    end = datetime.fromisoformat(query.end_date)
                    if asset.created_at and asset.created_at > end:
                        continue
                
                filtered.append(asset)
            
            # Convert to DTOs
            dtos = [AssetDTO.from_entity(asset) for asset in filtered]
            
            return dtos, len(dtos), []
            
        except Exception as e:
            logger.error(f"Error getting user assets: {e}")
            return [], 0, ["Internal server error"]