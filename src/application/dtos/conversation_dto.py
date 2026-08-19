"""
Conversation Data Transfer Object.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.domain.entities.conversation import Conversation
from src.application.dtos.message_dto import MessageDTO


@dataclass
class ConversationDTO:
    """
    DTO for conversation data sent to clients.
    """
    
    id: str
    user_id: str
    title: str
    model_name: str
    status: str
    created_at: str
    updated_at: str
    
    # Optional fields
    system_prompt: Optional[str] = None
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_pinned: bool = False
    is_favorite: bool = False
    summary: Optional[str] = None
    category: Optional[str] = None
    
    # Statistics
    total_tokens: int = 0
    message_count: int = 0
    message_count_display: str = ""
    token_count_display: str = ""
    
    # Related data
    messages: List[MessageDTO] = field(default_factory=list)
    last_message: Optional[Dict[str, Any]] = None
    last_activity: Optional[str] = None
    
    @classmethod
    def from_entity(
        cls,
        conversation: Conversation,
        include_messages: bool = False,
    ) -> "ConversationDTO":
        """
        Create DTO from domain entity.
        """
        dto = cls(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            model_name=conversation.model_name,
            status=conversation.status.value,
            created_at=conversation.created_at.isoformat() if conversation.created_at else "",
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
            system_prompt=conversation.system_prompt,
            model_parameters=conversation.model_parameters,
            tags=conversation.tags,
            is_pinned=conversation.is_pinned,
            is_favorite=conversation.is_favorite,
            summary=conversation.summary,
            category=conversation.category,
            total_tokens=conversation.total_tokens,
            message_count=conversation.message_count,
            message_count_display=conversation.message_count_display,
            token_count_display=conversation.token_count_display,
            last_activity=conversation.last_activity.isoformat() if conversation.last_activity else None,
        )
        
        if conversation.last_message:
            dto.last_message = {
                "role": conversation.last_message.role.value,
                "content": conversation.last_message.display_content,
                "created_at": conversation.last_message.created_at.isoformat() if conversation.last_message.created_at else None,
            }
        
        if include_messages and conversation.messages:
            dto.messages = [MessageDTO.from_entity(m) for m in conversation.messages]
        
        return dto
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "model_name": self.model_name,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "system_prompt": self.system_prompt,
            "model_parameters": self.model_parameters,
            "tags": self.tags,
            "is_pinned": self.is_pinned,
            "is_favorite": self.is_favorite,
            "summary": self.summary,
            "category": self.category,
            "total_tokens": self.total_tokens,
            "message_count": self.message_count,
            "message_count_display": self.message_count_display,
            "token_count_display": self.token_count_display,
            "last_message": self.last_message,
            "last_activity": self.last_activity,
            "messages": [m.to_dict() for m in self.messages] if self.messages else [],
        }