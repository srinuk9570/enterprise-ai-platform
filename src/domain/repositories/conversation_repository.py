"""
Abstract conversation repository interface.
"""
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.repositories.base_repository import BaseRepository
from src.shared.constants import ConversationStatus


class IConversationRepository(BaseRepository[Conversation]):
    """
    Abstract interface for conversation repository.
    """
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ConversationStatus] = None,
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        pass
    
    @abstractmethod
    async def get_active_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Conversation]:
        """Get user's active conversations."""
        pass
    
    @abstractmethod
    async def get_pinned_conversations(
        self,
        user_id: UUID,
    ) -> List[Conversation]:
        """Get user's pinned conversations."""
        pass
    
    @abstractmethod
    async def get_favorite_conversations(
        self,
        user_id: UUID,
    ) -> List[Conversation]:
        """Get user's favorite conversations."""
        pass
    
    @abstractmethod
    async def search_conversations(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10,
    ) -> List[Conversation]:
        """Search user's conversations by title or message content."""
        pass
    
    @abstractmethod
    async def get_recent_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[Conversation]:
        """Get user's most recent conversations."""
        pass
    
    @abstractmethod
    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """Get conversation with all messages loaded."""
        pass
    
    @abstractmethod
    async def add_message(
        self,
        conversation_id: UUID,
        message: Message,
    ) -> Message:
        """Add a message to a conversation."""
        pass
    
    @abstractmethod
    async def get_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """Get messages for a conversation."""
        pass
    
    @abstractmethod
    async def get_total_tokens_used(self, user_id: UUID) -> int:
        """Get total tokens used by user across all conversations."""
        pass
    
    @abstractmethod
    async def get_tokens_used_today(self, user_id: UUID) -> int:
        """Get tokens used by user today."""
        pass
    
    @abstractmethod
    async def archive_old_conversations(
        self,
        user_id: UUID,
        days_old: int = 30,
    ) -> int:
        """Archive conversations older than specified days."""
        pass
    
    @abstractmethod
    async def delete_archived_conversations(
        self,
        user_id: UUID,
        days_old: int = 90,
    ) -> int:
        """Permanently delete archived conversations older than days."""
        pass
    
    @abstractmethod
    async def get_conversation_stats(self, user_id: UUID) -> dict:
        """Get conversation statistics for user."""
        pass
    
    @abstractmethod
    async def get_by_tag(
        self,
        user_id: UUID,
        tag: str,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get conversations by tag."""
        pass
    
    @abstractmethod
    async def get_by_category(
        self,
        user_id: UUID,
        category: str,
        limit: int = 50,
    ) -> List[Conversation]:
        """Get conversations by category."""
        pass