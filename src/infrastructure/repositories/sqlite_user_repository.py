"""
SQLite implementation of user repository.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.repositories.user_repository import IUserRepository
from src.domain.exceptions import EntityNotFoundError, DuplicateEntityError
from src.infrastructure.database.sqlite.connection import db_connection
from src.shared.constants import UserRole

logger = logging.getLogger(__name__)


class SQLiteUserRepository(IUserRepository):
    """
    SQLite implementation of IUserRepository.
    """
    
    async def get_by_id(self, id: UUID) -> Optional[User]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = ?"
        row = db_connection.fetch_one(query, (email.lower(),))
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = ?"
        row = db_connection.fetch_one(query, (username,))
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        query = "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = db_connection.fetch_all(query, (limit, skip))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users."""
        query = """
            SELECT * FROM users 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        rows = db_connection.fetch_all(query, (limit, skip))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_users_by_role(
        self,
        role: UserRole,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """Get users by role."""
        query = """
            SELECT * FROM users 
            WHERE role = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        rows = db_connection.fetch_all(query, (role.value, limit, skip))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def add(self, user: User) -> User:
        """Add a new user."""
        # Check for duplicates
        if await self.email_exists(str(user.email)):
            raise DuplicateEntityError("User", "email", str(user.email))
        
        if await self.username_exists(user.username):
            raise DuplicateEntityError("User", "username", user.username)
        
        query = """
            INSERT INTO users (
                id, email, username, hashed_password, full_name, role,
                is_active, is_verified, avatar_url, bio, preferences,
                created_at, updated_at, last_login_at, email_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            str(user.id),
            str(user.email).lower(),
            user.username,
            user.hashed_password,
            user.full_name,
            user.role.value,
            1 if user.is_active else 0,
            1 if user.is_verified else 0,
            user.avatar_url,
            user.bio,
            json.dumps(user.preferences),
            user.created_at.isoformat() if user.created_at else None,
            user.updated_at.isoformat() if user.updated_at else None,
            user.last_login_at.isoformat() if user.last_login_at else None,
            user.email_verified_at.isoformat() if user.email_verified_at else None,
        ))
        
        logger.info(f"User created: {user.username} ({user.id})")
        return user
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        query = """
            UPDATE users SET
                email = ?, username = ?, hashed_password = ?, full_name = ?,
                role = ?, is_active = ?, is_verified = ?, avatar_url = ?,
                bio = ?, preferences = ?, updated_at = ?, last_login_at = ?,
                email_verified_at = ?
            WHERE id = ?
        """
        
        db_connection.execute(query, (
            str(user.email).lower(),
            user.username,
            user.hashed_password,
            user.full_name,
            user.role.value,
            1 if user.is_active else 0,
            1 if user.is_verified else 0,
            user.avatar_url,
            user.bio,
            json.dumps(user.preferences),
            datetime.utcnow().isoformat(),
            user.last_login_at.isoformat() if user.last_login_at else None,
            user.email_verified_at.isoformat() if user.email_verified_at else None,
            str(user.id),
        ))
        
        logger.info(f"User updated: {user.id}")
        return user
    
    async def delete(self, id: UUID) -> bool:
        """Delete a user by ID."""
        query = "DELETE FROM users WHERE id = ?"
        cursor = db_connection.execute(query, (str(id),))
        
        success = cursor.rowcount > 0 if cursor else False
        if success:
            logger.info(f"User deleted: {id}")
        
        return success
    
    async def exists(self, id: UUID) -> bool:
        """Check if user exists."""
        query = "SELECT 1 FROM users WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        return row is not None
    
    async def count(self) -> int:
        """Get total count of users."""
        query = "SELECT COUNT(*) as count FROM users"
        row = db_connection.fetch_one(query)
        return row["count"] if row else 0
    
    async def email_exists(self, email: str) -> bool:
        """Check if email exists."""
        query = "SELECT 1 FROM users WHERE email = ?"
        row = db_connection.fetch_one(query, (email.lower(),))
        return row is not None
    
    async def username_exists(self, username: str) -> bool:
        """Check if username exists."""
        query = "SELECT 1 FROM users WHERE username = ?"
        row = db_connection.fetch_one(query, (username,))
        return row is not None
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update last login timestamp."""
        query = "UPDATE users SET last_login_at = ? WHERE id = ?"
        db_connection.execute(query, (datetime.utcnow().isoformat(), str(user_id)))
    
    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        """Update user's password."""
        query = "UPDATE users SET hashed_password = ?, updated_at = ? WHERE id = ?"
        db_connection.execute(query, (
            hashed_password,
            datetime.utcnow().isoformat(),
            str(user_id),
        ))
    
    async def verify_email(self, user_id: UUID) -> None:
        """Mark email as verified."""
        query = """
            UPDATE users 
            SET is_verified = 1, email_verified_at = ?, updated_at = ?
            WHERE id = ?
        """
        now = datetime.utcnow().isoformat()
        db_connection.execute(query, (now, now, str(user_id)))
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username, email, or full name."""
        search_query = f"%{query}%"
        sql = """
            SELECT * FROM users 
            WHERE username LIKE ? OR email LIKE ? OR full_name LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = db_connection.fetch_all(sql, (search_query, search_query, search_query, limit))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics."""
        stats = {}
        
        # Conversation count
        conv_query = "SELECT COUNT(*) as count FROM conversations WHERE user_id = ?"
        conv_row = db_connection.fetch_one(conv_query, (str(user_id),))
        stats["conversation_count"] = conv_row["count"] if conv_row else 0
        
        # Asset count
        asset_query = "SELECT COUNT(*) as count FROM assets WHERE user_id = ?"
        asset_row = db_connection.fetch_one(asset_query, (str(user_id),))
        stats["asset_count"] = asset_row["count"] if asset_row else 0
        
        # Total tokens
        token_query = "SELECT SUM(total_tokens) as total FROM conversations WHERE user_id = ?"
        token_row = db_connection.fetch_one(token_query, (str(user_id),))
        stats["total_tokens"] = token_row["total"] if token_row and token_row["total"] else 0
        
        return stats
    
    def _row_to_entity(self, row: dict) -> User:
        """Convert database row to User entity."""
        return User(
            id=UUID(row["id"]),
            email=Email(row["email"]),
            username=row["username"],
            hashed_password=row["hashed_password"],
            full_name=row.get("full_name"),
            role=UserRole(row["role"]),
            is_active=bool(row["is_active"]),
            is_verified=bool(row["is_verified"]),
            avatar_url=row.get("avatar_url"),
            bio=row.get("bio"),
            preferences=json.loads(row["preferences"]) if row.get("preferences") else {},
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
            last_login_at=datetime.fromisoformat(row["last_login_at"]) if row.get("last_login_at") else None,
            email_verified_at=datetime.fromisoformat(row["email_verified_at"]) if row.get("email_verified_at") else None,
        )