"""
LLM Response Data Transfer Object.
"""
from dataclasses import dataclass, field
from typing import Dict, Any

from src.domain.services.llm_orchestration_service import LLMResponse


@dataclass
class LLMResponseDTO:
    """
    DTO for LLM response sent to clients.
    """
    
    content: str
    model_used: str
    tokens_used: int
    generation_time_ms: float
    finish_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional computed fields
    word_count: int = 0
    is_truncated: bool = False
    streaming: bool = False
    
    @classmethod
    def from_entity(cls, response: LLMResponse) -> "LLMResponseDTO":
        """
        Create DTO from domain entity.
        """
        return cls(
            content=response.content,
            model_used=response.model_used,
            tokens_used=response.tokens_used,
            generation_time_ms=response.generation_time_ms,
            finish_reason=response.finish_reason,
            metadata=response.metadata,
            word_count=response.word_count,
            is_truncated=response.is_truncated,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "generation_time_ms": self.generation_time_ms,
            "finish_reason": self.finish_reason,
            "word_count": self.word_count,
            "is_truncated": self.is_truncated,
            "streaming": self.streaming,
            "metadata": self.metadata,
        }