"""
API Key value objects.
"""
import secrets
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List

from src.domain.exceptions import DomainValidationError


class ApiKeyScope(str, Enum):
    """API key permission scopes."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    CHAT = "chat"
    IMAGE_GEN = "image_gen"
    CHART_GEN = "chart_gen"


@dataclass(frozen=True)
class ApiKey:
    """
    API Key value object.
    Represents a secure API key with scopes.
    """
    
    key_hash: str
    name: str
    scopes: List[ApiKeyScope]
    user_id: str
    prefix: str = field(default="")
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate API key."""
        self._validate_name()
        self._validate_scopes()
        self._validate_expiry()
    
    def _validate_name(self) -> None:
        """Validate key name."""
        if not self.name or len(self.name.strip()) == 0:
            raise DomainValidationError("API key name cannot be empty")
        if len(self.name) > 100:
            raise DomainValidationError("API key name must be at most 100 characters")
    
    def _validate_scopes(self) -> None:
        """Validate scopes."""
        if not self.scopes:
            raise DomainValidationError("API key must have at least one scope")
        
        # ADMIN scope implies all others
        if ApiKeyScope.ADMIN in self.scopes and len(self.scopes) > 1:
            # It's fine, just note that admin has all permissions
            pass
    
    def _validate_expiry(self) -> None:
        """Validate expiration date."""
        if self.expires_at and self.expires_at < datetime.utcnow():
            raise DomainValidationError("Expiration date cannot be in the past")
    
    @classmethod
    def generate(cls, user_id: str, name: str, scopes: List[ApiKeyScope]) -> tuple['ApiKey', str]:
        """
        Generate a new API key.
        Returns the ApiKey object and the raw key (to show to user once).
        """
        # Generate secure random key
        raw_key = f"eap_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:8]
        
        # Hash the key for storage
        key_hash = cls._hash_key(raw_key)
        
        api_key = cls(
            key_hash=key_hash,
            name=name,
            scopes=scopes,
            user_id=user_id,
            prefix=prefix,
        )
        
        return api_key, raw_key
    
    @staticmethod
    def _hash_key(key: str) -> str:
        """Hash a key using SHA-256."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @classmethod
    def verify(cls, raw_key: str, stored_hash: str) -> bool:
        """Verify a raw key against a stored hash."""
        return cls._hash_key(raw_key) == stored_hash
    
    def has_scope(self, scope: ApiKeyScope) -> bool:
        """Check if key has a specific scope."""
        if not self.is_active:
            return False
        
        if self.is_expired:
            return False
        
        if ApiKeyScope.ADMIN in self.scopes:
            return True
        
        return scope in self.scopes
    
    def has_any_scope(self, scopes: List[ApiKeyScope]) -> bool:
        """Check if key has any of the given scopes."""
        return any(self.has_scope(s) for s in scopes)
    
    def has_all_scopes(self, scopes: List[ApiKeyScope]) -> bool:
        """Check if key has all given scopes."""
        return all(self.has_scope(s) for s in scopes)
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)."""
        return self.is_active and not self.is_expired
    
    def record_usage(self) -> None:
        """Record key usage (requires mutable object, handled by repository)."""
        # This would be handled by the repository layer
        pass
    
    def mask_key(self) -> str:
        """Return masked key for display."""
        return f"{self.prefix}...{self.key_hash[-4:]}"
    
    def to_dict(self, include_hash: bool = False) -> dict:
        """Convert to dictionary."""
        data = {
            "name": self.name,
            "prefix": self.prefix,
            "scopes": [s.value for s in self.scopes],
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_hash:
            data["key_hash"] = self.key_hash
        return data