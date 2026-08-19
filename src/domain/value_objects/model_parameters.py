"""
LLM model parameters value object with validation.
"""
from dataclasses import dataclass, field
from typing import Optional, List

from src.domain.exceptions import DomainValidationError
from src.shared.constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_FREQUENCY_PENALTY,
)


@dataclass(frozen=True)
class ModelParameters:
    """
    LLM model parameters.
    Immutable and self-validating.
    """
    
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = DEFAULT_TOP_P
    max_tokens: int = DEFAULT_MAX_TOKENS
    presence_penalty: float = DEFAULT_PRESENCE_PENALTY
    frequency_penalty: float = DEFAULT_FREQUENCY_PENALTY
    top_k: Optional[int] = None
    seed: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    repetition_penalty: float = 1.0
    stream: bool = False 
    
    def __post_init__(self) -> None:
        """Validate all parameters."""
        self._validate_temperature()
        self._validate_top_p()
        self._validate_max_tokens()
        self._validate_penalties()
        self._validate_top_k()
        self._validate_repetition_penalty()
        self._validate_stop_sequences()
    
    def _validate_temperature(self) -> None:
        """Temperature must be between 0 and 2."""
        if not 0 <= self.temperature <= 2:
            raise DomainValidationError(
                f"Temperature must be between 0 and 2, got {self.temperature}"
            )
    
    def _validate_top_p(self) -> None:
        """Top-p must be between 0 and 1."""
        if not 0 <= self.top_p <= 1:
            raise DomainValidationError(
                f"Top-p must be between 0 and 1, got {self.top_p}"
            )
    
    def _validate_max_tokens(self) -> None:
        """Max tokens must be positive and within reasonable limits."""
        if self.max_tokens < 1:
            raise DomainValidationError("Max tokens must be at least 1")
        if self.max_tokens > 32000:
            raise DomainValidationError("Max tokens cannot exceed 32000")
    
    def _validate_penalties(self) -> None:
        """Penalties must be between -2 and 2."""
        if not -2 <= self.presence_penalty <= 2:
            raise DomainValidationError("Presence penalty must be between -2 and 2")
        if not -2 <= self.frequency_penalty <= 2:
            raise DomainValidationError("Frequency penalty must be between -2 and 2")
    
    def _validate_top_k(self) -> None:
        """Top-k must be positive if specified."""
        if self.top_k is not None and self.top_k < 1:
            raise DomainValidationError("Top-k must be at least 1")
    
    def _validate_repetition_penalty(self) -> None:
        """Repetition penalty must be positive."""
        if self.repetition_penalty <= 0:
            raise DomainValidationError("Repetition penalty must be positive")
        if self.repetition_penalty > 2:
            raise DomainValidationError("Repetition penalty should not exceed 2")
    
    def _validate_stop_sequences(self) -> None:
        """Validate stop sequences."""
        if self.stop_sequences:
            if len(self.stop_sequences) > 4:
                raise DomainValidationError("Maximum 4 stop sequences allowed")
            for seq in self.stop_sequences:
                if len(seq) > 50:
                    raise DomainValidationError("Stop sequence must be at most 50 characters")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API consumption."""
        result = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "repetition_penalty": self.repetition_penalty,
        }
        if self.top_k is not None:
            result["top_k"] = self.top_k
        if self.seed is not None:
            result["seed"] = self.seed
        if self.stop_sequences:
            result["stop"] = self.stop_sequences
        return result
    
    @classmethod
    def creative(cls) -> "ModelParameters":
        """Factory method for creative responses."""
        return cls(
            temperature=0.9,
            top_p=0.95,
            presence_penalty=0.1,
            frequency_penalty=0.1,
        )
    
    @classmethod
    def precise(cls) -> "ModelParameters":
        """Factory method for precise/factual responses."""
        return cls(
            temperature=0.1,
            top_p=0.1,
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
    
    @classmethod
    def balanced(cls) -> "ModelParameters":
        """Factory method for balanced responses."""
        return cls(
            temperature=0.7,
            top_p=0.9,
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
    
    @classmethod
    def code_generation(cls) -> "ModelParameters":
        """Factory method for code generation."""
        return cls(
            temperature=0.2,
            top_p=0.95,
            repetition_penalty=1.05,
        )
    
    def with_temperature(self, temperature: float) -> "ModelParameters":
        """Create copy with new temperature."""
        return ModelParameters(
            temperature=temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            top_k=self.top_k,
            seed=self.seed,
            stop_sequences=self.stop_sequences,
            repetition_penalty=self.repetition_penalty,
        )
    
    def with_max_tokens(self, max_tokens: int) -> "ModelParameters":
        """Create copy with new max_tokens."""
        return ModelParameters(
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=max_tokens,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            top_k=self.top_k,
            seed=self.seed,
            stop_sequences=self.stop_sequences,
            repetition_penalty=self.repetition_penalty,
        )
