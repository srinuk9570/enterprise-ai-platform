"""
Handler for conversation-related queries.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from src.application.queries import (
    GetConversationHistoryQuery,
    SearchConversationsQuery,
)
from src.application.dtos import ConversationDTO, MessageDTO
from src.domain.exceptions import EntityNotFoundError, UnauthorizedOperationError

logger = logging.getLogger(__name__)


class ConversationQueryHandler:
    """
    Handler for conversation-related queries.
    """
    
    def __init__(
        self,
        conversation_repository,
        message_repository,
        user_repository,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.user_repository = user_repository
    
    async def handle_get_conversation_history(
        self,
        query: GetConversationHistoryQuery,
    ) -> tuple[Optional[ConversationDTO], list[str]]:
        """
        Handle GetConversationHistoryQuery.
        Returns (conversation_dto, errors).
        """
        # Validate query
        is_valid, errors = query.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Get conversation
            conversation = await self.conversation_repository.get_by_id(query.conversation_id)
            if not conversation:
                raise EntityNotFoundError("Conversation", str(query.conversation_id))
            
            # Check permissions
            if conversation.user_id != query.user_id:
                user = await self.user_repository.get_by_id(query.user_id)
                if not user or user.role != "admin":
                    raise UnauthorizedOperationError("You don't have access to this conversation")
            
            # Check status
            if not query.include_archived and conversation.status.value == "archived":
                return None, ["Conversation is archived"]
            
            # Get messages if requested
            if query.include_messages:
                messages = await self.message_repository.get_messages(
                    conversation_id=query.conversation_id,
                    skip=query.skip,
                    limit=query.message_limit or query.limit,
                )
                conversation.messages = messages
            
            # Filter messages if search term provided
            if query.search_term and conversation.messages:
                search_lower = query.search_term.lower()
                conversation.messages = [
                    m for m in conversation.messages
                    if search_lower in m.content.lower()
                ]
            
            return ConversationDTO.from_entity(conversation, include_messages=query.include_messages), []
            
        except EntityNotFoundError as e:
            return None, [str(e)]
        except UnauthorizedOperationError as e:
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return None, ["Internal server error"]
    
    async def handle_search_conversations(
        self,
        query: SearchConversationsQuery,
    ) -> tuple[List[ConversationDTO], int, list[str]]:
        """
        Handle SearchConversationsQuery.
        Returns (conversation_dtos, total_count, errors).
        """
        # Validate query
        is_valid, errors = query.validate()
        if not is_valid:
            return [], 0, errors
        
        try:
            # Search conversations
            conversations = await self.conversation_repository.search_conversations(
                user_id=query.user_id,
                query=query.get_sanitized_query(),
                limit=query.limit,
            )
            
            # Apply additional filters
            filtered = []
            for conv in conversations:
                # Status filter
                if query.status and conv.status.value != query.status:
                    continue
                
                # Tags filter
                if query.tags:
                    if not any(tag in conv.tags for tag in query.tags):
                        continue
                
                # Category filter
                if query.category and conv.category != query.category:
                    continue
                
                # Model filter
                if query.model_name and conv.model_name != query.model_name:
                    continue
                
                filtered.append(conv)
            
            # Convert to DTOs
            dtos = [ConversationDTO.from_entity(conv) for conv in filtered]
            
            return dtos, len(dtos), []
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return [], 0, ["Internal server error"]
    
    async def get_user_conversations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> tuple[List[ConversationDTO], int, list[str]]:
        """
        Get user's conversations with pagination.
        """
        try:
            from src.shared.constants import ConversationStatus
            
            status_enum = ConversationStatus(status) if status else None
            
            conversations = await self.conversation_repository.get_by_user_id(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status=status_enum,
            )
            
            total = await self.conversation_repository.count()
            
            dtos = [ConversationDTO.from_entity(conv) for conv in conversations]
            
            return dtos, total, []
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return [], 0, ["Internal server error"]
    
    async def get_recent_conversations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> tuple[List[ConversationDTO], list[str]]:
        """
        Get user's recent conversations.
        """
        try:
            conversations = await self.conversation_repository.get_recent_conversations(
                user_id=user_id,
                limit=limit,
            )
            
            dtos = [ConversationDTO.from_entity(conv) for conv in conversations]
            
            return dtos, []
            
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return [], ["Internal server error"]