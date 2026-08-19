"""
Command for deleting a conversation.
"""
from dataclasses import dataclass
from uuid import UUID

from src.application.commands.base_command import BaseCommand


@dataclass
class DeleteConversationCommand(BaseCommand):
    """
    Command to delete (or soft delete) a conversation.
    """
    
    conversation_id: UUID
    user_id: UUID
    
    # Deletion options
    permanent: bool = False  # If True, hard delete; otherwise soft delete
    delete_assets: bool = False  # Also delete associated assets
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        return len(errors) == 0, errors