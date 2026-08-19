"""
API Key management for programmatic access.
"""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.infrastructure.database.sqlite.connection import db_connection
from src.domain.value_objects.api_key import ApiKey, ApiKeyScope

logger = logging.getLogger(__name__)


class ApiKeyManager:
    """
    Manager for creating, validating, and revoking API keys.
    """
    
    def __init__(self):
        self.key_prefix = "eap_"
    
    def generate_key(self) -> tuple[str, str]:
        """
        Generate a new API key.
        Returns (raw_key, key_hash).
        """
        raw_key = f"{self.key_prefix}{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)
        return raw_key, key_hash
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def create_api_key(
        self,
        user_id: UUID,
        name: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new API key for a user.
        """
        raw_key, key_hash = self.generate_key()
        prefix = raw_key[:12]  # eap_ + 8 chars
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        import json
        from uuid import uuid4
        
        key_id = str(uuid4())
        
        query = """
            INSERT INTO api_keys (
                id, user_id, key_hash, name, prefix, scopes,
                is_active, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            key_id,
            str(user_id),
            key_hash,
            name,
            prefix,
            json.dumps(scopes),
            1,  # is_active
            expires_at.isoformat() if expires_at else None,
            datetime.utcnow().isoformat(),
        ))
        
        logger.info(f"API key created for user {user_id}: {name} ({key_id})")
        
        return {
            "id": key_id,
            "name": name,
            "key": raw_key,  # Only shown once!
            "prefix": prefix,
            "scopes": scopes,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
    
    async def validate_api_key(self, raw_key: str) -> tuple[bool, Optional[UUID], List[str], Optional[str]]:
        """
        Validate an API key.
        Returns (is_valid, user_id, scopes, error_message).
        """
        if not raw_key or not raw_key.startswith(self.key_prefix):
            return False, None, [], "Invalid API key format"
        
        key_hash = self._hash_key(raw_key)
        
        query = """
            SELECT user_id, scopes, is_active, expires_at
            FROM api_keys
            WHERE key_hash = ?
        """
        
        row = db_connection.fetch_one(query, (key_hash,))
        
        if not row:
            return False, None, [], "Invalid API key"
        
        # Check if active
        if not row["is_active"]:
            return False, None, [], "API key is revoked"
        
        # Check expiration
        if row["expires_at"]:
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at < datetime.utcnow():
                return False, None, [], "API key has expired"
        
        # Update last used
        update_query = """
            UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?
        """
        db_connection.execute(update_query, (datetime.utcnow().isoformat(), key_hash))
        
        import json
        scopes = json.loads(row["scopes"]) if row["scopes"] else []
        user_id = UUID(row["user_id"])
        
        return True, user_id, scopes, None
    
    async def revoke_api_key(self, key_id: str, user_id: UUID) -> bool:
        """
        Revoke an API key.
        """
        query = """
            UPDATE api_keys SET is_active = 0
            WHERE id = ? AND user_id = ?
        """
        
        cursor = db_connection.execute(query, (key_id, str(user_id)))
        success = cursor.rowcount > 0 if cursor else False
        
        if success:
            logger.info(f"API key revoked: {key_id}")
        
        return success
    
    async def list_api_keys(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        List all API keys for a user (without the actual keys).
        """
        query = """
            SELECT id, name, prefix, scopes, is_active,
                   last_used_at, expires_at, created_at
            FROM api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
        """
        
        rows = db_connection.fetch_all(query, (str(user_id),))
        
        import json
        
        keys = []
        for row in rows:
            keys.append({
                "id": row["id"],
                "name": row["name"],
                "prefix": row["prefix"],
                "scopes": json.loads(row["scopes"]) if row["scopes"] else [],
                "is_active": bool(row["is_active"]),
                "last_used_at": row["last_used_at"],
                "expires_at": row["expires_at"],
                "created_at": row["created_at"],
                "is_expired": (
                    datetime.fromisoformat(row["expires_at"]) < datetime.utcnow()
                    if row["expires_at"] else False
                ),
            })
        
        return keys
    
    async def delete_api_key(self, key_id: str, user_id: UUID) -> bool:
        """
        Permanently delete an API key.
        """
        query = "DELETE FROM api_keys WHERE id = ? AND user_id = ?"
        cursor = db_connection.execute(query, (key_id, str(user_id)))
        
        success = cursor.rowcount > 0 if cursor else False
        
        if success:
            logger.info(f"API key deleted: {key_id}")
        
        return success
    
    async def has_scope(self, raw_key: str, required_scope: str) -> bool:
        """
        Check if API key has a specific scope.
        """
        is_valid, user_id, scopes, _ = await self.validate_api_key(raw_key)
        
        if not is_valid:
            return False
        
        return required_scope in scopes or "admin" in scopes
    
    async def cleanup_expired_keys(self) -> int:
        """
        Deactivate expired API keys.
        """
        query = """
            UPDATE api_keys 
            SET is_active = 0
            WHERE expires_at IS NOT NULL 
            AND expires_at < ? 
            AND is_active = 1
        """
        
        cursor = db_connection.execute(query, (datetime.utcnow().isoformat(),))
        count = cursor.rowcount if cursor else 0
        
        if count > 0:
            logger.info(f"Deactivated {count} expired API keys")
        
        return count