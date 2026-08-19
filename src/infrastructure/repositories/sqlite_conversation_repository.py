"""
SQLite implementation of conversation repository.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.repositories.conversation_repository import IConversationRepository
from src.domain.exceptions import EntityNotFoundError
from src.infrastructure.database.sqlite.connection import db_connection
from src.shared.constants import ConversationStatus, MessageRole

logger = logging.getLogger(__name__)


class SQLiteConversationRepository(IConversationRepository):
    """
    SQLite implementation of IConversationRepository.
    """
    
    async def get_by_id(self, id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        query = "SELECT * FROM conversations WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        
        if not row:
            return None
        
        return self._row_to_entity(row)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations with pagination."""
        query = "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        rows = db_connection.fetch_all(query, (limit, skip))
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ConversationStatus] = None,
    ) -> List[Conversation]:
        """Get conversations for a user."""
        if status:
            query = """
                SELECT * FROM conversations 
                WHERE user_id = ? AND status = ?
                ORDER BY is_pinned DESC, updated_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), status.value, limit, skip)
        else:
            query = """
                SELECT * FROM conversations 
                WHERE user_id = ?
                ORDER BY is_pinned DESC, updated_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (str(user_id), limit, skip)
        
        rows = db_connection.fetch_all(query, params)
        return [self._row_to_entity(row) for row in rows]
    
    async def get_active_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Conversation]:
        """Get user's active conversations."""
        return await self.get_by_user_id(
            user_id, skip, limit, ConversationStatus.ACTIVE
        )
    
    async def get_pinned_conversations(
        self,
        user_id: UUID,
    ) -> List[Conversation]:
        """Get user's pinned conversations."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND is_pinned = 1 AND status = 'active'
            ORDER BY updated_at DESC
        """
        rows = db_connection.fetch_all(query, (str(user_id),))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_favorite_conversations(
        self,
        user_id: UUID,
    ) -> List[Conversation]:
        """Get user's favorite conversations."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND is_favorite = 1
            ORDER BY updated_at DESC
        """
        rows = db_connection.fetch_all(query, (str(user_id),))
        return [self._row_to_entity(row) for row in rows]
    
    async def search_conversations(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10,
    ) -> List[Conversation]:
        """Search user's conversations."""
        search_query = f"%{query}%"
        
        # Search in titles
        sql = """
            SELECT DISTINCT c.* FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ?
            AND (c.title LIKE ? OR m.content LIKE ?)
            ORDER BY c.updated_at DESC
            LIMIT ?
        """
        rows = db_connection.fetch_all(sql, (str(user_id), search_query, search_query, limit))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_recent_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[Conversation]:
        """Get user's recent conversations."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND status = 'active'
            ORDER BY updated_at DESC 
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), limit))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """Get conversation with all messages loaded."""
        conversation = await self.get_by_id(conversation_id)
        if not conversation:
            return None
        
        messages = await self.get_messages(conversation_id)
        conversation.messages = messages
        conversation.message_count = len(messages)
        
        return conversation
    
    async def add(self, conversation: Conversation) -> Conversation:
        """Add a new conversation."""
        query = """
            INSERT INTO conversations (
                id, user_id, title, model_name, status, system_prompt,
                model_parameters, tags, is_pinned, is_favorite,
                total_tokens, message_count, summary, category,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            str(conversation.id),
            str(conversation.user_id),
            conversation.title,
            conversation.model_name,
            conversation.status.value,
            conversation.system_prompt,
            json.dumps(conversation.model_parameters),
            json.dumps(conversation.tags),
            1 if conversation.is_pinned else 0,
            1 if conversation.is_favorite else 0,
            conversation.total_tokens,
            conversation.message_count,
            conversation.summary,
            conversation.category,
            conversation.created_at.isoformat() if conversation.created_at else datetime.utcnow().isoformat(),
            conversation.updated_at.isoformat() if conversation.updated_at else datetime.utcnow().isoformat(),
        ))
        
        logger.info(f"Conversation created: {conversation.id}")
        return conversation
    
    async def update(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation."""
        query = """
            UPDATE conversations SET
                title = ?, model_name = ?, status = ?, system_prompt = ?,
                model_parameters = ?, tags = ?, is_pinned = ?, is_favorite = ?,
                total_tokens = ?, message_count = ?, summary = ?, category = ?,
                updated_at = ?
            WHERE id = ?
        """
        
        db_connection.execute(query, (
            conversation.title,
            conversation.model_name,
            conversation.status.value,
            conversation.system_prompt,
            json.dumps(conversation.model_parameters),
            json.dumps(conversation.tags),
            1 if conversation.is_pinned else 0,
            1 if conversation.is_favorite else 0,
            conversation.total_tokens,
            conversation.message_count,
            conversation.summary,
            conversation.category,
            datetime.utcnow().isoformat(),
            str(conversation.id),
        ))
        
        logger.info(f"Conversation updated: {conversation.id}")
        return conversation
    
    async def delete(self, id: UUID) -> bool:
        """Delete a conversation."""
        query = "DELETE FROM conversations WHERE id = ?"
        cursor = db_connection.execute(query, (str(id),))
        
        success = cursor.rowcount > 0 if cursor else False
        if success:
            logger.info(f"Conversation deleted: {id}")
        
        return success
    
    async def exists(self, id: UUID) -> bool:
        """Check if conversation exists."""
        query = "SELECT 1 FROM conversations WHERE id = ?"
        row = db_connection.fetch_one(query, (str(id),))
        return row is not None
    
    async def count(self) -> int:
        """Get total count of conversations."""
        query = "SELECT COUNT(*) as count FROM conversations"
        row = db_connection.fetch_one(query)
        return row["count"] if row else 0
    
    async def add_message(
        self,
        conversation_id: UUID,
        message: Message,
    ) -> Message:
        """Add a message to a conversation."""
        query = """
            INSERT INTO messages (
                id, conversation_id, role, content, sequence_number,
                token_count, model_used, generation_time_ms, finish_reason,
                is_edited, edited_at, original_content, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        db_connection.execute(query, (
            str(message.id),
            str(conversation_id),
            message.role.value,
            message.content,
            message.sequence_number,
            message.token_count,
            message.model_used,
            message.generation_time_ms,
            message.finish_reason,
            1 if message.is_edited else 0,
            message.edited_at.isoformat() if message.edited_at else None,
            message.original_content,
            json.dumps(message.metadata),
            message.created_at.isoformat() if message.created_at else datetime.utcnow().isoformat(),
        ))
        
        # Update conversation metadata
        update_query = """
            UPDATE conversations SET
                message_count = message_count + 1,
                total_tokens = total_tokens + ?,
                updated_at = ?
            WHERE id = ?
        """
        db_connection.execute(update_query, (
            message.token_count,
            datetime.utcnow().isoformat(),
            str(conversation_id),
        ))
        
        logger.debug(f"Message added to conversation {conversation_id}: {message.id}")
        return message
    
    async def get_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """Get messages for a conversation."""
        query = """
            SELECT * FROM messages 
            WHERE conversation_id = ?
            ORDER BY sequence_number ASC
            LIMIT ? OFFSET ?
        """
        rows = db_connection.fetch_all(query, (str(conversation_id), limit, skip))
        return [self._row_to_message(row) for row in rows]
    
    async def get_message_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get a single message by ID."""
        query = "SELECT * FROM messages WHERE id = ?"
        row = db_connection.fetch_one(query, (str(message_id),))
        
        if not row:
            return None
        
        return self._row_to_message(row)
    
    async def update_message(self, message: Message) -> Message:
        """Update an existing message."""
        query = """
            UPDATE messages SET
                content = ?, is_edited = ?, edited_at = ?, original_content = ?,
                metadata = ?
            WHERE id = ?
        """
        
        db_connection.execute(query, (
            message.content,
            1 if message.is_edited else 0,
            message.edited_at.isoformat() if message.edited_at else None,
            message.original_content,
            json.dumps(message.metadata),
            str(message.id),
        ))
        
        return message
    
    async def delete_message(self, message_id: UUID) -> bool:
        """Delete a message."""
        # Get message first to update conversation stats
        message = await self.get_message_by_id(message_id)
        if not message:
            return False
        
        query = "DELETE FROM messages WHERE id = ?"
        cursor = db_connection.execute(query, (str(message_id),))
        
        if cursor.rowcount > 0:
            # Update conversation stats
            update_query = """
                UPDATE conversations SET
                    message_count = message_count - 1,
                    total_tokens = total_tokens - ?,
                    updated_at = ?
                WHERE id = ?
            """
            db_connection.execute(update_query, (
                message.token_count,
                datetime.utcnow().isoformat(),
                str(message.conversation_id),
            ))
            
            return True
        
        return False
    
    async def get_total_tokens_used(self, user_id: UUID) -> int:
        """Get total tokens used by user."""
        query = """
            SELECT SUM(total_tokens) as total 
            FROM conversations 
            WHERE user_id = ?
        """
        row = db_connection.fetch_one(query, (str(user_id),))
        return row["total"] if row and row["total"] else 0
    
    async def get_tokens_used_today(self, user_id: UUID) -> int:
        """Get tokens used today."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        query = """
            SELECT SUM(m.token_count) as total
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ? AND DATE(m.created_at) = ?
        """
        row = db_connection.fetch_one(query, (str(user_id), today))
        return row["total"] if row and row["total"] else 0
    
    async def archive_old_conversations(
        self,
        user_id: UUID,
        days_old: int = 30,
    ) -> int:
        """Archive old conversations."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        query = """
            UPDATE conversations 
            SET status = 'archived', updated_at = ?
            WHERE user_id = ? AND status = 'active' AND updated_at < ?
        """
        cursor = db_connection.execute(query, (
            datetime.utcnow().isoformat(),
            str(user_id),
            cutoff_date.isoformat(),
        ))
        
        count = cursor.rowcount if cursor else 0
        logger.info(f"Archived {count} old conversations for user {user_id}")
        return count
    
    async def delete_archived_conversations(
        self,
        user_id: UUID,
        days_old: int = 90,
    ) -> int:
        """Permanently delete archived conversations."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Get conversations to delete
        select_query = """
            SELECT id FROM conversations 
            WHERE user_id = ? AND status = 'archived' AND updated_at < ?
        """
        rows = db_connection.fetch_all(select_query, (str(user_id), cutoff_date.isoformat()))
        
        deleted_count = 0
        for row in rows:
            if await self.delete(UUID(row["id"])):
                deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} archived conversations for user {user_id}")
        return deleted_count
    
    async def get_conversation_stats(self, user_id: UUID) -> dict:
        """Get conversation statistics for user."""
        stats = {
            "total_conversations": 0,
            "active_conversations": 0,
            "archived_conversations": 0,
            "total_messages": 0,
            "total_tokens": 0,
            "average_messages_per_conversation": 0,
            "most_used_model": None,
        }
        
        # Count by status
        query = """
            SELECT status, COUNT(*) as count, SUM(total_tokens) as tokens, SUM(message_count) as messages
            FROM conversations 
            WHERE user_id = ?
            GROUP BY status
        """
        rows = db_connection.fetch_all(query, (str(user_id),))
        
        for row in rows:
            status = row["status"]
            stats[f"{status}_conversations"] = row["count"]
            stats["total_conversations"] += row["count"]
            stats["total_tokens"] += row["tokens"] or 0
            stats["total_messages"] += row["messages"] or 0
        
        # Average messages
        if stats["total_conversations"] > 0:
            stats["average_messages_per_conversation"] = stats["total_messages"] / stats["total_conversations"]
        
        # Most used model
        model_query = """
            SELECT model_name, COUNT(*) as count
            FROM conversations 
            WHERE user_id = ?
            GROUP BY model_name
            ORDER BY count DESC
            LIMIT 1
        """
        model_row = db_connection.fetch_one(model_query, (str(user_id),))
        if model_row:
            stats["most_used_model"] = model_row["model_name"]
        
        return stats
    
    async def get_by_tag(
        self,
        user_id: UUID,
        tag: str,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get conversations by tag."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND tags LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), f'%"{tag}"%', limit))
        return [self._row_to_entity(row) for row in rows]
    
    async def get_by_category(
        self,
        user_id: UUID,
        category: str,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get conversations by category."""
        query = """
            SELECT * FROM conversations 
            WHERE user_id = ? AND category = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """
        rows = db_connection.fetch_all(query, (str(user_id), category, limit))
        return [self._row_to_entity(row) for row in rows]
    
    def _row_to_entity(self, row: dict) -> Conversation:
        """Convert database row to Conversation entity."""
        return Conversation(
            id=UUID(row["id"]),
            user_id=UUID(row["user_id"]),
            title=row["title"],
            model_name=row["model_name"],
            status=ConversationStatus(row["status"]),
            system_prompt=row.get("system_prompt"),
            model_parameters=json.loads(row["model_parameters"]) if row.get("model_parameters") else {},
            tags=json.loads(row["tags"]) if row.get("tags") else [],
            is_pinned=bool(row["is_pinned"]),
            is_favorite=bool(row["is_favorite"]),
            total_tokens=row["total_tokens"],
            message_count=row["message_count"],
            summary=row.get("summary"),
            category=row.get("category"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )
    
    def _row_to_message(self, row: dict) -> Message:
        """Convert database row to Message entity."""
        return Message(
            id=UUID(row["id"]),
            conversation_id=UUID(row["conversation_id"]),
            role=MessageRole(row["role"]),
            content=row["content"],
            sequence_number=row["sequence_number"],
            token_count=row["token_count"],
            model_used=row.get("model_used"),
            generation_time_ms=row.get("generation_time_ms"),
            finish_reason=row.get("finish_reason"),
            is_edited=bool(row["is_edited"]),
            edited_at=datetime.fromisoformat(row["edited_at"]) if row.get("edited_at") else None,
            original_content=row.get("original_content"),
            metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )