"""
File-based implementation of asset repository.
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from uuid import UUID

from src.domain.entities.generated_asset import GeneratedAsset
from src.domain.repositories.asset_repository import IAssetRepository
from src.domain.exceptions import EntityNotFoundError
from src.infrastructure.database.sqlite.connection import db_connection
from src.shared.config import settings
from src.shared.constants import AssetType

logger = logging.getLogger(__name__)


class FileAssetRepository(IAssetRepository):
    """
    File-based implementation of IAssetRepository.
    Stores metadata in SQLite and files on disk.
    """
    
    def __init__(self):
        self.base_path = Path(settings.BASE_DIR)
        self.images_path = Path(settings.GENERATED_IMAGES_PATH)
        self.charts_path = Path(settings.GENERATED_CHARTS_PATH)
        
        # Ensure directories exist
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.charts_path.mkdir(parents=True, exist_ok=True)
    
    async def get_by_id(self, id: UUID) -> Optional[GeneratedAsset]:
        """Get asset by ID."""
        query = "SELECT * FROM assets WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[GeneratedAsset]:
        """Get all assets with pagination."""
        query = "SELECT * FROM assets ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = db_connection.fetch_all(query, (limit, skip))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        asset_type: Optional[AssetType] = None,
    ) -> List[GeneratedAsset]:
        """Get assets for a user."""
        if asset_type:
            query = """
                SELECT * FROM assets 
                WHERE user_id = ? AND asset_type = ?
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), asset_type.value, limit, skip)
        else:
            query = """
                SELECT * FROM assets 
                WHERE user_id = ?
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), limit, skip)
        
        rows = db_connection.fetch_all(query, params)
        return [self._row_to_entity(row) for row in rows]
    
    async def get_by_type(
        self,
        user_id: UUID,
        asset_type: AssetType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[GeneratedAsset]:
        """Get assets by type."""
        return await self.get_by_user_id(user_id, skip, limit, asset_type)
    
    async def get_favorites(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get user's favorite assets."""
        query = """
            SELECT * FROM assets 
            WHERE user_id = ? AND is_favorite = 1
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), limit))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_recent_assets(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> List[GeneratedAsset]:
        """Get user's recent assets."""
        query = """
            SELECT * FROM assets 
            WHERE user_id = ?
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), limit))
        return [self._row_to_entity(row) for row in rows]
    
    async def search_assets(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[GeneratedAsset]:
        """Search user's assets."""
        search_query = f"%{query}%"
        sql = """
            SELECT * FROM assets 
            WHERE user_id = ? 
            AND (title LIKE ? OR description LIKE ? OR prompt LIKE ? OR file_name LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
        """
        params = (str(user_id), search_query, search_query, search_query, search_query, limit)
        rows = db_connection.fetch_all(sql, params)
        return [self._row_to_entity(row) for row in rows]
    
    async def get_by_conversation(
        self,
        conversation_id: UUID,
    ) -> List[GeneratedAsset]:
        """Get assets for a conversation."""
        query = """
            SELECT * FROM assets 
            WHERE conversation_id = ?
            ORDER BY created_at DESC
        """
        rows = db_connection.fetch_all(query, (str(conversation_id),))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_public_assets(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get public assets."""
        query = """
            SELECT * FROM assets 
            WHERE is_public = 1
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        rows = db_connection.fetch_all(query, (limit, skip))
        return [self._row_to_entity(row) for row in rows]
    
    async def add(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Add a new asset."""
        # Determine storage path based on asset type
        if asset.asset_type == AssetType.IMAGE:
            storage_dir = self.images_path
        elif asset.asset_type == AssetType.CHART:
            storage_dir = self.charts_path
        else:
            storage_dir = self.base_path / "data" / "exports"
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create user subdirectory
        user_dir = storage_dir / str(asset.user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate file path if not provided
        if not asset.file_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{asset.asset_type.value}_{timestamp}_{asset.id}.png"
            asset.file_path = str(user_dir / filename)
            asset.file_name = filename
        
        # Insert metadata into database
        query = """
            INSERT INTO assets (
                id, user_id, asset_type, file_path, file_name, file_size, mime_type,
                title, description, prompt, model_used, generation_params,
                generation_time_ms, tags, is_favorite, is_public,
                view_count, download_count, conversation_id, chart_configuration_id,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            str(asset.id),
            str(asset.user_id),
            asset.asset_type.value,
            asset.file_path,
            asset.file_name,
            asset.file_size,
            asset.mime_type,
            asset.title,
            asset.description,
            asset.prompt,
            asset.model_used,
            json.dumps(asset.generation_params),
            asset.generation_time_ms,
            json.dumps(asset.tags),
            1 if asset.is_favorite else 0,
            1 if asset.is_public else 0,
            asset.view_count,
            asset.download_count,
            str(asset.conversation_id) if asset.conversation_id else None,
            str(asset.chart_configuration_id) if asset.chart_configuration_id else None,
            asset.created_at.isoformat() if asset.created_at else datetime.utcnow().isoformat(),
        ))
        
        logger.info(f"Asset created: {asset.id} ({asset.asset_type.value})")
        return asset
    
    async def update(self, asset: GeneratedAsset) -> GeneratedAsset:
        """Update an existing asset."""
        query = """
            UPDATE assets SET
                title = ?, description = ?, tags = ?, is_favorite = ?, is_public = ?,
                view_count = ?, download_count = ?
            WHERE id = ?
        """
        
        db_connection.execute(query, (
            asset.title,
            asset.description,
            json.dumps(asset.tags),
            1 if asset.is_favorite else 0,
            1 if asset.is_public else 0,
            asset.view_count,
            asset.download_count,
            str(asset.id),
        ))
        
        logger.info(f"Asset updated: {asset.id}")
        return asset
    
    async def delete(self, id: UUID) -> bool:
        """Delete an asset and its file."""
        # Get asset first to get file path
        asset = await self.get_by_id(id)
        if not asset:
            return False
        
        # Delete file from disk
        try:
            if os.path.exists(asset.file_path):
                os.remove(asset.file_path)
                logger.info(f"Deleted asset file: {asset.file_path}")
        except Exception as e:
            logger.error(f"Error deleting asset file {asset.file_path}: {e}")
        
        # Delete from database
        query = "DELETE FROM assets WHERE id = ?"
        cursor = db_connection.execute(query, (str(id),))
        
        success = cursor.rowcount > 0 if cursor else False
        if success:
            logger.info(f"Asset deleted: {id}")
        
        return success
    
    async def exists(self, id: UUID) -> bool:
        """Check if asset exists."""
        query = "SELECT 1 FROM assets WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        return row is not None
    
    async def count(self) -> int:
        """Get total count of assets."""
        query = "SELECT COUNT(*) as count FROM assets"
        row = db_connection.fetch_one(query)
        return row["count"] if row else 0
    
    async def increment_view_count(self, asset_id: UUID) -> None:
        """Increment view count."""
        query = "UPDATE assets SET view_count = view_count + 1 WHERE id = ?"
        db_connection.execute(query, (str(asset_id),))
    
    async def increment_download_count(self, asset_id: UUID) -> None:
        """Increment download count."""
        query = "UPDATE assets SET download_count = download_count + 1 WHERE id = ?"
        db_connection.execute(query, (str(asset_id),))
    
    async def get_storage_stats(self, user_id: UUID) -> dict:
        """Get storage statistics for user."""
        query = """
            SELECT 
                COUNT(*) as total_count,
                SUM(file_size) as total_size,
                asset_type,
                COUNT(*) as type_count
            FROM assets 
            WHERE user_id = ?
            GROUP BY asset_type
        """
        rows = db_connection.fetch_all(query, (str(user_id),))
        
        stats = {
            "total_count": 0,
            "total_size_bytes": 0,
            "by_type": {},
        }
        
        for row in rows:
            stats["total_count"] += row["type_count"]
            stats["total_size_bytes"] += row["total_size"] or 0
            stats["by_type"][row["asset_type"]] = {
                "count": row["type_count"],
                "size_bytes": row["total_size"] or 0,
            }
        
        return stats
    
    async def delete_old_assets(
        self,
        user_id: UUID,
        days_old: int = 30,
        keep_favorites: bool = True,
    ) -> int:
        """Delete old assets."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Get old assets
        query = """
            SELECT id, file_path FROM assets 
            WHERE user_id = ? AND created_at < ?
        """
        params = [str(user_id), cutoff_date.isoformat()]
        
        if keep_favorites:
            query += " AND is_favorite = 0"
        
        rows = db_connection.fetch_all(query, params)
        
        deleted_count = 0
        for row in rows:
            asset_id = row["id"]
            file_path = row["file_path"]
            
            # Delete file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
            
            # Delete from database
            db_connection.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} old assets for user {user_id}")
        return deleted_count
    
    async def get_total_size(self, user_id: UUID) -> int:
        """Get total size of user's assets."""
        query = "SELECT SUM(file_size) as total FROM assets WHERE user_id = ?"
        row = db_connection.fetch_one(query, (str(user_id),))
        return row["total"] if row and row["total"] else 0
    
    async def get_by_tag(
        self,
        user_id: UUID,
        tag: str,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get assets by tag."""
        query = """
            SELECT * FROM assets 
            WHERE user_id = ? AND tags LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), f'%"{tag}"%', limit))
        return [self._row_to_entity(row) for row in rows]
    
    def save_file(self, asset_id: UUID, file_data: bytes, filename: str, mime_type: str) -> str:
        """
        Save a file to disk and return the file path.
        """
        from src.shared.config import settings
        
        # Determine directory
        if "image" in mime_type:
            storage_dir = self.images_path
        else:
            storage_dir = self.base_path / "data" / "uploads"
            storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dated subdirectory
        date_dir = storage_dir / datetime.utcnow().strftime("%Y/%m/%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = filename.split(".")[-1] if "." in filename else "bin"
        unique_filename = f"{asset_id}.{file_ext}"
        file_path = date_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        logger.info(f"Saved file: {file_path}")
        return str(file_path)
    
    def get_file_data(self, file_path: str) -> Optional[bytes]:
        """
        Read file data from disk.
        """
        try:
            full_path = self.base_path / file_path if not os.path.isabs(file_path) else Path(file_path)
            
            if full_path.exists():
                with open(full_path, "rb") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        
        return None
    
    def _row_to_entity(self, row: dict) -> GeneratedAsset:
        """Convert database row to GeneratedAsset entity."""
        from src.shared.constants import AssetType
        
        return GeneratedAsset(
            id=UUID(row["id"]),
            user_id=UUID(row["user_id"]),
            asset_type=AssetType(row["asset_type"]),
            file_path=row["file_path"],
            file_name=row["file_name"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            title=row.get("title"),
            description=row.get("description"),
            prompt=row.get("prompt"),
            model_used=row.get("model_used"),
            generation_params=json.loads(row["generation_params"]) if row.get("generation_params") else {},
            generation_time_ms=row.get("generation_time_ms"),
            tags=json.loads(row["tags"]) if row.get("tags") else [],
            is_favorite=bool(row["is_favorite"]),
            is_public=bool(row["is_public"]),
            view_count=row["view_count"],
            download_count=row["download_count"],
            conversation_id=UUID(row["conversation_id"]) if row.get("conversation_id") else None,
            chart_configuration_id=UUID(row["chart_configuration_id"]) if row.get("chart_configuration_id") else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )