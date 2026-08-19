"""
Input validation utility functions.
"""
import re
import json
from typing import Tuple, List, Optional, Any
from uuid import UUID


# ==================== Email Validation ====================

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    """
    Check if email is valid.
    
    Args:
        email: Email address
    
    Returns:
        True if valid
    """
    if not email or len(email) > 255:
        return False
    
    return bool(EMAIL_PATTERN.match(email))


# ==================== URL Validation ====================

URL_PATTERN = re.compile(
    r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$"
)


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL string
    
    Returns:
        True if valid
    """
    if not url:
        return False
    
    return bool(URL_PATTERN.match(url))


# ==================== UUID Validation ====================

def is_valid_uuid(value: str) -> bool:
    """
    Check if string is a valid UUID.
    
    Args:
        value: String to check
    
    Returns:
        True if valid UUID
    """
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


# ==================== Username Validation ====================

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")


def is_valid_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters"
    
    if not USERNAME_PATTERN.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    if username[0] in "-_" or username[-1] in "-_":
        return False, "Username cannot start or end with hyphen or underscore"
    
    if "--" in username or "__" in username:
        return False, "Username cannot contain consecutive hyphens or underscores"
    
    return True, None


# ==================== JSON Validation ====================

def is_valid_json(json_str: str) -> bool:
    """
    Check if string is valid JSON.
    
    Args:
        json_str: JSON string
    
    Returns:
        True if valid JSON
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


# ==================== Password Validation ====================

COMMON_PASSWORDS = {
    "password", "12345678", "qwerty123", "admin123", "letmein",
    "welcome", "monkey", "dragon", "master", "hello",
    "freedom", "whatever", "qazwsx", "trustno1", "password1",
    "123456789", "abc123", "password123", "admin", "user",
}


def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum length
        require_upper: Require uppercase
        require_lower: Require lowercase
        require_digit: Require digit
        require_special: Require special character
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    if not password:
        issues.append("Password is required")
        return False, issues
    
    if len(password) < min_length:
        issues.append(f"Password must be at least {min_length} characters long")
    
    if len(password) > 128:
        issues.append("Password must be at most 128 characters long")
    
    if require_upper and not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if require_lower and not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if require_digit and not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    
    if require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
        issues.append("Password must contain at least one special character")
    
    if password.lower() in COMMON_PASSWORDS:
        issues.append("Password is too common")
    
    # Check for sequential characters
    if _has_sequential_chars(password):
        issues.append("Password contains sequential characters")
    
    # Check for repeated characters
    if _has_repeated_chars(password):
        issues.append("Password contains too many repeated characters")
    
    return len(issues) == 0, issues


def _has_sequential_chars(password: str) -> bool:
    """Check for sequential characters."""
    password_lower = password.lower()
    
    for i in range(len(password_lower) - 2):
        c1, c2, c3 = password_lower[i], password_lower[i+1], password_lower[i+2]
        
        if ord(c1) + 1 == ord(c2) and ord(c2) + 1 == ord(c3):
            return True
        
        if c1.isdigit() and c2.isdigit() and c3.isdigit():
            if int(c1) + 1 == int(c2) and int(c2) + 1 == int(c3):
                return True
    
    return False


def _has_repeated_chars(password: str) -> bool:
    """Check for too many repeated characters."""
    from collections import Counter
    counts = Counter(password.lower())
    max_count = max(counts.values())
    return max_count > len(password) * 0.4


def get_password_strength_score(password: str) -> int:
    """
    Get password strength score (0-100).
    
    Args:
        password: Password to score
    
    Returns:
        Score from 0 to 100
    """
    if not password:
        return 0
    
    score = 0
    
    # Length contribution
    score += min(len(password) * 2, 30)
    
    # Character variety
    if any(c.isupper() for c in password):
        score += 10
    if any(c.islower() for c in password):
        score += 10
    if any(c.isdigit() for c in password):
        score += 10
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/" for c in password):
        score += 10
    
    # Penalties
    if password.lower() in COMMON_PASSWORDS:
        score -= 30
    if _has_sequential_chars(password):
        score -= 15
    if _has_repeated_chars(password):
        score -= 15
    
    return max(0, min(100, score))


# ==================== HTML Sanitization ====================

def sanitize_html(html: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML by removing dangerous tags and attributes.
    
    Args:
        html: HTML string to sanitize
        allowed_tags: List of allowed HTML tags
    
    Returns:
        Sanitized HTML
    """
    if allowed_tags is None:
        allowed_tags = ["p", "br", "b", "i", "u", "strong", "em", "a", "ul", "ol", "li", "code", "pre"]
    
    # Simple tag stripping for now
    # For production, use a proper library like bleach
    
    # Remove script tags completely
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove style tags
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* event handlers
    html = re.sub(r"\son\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    html = re.sub(r"href\s*=\s*[\"']javascript:[^\"']*[\"']", 'href="#"', html, flags=re.IGNORECASE)
    
    return html


# ==================== Input Sanitization ====================

def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input.
    
    Args:
        text: Input text
        max_length: Maximum length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    sanitized = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


# ==================== Number Validation ====================

def is_in_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> bool:
    """
    Check if value is within range.
    
    Args:
        value: Value to check
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
    
    Returns:
        True if in range
    """
    return min_val <= value <= max_val


def is_positive(value: Union[int, float]) -> bool:
    """Check if value is positive."""
    return value > 0


def is_non_negative(value: Union[int, float]) -> bool:
    """Check if value is non-negative."""
    return value >= 0


def is_integer(value: Any) -> bool:
    """Check if value can be parsed as integer."""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_float(value: Any) -> bool:
    """Check if value can be parsed as float."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False