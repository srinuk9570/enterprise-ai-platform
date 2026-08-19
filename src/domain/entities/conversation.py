"""
Conversation aggregate root entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from src.shared.constants import ConversationStatus, MessageRole
from src.domain.exceptions import (
    DomainValidationError,
    InvalidStateTransitionError,
    BusinessRuleViolationError,
)
from src.domain.entities.message import Message


@dataclass
class Conversation:
    """
    Conversation aggregate root.
    Manages a collection of messages between user and AI.
    """
    
    user_id: UUID
    title: str
    model_name: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Collections
    messages: List[Message] = field(default_factory=list)
    
    # Database fields
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Configuration
    system_prompt: Optional[str] = None
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_pinned: bool = False
    is_favorite: bool = False
    
    # Metadata
    total_tokens: int = 0
    message_count: int = 0
    total_cost_estimate: float = 0.0
    
    # Optional fields
    summary: Optional[str] = None
    category: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        self._validate_title()
        self._validate_model_name()
        self._validate_tags()
    
    def _validate_title(self) -> None:
        """Validate conversation title."""
        if not self.title or len(self.title.strip()) == 0:
            raise DomainValidationError("Conversation title cannot be empty")
        if len(self.title) > 200:
            raise DomainValidationError("Conversation title must be at most 200 characters")
        self.title = self.title.strip()
    
    def _validate_model_name(self) -> None:
        """Validate model name."""
        if not self.model_name:
            raise DomainValidationError("Model name cannot be empty")
        if len(self.model_name) > 50:
            raise DomainValidationError("Model name must be at most 50 characters")
    
    def _validate_tags(self) -> None:
        """Validate conversation tags."""
        for tag in self.tags:
            if len(tag) > 30:
                raise DomainValidationError(f"Tag '{tag}' exceeds maximum length of 30 characters")
            if not tag.replace("-", "").replace("_", "").isalnum():
                raise DomainValidationError(
                    f"Tag '{tag}' can only contain letters, numbers, hyphens, and underscores"
                )
        
        # Remove duplicates while preserving order
        seen = set()
        self.tags = [x for x in self.tags if not (x in seen or seen.add(x))]
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        tokens: int = 0,
        model_used: Optional[str] = None,
        generation_time_ms: Optional[float] = None,
        finish_reason: Optional[str] = None,
    ) -> Message:
        """
        Add a new message to the conversation.
        """
        if self.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                f"Cannot add message to {self.status.value} conversation"
            )
        
        if not content or len(content.strip()) == 0:
            raise DomainValidationError("Message content cannot be empty")
        
        message = Message(
            conversation_id=self.id,
            role=role,
            content=content.strip(),
            token_count=tokens,
            sequence_number=self.message_count,
            model_used=model_used or self.model_name,
            generation_time_ms=generation_time_ms,
            finish_reason=finish_reason,
        )
        
        self.messages.append(message)
        self.message_count += 1
        self.total_tokens += tokens
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message if title is generic
        if self.message_count == 1 and role == MessageRole.USER:
            if self.title.startswith("New Conversation"):
                self.generate_title_from_content()
        
        return message
    
    def get_messages_for_llm(self, max_tokens: Optional[int] = None) -> List[dict]:
        """
        Get messages formatted for LLM API consumption.
        Implements sliding window for context management.
        """
        formatted = []
        
        # Add system prompt if exists
        if self.system_prompt:
            formatted.append({"role": "system", "content": self.system_prompt})
        
        # Add conversation messages
        for msg in self.messages:
            formatted.append({"role": msg.role.value, "content": msg.content})
        
        # Apply token limit if specified (sliding window from start)
        if max_tokens and len(formatted) > 0:
            total_tokens = sum(m.token_count for m in self.messages)
            
            if total_tokens > max_tokens:
                # Keep system prompt + most recent messages
                if self.system_prompt:
                    system_msg = formatted[0]
                    other_msgs = formatted[1:]
                else:
                    system_msg = None
                    other_msgs = formatted
                
                # Keep messages until we hit token limit
                kept_messages = []
                current_tokens = 0
                
                for msg in reversed(other_msgs):
                    msg_tokens = len(msg["content"]) // 4  # Rough estimate
                    if current_tokens + msg_tokens <= max_tokens:
                        kept_messages.insert(0, msg)
                        current_tokens += msg_tokens
                    else:
                        break
                
                if system_msg:
                    return [system_msg] + kept_messages
                return kept_messages
        
        return formatted
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get the last n messages from the conversation."""
        return self.messages[-n:] if n > 0 else []
    
    def get_user_messages(self) -> List[Message]:
        """Get all user messages."""
        return [m for m in self.messages if m.role == MessageRole.USER]
    
    def get_assistant_messages(self) -> List[Message]:
        """Get all assistant messages."""
        return [m for m in self.messages if m.role == MessageRole.ASSISTANT]
    
    def archive(self) -> None:
        """Archive the conversation."""
        if self.status == ConversationStatus.ARCHIVED:
            raise InvalidStateTransitionError("Conversation is already archived")
        if self.status == ConversationStatus.DELETED:
            raise InvalidStateTransitionError("Cannot archive deleted conversation")
        
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def unarchive(self) -> None:
        """Unarchive the conversation."""
        if self.status != ConversationStatus.ARCHIVED:
            raise InvalidStateTransitionError("Only archived conversations can be unarchived")
        
        self.status = ConversationStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def delete(self) -> None:
        """Soft delete the conversation."""
        if self.status == ConversationStatus.DELETED:
            raise InvalidStateTransitionError("Conversation is already deleted")
        
        self.status = ConversationStatus.DELETED
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a deleted conversation."""
        if self.status != ConversationStatus.DELETED:
            raise InvalidStateTransitionError("Only deleted conversations can be restored")
        
        self.status = ConversationStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def update_title(self, new_title: str) -> None:
        """Update conversation title."""
        self.title = new_title
        self._validate_title()
        self.updated_at = datetime.utcnow()
    
    def set_system_prompt(self, prompt: str) -> None:
        """Set or update system prompt."""
        if prompt and len(prompt) > 2000:
            raise DomainValidationError("System prompt must be at most 2000 characters")
        self.system_prompt = prompt
        self.updated_at = datetime.utcnow()
    
    def generate_title_from_content(self) -> str:
        """
        Generate a title from first user message content.
        """
        first_user_message = next(
            (m for m in self.messages if m.role == MessageRole.USER),
            None
        )
        
        if first_user_message:
            content = first_user_message.content[:50]
            title = content + ("..." if len(first_user_message.content) > 50 else "")
            self.title = title
            self.updated_at = datetime.utcnow()
            return title
        
        return self.title
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the conversation."""
        if tag not in self.tags:
            self.tags.append(tag)
            self._validate_tags()
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the conversation."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def toggle_pin(self) -> None:
        """Toggle pin status."""
        self.is_pinned = not self.is_pinned
        self.updated_at = datetime.utcnow()
    
    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
        self.updated_at = datetime.utcnow()
    
    def set_category(self, category: str) -> None:
        """Set conversation category."""
        if len(category) > 50:
            raise DomainValidationError("Category must be at most 50 characters")
        self.category = category
        self.updated_at = datetime.utcnow()
    
    def update_model_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update model parameters."""
        valid_params = {
            "temperature": (0.0, 2.0),
            "top_p": (0.0, 1.0),
            "max_tokens": (1, 32000),
            "presence_penalty": (-2.0, 2.0),
            "frequency_penalty": (-2.0, 2.0),
        }
        
        for key, value in parameters.items():
            if key not in valid_params:
                raise DomainValidationError(f"Invalid parameter: {key}")
            
            min_val, max_val = valid_params[key]
            if not (min_val <= value <= max_val):
                raise DomainValidationError(
                    f"{key} must be between {min_val} and {max_val}, got {value}"
                )
        
        self.model_parameters.update(parameters)
        self.updated_at = datetime.utcnow()
    
    def clear_messages(self) -> None:
        """Clear all messages from conversation."""
        if self.status != ConversationStatus.ACTIVE:
            raise InvalidStateTransitionError(
                f"Cannot clear messages from {self.status.value} conversation"
            )
        
        self.messages.clear()
        self.message_count = 0
        self.total_tokens = 0
        self.updated_at = datetime.utcnow()
    
    def estimate_total_cost(self, cost_per_1k_tokens: float = 0.002) -> float:
        """Estimate total cost of conversation."""
        self.total_cost_estimate = (self.total_tokens / 1000) * cost_per_1k_tokens
        return self.total_cost_estimate
    
    @property
    def message_count_display(self) -> str:
        """Get formatted message count."""
        if self.message_count == 0:
            return "No messages"
        if self.message_count == 1:
            return "1 message"
        return f"{self.message_count} messages"
    
    @property
    def token_count_display(self) -> str:
        """Get formatted token count."""
        if self.total_tokens < 1000:
            return f"{self.total_tokens} tokens"
        return f"{self.total_tokens / 1000:.1f}k tokens"
    
    @property
    def last_message(self) -> Optional[Message]:
        """Get the last message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    @property
    def last_activity(self) -> datetime:
        """Get last activity timestamp."""
        if self.last_message:
            return self.last_message.created_at
        return self.updated_at
    
    def to_dict(self, include_messages: bool = False) -> dict:
        """Convert conversation to dictionary."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "model_name": self.model_name,
            "status": self.status.value,
            "system_prompt": self.system_prompt,
            "model_parameters": self.model_parameters,
            "tags": self.tags,
            "is_pinned": self.is_pinned,
            "is_favorite": self.is_favorite,
            "total_tokens": self.total_tokens,
            "message_count": self.message_count,
            "summary": self.summary,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }
        
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        
        return data