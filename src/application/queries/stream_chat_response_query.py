"""
Query for streaming chat responses.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class StreamChatResponseQuery:
    """
    Query to stream AI response tokens in real-time.
    """
    
    conversation_id: UUID
    user_id: UUID
    message: str
    model_name: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    include_context: bool = True
    max_context_messages: int = 20
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.message or len(self.message.strip()) == 0:
            errors.append("Message cannot be empty")
        
        return len(errors) == 0, errors