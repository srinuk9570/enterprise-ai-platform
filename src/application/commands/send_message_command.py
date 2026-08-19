"""
Command for sending a message in a conversation.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

from src.application.commands.base_command import BaseCommand


@dataclass
class SendMessageCommand(BaseCommand):
    """
    Command to send a message to the AI assistant.
    """
    
    conversation_id: UUID
    content: str
    user_id: UUID
    model_name: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    stream_response: bool = True
    use_rag: bool = True
    attachments: Optional[list[str]] = None
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        
        if not self.content or len(self.content.strip()) == 0:
            errors.append("Message content cannot be empty")
        
        if len(self.content) > 10000:
            errors.append("Message content exceeds maximum length of 10000 characters")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        return len(errors) == 0, errors
    
    def get_trimmed_content(self, max_length: int = 500) -> str:
        """Get trimmed content for logging."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."