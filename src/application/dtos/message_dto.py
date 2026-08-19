"""
Message Data Transfer Object.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from src.domain.entities.message import Message


@dataclass
class MessageDTO:
    """
    DTO for message data sent to clients.
    """
    
    id: str
    conversation_id: str
    role: str
    content: str
    sequence_number: int
    token_count: int
    created_at: str
    
    # AI response metadata
    model_used: Optional[str] = None
    generation_time_ms: Optional[float] = None
    finish_reason: Optional[str] = None
    
    # Additional fields
    is_edited: bool = False
    edited_at: Optional[str] = None
    word_count: int = 0
    character_count: int = 0
    display_content: str = ""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_entity(cls, message: Message) -> "MessageDTO":
        """
        Create DTO from domain entity.
        """
        return cls(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            role=message.role.value,
            content=message.content,
            sequence_number=message.sequence_number,
            token_count=message.token_count,
            created_at=message.created_at.isoformat() if message.created_at else "",
            model_used=message.model_used,
            generation_time_ms=message.generation_time_ms,
            finish_reason=message.finish_reason,
            is_edited=message.is_edited,
            edited_at=message.edited_at.isoformat() if message.edited_at else None,
            word_count=message.word_count,
            character_count=message.character_count,
            display_content=message.display_content,
            metadata=message.metadata,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "display_content": self.display_content,
            "sequence_number": self.sequence_number,
            "token_count": self.token_count,
            "created_at": self.created_at,
            "model_used": self.model_used,
            "generation_time_ms": self.generation_time_ms,
            "finish_reason": self.finish_reason,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "metadata": self.metadata,
        }