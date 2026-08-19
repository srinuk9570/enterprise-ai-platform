"""
Validation utilities for user input and data.
"""
import re
import json
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path


# Email validation pattern
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# URL validation pattern
URL_PATTERN = re.compile(
    r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$"
)

# Username validation pattern
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")

# Common weak passwords
COMMON_PASSWORDS = {
    "password", "12345678", "qwerty123", "admin123", "letmein",
    "welcome", "monkey", "dragon", "master", "hello",
    "freedom", "whatever", "qazwsx", "trustno1", "password1",
    "123456789", "abc123", "password123", "admin", "user",
}


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    if len(email) > 255:
        return False, "Email must be at most 255 characters"
    
    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"
    
    # Check for disposable domains
    disposable_domains = {
        "tempmail.com", "throwawaymail.com", "mailinator.com",
        "guerrillamail.com", "10minutemail.com", "yopmail.com",
    }
    
    domain = email.split("@")[1].lower()
    if domain in disposable_domains:
        return False, "Disposable email addresses are not allowed"
    
    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
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


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    
    if not password:
        issues.append("Password is required")
        return False, issues
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        issues.append("Password must be at most 128 characters long")
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password):
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
    
    # Length
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


def get_password_strength_label(password: str) -> str:
    """
    Get password strength label.
    
    Args:
        password: Password to evaluate
    
    Returns:
        Strength label
    """
    score = get_password_strength_score(password)
    
    if score < 30:
        return "Very Weak"
    elif score < 50:
        return "Weak"
    elif score < 70:
        return "Fair"
    elif score < 85:
        return "Strong"
    else:
        return "Very Strong"


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    if not URL_PATTERN.match(url):
        return False, "Invalid URL format"
    
    return True, None


def validate_json(data: str) -> Tuple[bool, Optional[Any], Optional[str]]:
    """
    Validate JSON string.
    
    Args:
        data: JSON string to validate
    
    Returns:
        (is_valid, parsed_data, error_message)
    """
    if not data:
        return False, None, "JSON data is required"
    
    try:
        parsed = json.loads(data)
        return True, parsed, None
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing dangerous characters.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    sanitized = "".join(c for c in text if ord(c) >= 32 or c in "\n\r\t")
    
    # Remove HTML tags
    sanitized = re.sub(r"<[^>]*>", "", sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_file_size(
    file_size: int,
    max_size_mb: int = 50,
) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
    
    Returns:
        (is_valid, error_message)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size <= 0:
        return False, "File is empty"
    
    if file_size > max_size_bytes:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    return True, None


def validate_file_type(
    filename: str,
    allowed_extensions: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Validate file type by extension.
    
    Args:
        filename: File name to check
        allowed_extensions: List of allowed extensions (e.g., ['.csv', '.json'])
    
    Returns:
        (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is required"
    
    ext = Path(filename).suffix.lower()
    
    if ext not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        return False, f"File type '{ext}' not allowed. Allowed: {allowed}"
    
    return True, None


def validate_prompt(prompt: str, max_length: int = 4000) -> Tuple[bool, Optional[str]]:
    """
    Validate AI prompt.
    
    Args:
        prompt: Prompt text
        max_length: Maximum length
    
    Returns:
        (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
    
    if len(prompt) > max_length:
        return False, f"Prompt exceeds maximum length of {max_length} characters"
    
    # Check for prohibited content (basic)
    prohibited = ["nsfw", "explicit", "violence", "gore", "hate speech"]
    prompt_lower = prompt.lower()
    
    for term in prohibited:
        if term in prompt_lower:
            return False, f"Prompt contains prohibited term: {term}"
    
    return True, None