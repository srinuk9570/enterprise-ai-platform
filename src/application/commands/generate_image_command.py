"""
Command for generating an AI image.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from uuid import UUID

from src.application.commands.base_command import BaseCommand


@dataclass
class GenerateImageCommand(BaseCommand):
    """
    Command to generate an image using AI.
    """
    
    user_id: UUID
    prompt: str
    
    # Optional parameters
    negative_prompt: Optional[str] = None
    model_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    conversation_id: Optional[UUID] = None
    
    # Image specifications
    width: int = 1024
    height: int = 1024
    num_images: int = 1
    seed: Optional[int] = None
    
    # Processing options
    enhance_prompt: bool = True
    return_immediately: bool = False  # For async processing
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.prompt or len(self.prompt.strip()) == 0:
            errors.append("Prompt cannot be empty")
        
        if len(self.prompt) > 4000:
            errors.append("Prompt exceeds maximum length of 4000 characters")
        
        if self.negative_prompt and len(self.negative_prompt) > 1000:
            errors.append("Negative prompt exceeds maximum length of 1000 characters")
        
        if self.width < 256 or self.width > 2048:
            errors.append("Width must be between 256 and 2048")
        
        if self.height < 256 or self.height > 2048:
            errors.append("Height must be between 256 and 2048")
        
        if self.num_images < 1 or self.num_images > 10:
            errors.append("Number of images must be between 1 and 10")
        
        return len(errors) == 0, errors
    
    def get_safe_prompt(self) -> str:
        """Get prompt safe for logging (truncated)."""
        if len(self.prompt) <= 100:
            return self.prompt
        return self.prompt[:97] + "..."