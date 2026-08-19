"""
Command for archiving a conversation.
"""
from dataclasses import dataclass
from uuid import UUID

from src.application.commands.base_command import BaseCommand


@dataclass
class ArchiveConversationCommand(BaseCommand):
    """
    Command to archive or unarchive a conversation.
    """
    
    conversation_id: UUID
    user_id: UUID
    archive: bool = True  # True to archive, False to unarchive
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        return len(errors) == 0, errors