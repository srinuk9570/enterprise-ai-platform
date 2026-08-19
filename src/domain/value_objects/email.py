"""
Email value object with validation.
"""
import re
from dataclasses import dataclass
from typing import Optional

from src.domain.exceptions import DomainValidationError


@dataclass(frozen=True)
class Email:
    """
    Email value object.
    Immutable and self-validating.
    """
    
    value: str
    
    # Email validation regex pattern (RFC 5322 compliant)
    _PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@'
        r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|"
        r"\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|"
        r"[a-zA-Z0-9-]*[a-zA-Z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|"
        r"\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$"
    )
    
    # Common disposable email domains
    _DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwawaymail.com", "mailinator.com",
        "guerrillamail.com", "10minutemail.com", "yopmail.com",
        "temp-mail.org", "fakeinbox.com", "trashmail.com",
    }
    
    def __post_init__(self) -> None:
        """Validate email format upon creation."""
        if not self.value:
            raise DomainValidationError("Email cannot be empty")
        
        if len(self.value) > 255:
            raise DomainValidationError("Email must be at most 255 characters")
        
        if not self._PATTERN.match(self.value):
            raise DomainValidationError(f"Invalid email format: {self.value}")
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def local_part(self) -> str:
        """Extract local part of email (before @)."""
        return self.value.split("@")[0]
    
    @property
    def domain(self) -> str:
        """Extract domain part of email (after @)."""
        return self.value.split("@")[1]
    
    @property
    def masked(self) -> str:
        """Return masked email for privacy."""
        local, domain = self.value.split("@")
        if len(local) <= 2:
            masked_local = local[0] + "*" * (len(local) - 1)
        elif len(local) <= 4:
            masked_local = local[:1] + "*" * (len(local) - 2) + local[-1]
        else:
            masked_local = local[:2] + "*" * (len(local) - 3) + local[-1]
        return f"{masked_local}@{domain}"
    
    @property
    def is_disposable(self) -> bool:
        """Check if email is from a disposable email provider."""
        return self.domain.lower() in self._DISPOSABLE_DOMAINS
    
    @property
    def is_common_domain(self) -> bool:
        """Check if email is from a common email provider."""
        common_domains = {
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "icloud.com", "protonmail.com", "aol.com", "mail.com",
        }
        return self.domain.lower() in common_domains
    
    def equals(self, other: 'Email') -> bool:
        """Case-insensitive comparison."""
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()
    
    @classmethod
    def try_create(cls, value: str) -> Optional['Email']:
        """Try to create an Email, return None if invalid."""
        try:
            return cls(value)
        except DomainValidationError:
            return None