"""
Message entity within a conversation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from src.shared.constants import MessageRole
from src.domain.exceptions import DomainValidationError


@dataclass
class Message:
    """
    Message entity within a conversation.
    """
    
    conversation_id: UUID
    role: MessageRole
    content: str
    sequence_number: int
    
    # Optional fields
    token_count: int = 0
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata for AI responses
    model_used: Optional[str] = None
    generation_time_ms: Optional[float] = None
    finish_reason: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    original_content: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate message content."""
        self._validate_content()
        self._validate_sequence_number()
    
    def _validate_content(self) -> None:
        """Validate message content according to business rules."""
        if not self.content or len(self.content.strip()) == 0:
            raise DomainValidationError("Message content cannot be empty")
        
        max_lengths = {
            MessageRole.USER: 10000,
            MessageRole.ASSISTANT: 50000,
            MessageRole.SYSTEM: 2000,
        }
        
        max_length = max_lengths.get(self.role, 10000)
        if len(self.content) > max_length:
            raise DomainValidationError(
                f"Message content exceeds maximum length of {max_length} characters"
            )
        
        # Trim whitespace
        self.content = self.content.strip()
    
    def _validate_sequence_number(self) -> None:
        """Validate sequence number."""
        if self.sequence_number < 0:
            raise DomainValidationError("Sequence number cannot be negative")
    
    def estimate_tokens(self) -> int:
        """
        Rough estimate of token count.
        Approximately 4 characters per token for English text.
        """
        self.token_count = len(self.content) // 4
        return self.token_count
    
    def edit_content(self, new_content: str) -> None:
        """
        Edit message content.
        Only allowed for user messages.
        """
        if self.role != MessageRole.USER:
            raise DomainValidationError("Only user messages can be edited")
        
        if not new_content or len(new_content.strip()) == 0:
            raise DomainValidationError("Message content cannot be empty")
        
        if len(new_content) > 10000:
            raise DomainValidationError("Message content exceeds maximum length")
        
        # Store original for history
        if not self.is_edited:
            self.original_content = self.content
            self.is_edited = True
        
        self.content = new_content.strip()
        self.edited_at = datetime.utcnow()
        self.estimate_tokens()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to message."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    @property
    def is_from_user(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER
    
    @property
    def is_from_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT
    
    @property
    def is_system(self) -> bool:
        """Check if message is system message."""
        return self.role == MessageRole.SYSTEM
    
    @property
    def word_count(self) -> int:
        """Get word count of message."""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """Get character count of message."""
        return len(self.content)
    
    @property
    def reading_time_seconds(self) -> float:
        """Estimate reading time in seconds (avg 200 wpm)."""
        return self.word_count / 3.33
    
    @property
    def display_content(self) -> str:
        """Get display content (truncated if too long)."""
        if len(self.content) <= 500:
            return self.content
        return self.content[:497] + "..."
    
    def to_dict(self, include_metadata: bool = True) -> dict:
        """Convert message to dictionary."""
        data = {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role.value,
            "content": self.content,
            "sequence_number": self.sequence_number,
            "token_count": self.token_count,
            "model_used": self.model_used,
            "generation_time_ms": self.generation_time_ms,
            "finish_reason": self.finish_reason,
            "is_edited": self.is_edited,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "word_count": self.word_count,
            "character_count": self.character_count,
        }
        
        if include_metadata and self.metadata:
            data["metadata"] = self.metadata
        
        return data
    
    def to_llm_format(self) -> dict:
        """Convert to format expected by LLM APIs."""
        return {
            "role": self.role.value,
            "content": self.content,
        }