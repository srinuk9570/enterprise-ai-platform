"""
Date and time utility functions.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


def utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def format_iso(dt: Optional[datetime] = None) -> str:
    """
    Format datetime as ISO 8601 string.
    
    Args:
        dt: Datetime to format (default: now)
    
    Returns:
        ISO 8601 formatted string
    """
    if dt is None:
        dt = utc_now()
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat().replace("+00:00", "Z")


def parse_iso(iso_str: str) -> datetime:
    """
    Parse ISO 8601 string to datetime.
    
    Args:
        iso_str: ISO 8601 string
    
    Returns:
        Datetime object
    """
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1] + "+00:00"
    
    dt = datetime.fromisoformat(iso_str)
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt


def to_naive_utc(dt: datetime) -> datetime:
    """
    Convert datetime to naive UTC.
    
    Args:
        dt: Datetime to convert
    
    Returns:
        Naive UTC datetime
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to datetime.
    
    Args:
        dt: Base datetime
        days: Days to add (can be negative)
    
    Returns:
        New datetime
    """
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Add hours to datetime.
    
    Args:
        dt: Base datetime
        hours: Hours to add (can be negative)
    
    Returns:
        New datetime
    """
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    Add minutes to datetime.
    
    Args:
        dt: Base datetime
        minutes: Minutes to add (can be negative)
    
    Returns:
        New datetime
    """
    return dt + timedelta(minutes=minutes)


def add_seconds(dt: datetime, seconds: int) -> datetime:
    """
    Add seconds to datetime.
    
    Args:
        dt: Base datetime
        seconds: Seconds to add (can be negative)
    
    Returns:
        New datetime
    """
    return dt + timedelta(seconds=seconds)


def start_of_day(dt: datetime) -> datetime:
    """
    Get start of day (00:00:00).
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at start of day
    """
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """
    Get end of day (23:59:59.999999).
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at end of day
    """
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_week(dt: datetime) -> datetime:
    """
    Get start of week (Monday 00:00:00).
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at start of week
    """
    # Monday is 0, Sunday is 6
    days_since_monday = dt.weekday()
    start = dt - timedelta(days=days_since_monday)
    return start_of_day(start)


def end_of_week(dt: datetime) -> datetime:
    """
    Get end of week (Sunday 23:59:59).
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at end of week
    """
    # Monday is 0, Sunday is 6
    days_until_sunday = 6 - dt.weekday()
    end = dt + timedelta(days=days_until_sunday)
    return end_of_day(end)


def start_of_month(dt: datetime) -> datetime:
    """
    Get start of month.
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at start of month
    """
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(dt: datetime) -> datetime:
    """
    Get end of month.
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at end of month
    """
    # Get first day of next month, then subtract one microsecond
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)
    
    return next_month - timedelta(microseconds=1)


def start_of_year(dt: datetime) -> datetime:
    """
    Get start of year.
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at start of year
    """
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_year(dt: datetime) -> datetime:
    """
    Get end of year.
    
    Args:
        dt: Datetime
    
    Returns:
        Datetime at end of year
    """
    return dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)


def time_ago(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Get relative time string (e.g., "2 hours ago").
    
    Args:
        dt: Datetime to compare
        reference: Reference datetime (default: now)
    
    Returns:
        Relative time string
    """
    if reference is None:
        reference = utc_now()
    
    diff = reference - dt
    
    if diff.total_seconds() < 0:
        return "in the future"
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def is_expired(
    dt: datetime,
    ttl_seconds: int,
    reference: Optional[datetime] = None,
) -> bool:
    """
    Check if a datetime has expired based on TTL.
    
    Args:
        dt: Datetime to check
        ttl_seconds: Time-to-live in seconds
        reference: Reference datetime (default: now)
    
    Returns:
        True if expired
    """
    if reference is None:
        reference = utc_now()
    
    expiry = dt + timedelta(seconds=ttl_seconds)
    return reference > expiry


def is_today(dt: datetime) -> bool:
    """
    Check if datetime is today.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if today
    """
    now = utc_now()
    return dt.date() == now.date()


def is_yesterday(dt: datetime) -> bool:
    """
    Check if datetime is yesterday.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if yesterday
    """
    now = utc_now()
    yesterday = now - timedelta(days=1)
    return dt.date() == yesterday.date()


def is_tomorrow(dt: datetime) -> bool:
    """
    Check if datetime is tomorrow.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if tomorrow
    """
    now = utc_now()
    tomorrow = now + timedelta(days=1)
    return dt.date() == tomorrow.date()


def date_range(
    start: datetime,
    end: datetime,
    step: timedelta = timedelta(days=1),
) -> list[datetime]:
    """
    Generate a range of datetimes.
    
    Args:
        start: Start datetime
        end: End datetime
        step: Step size
    
    Returns:
        List of datetimes
    """
    result = []
    current = start
    
    while current <= end:
        result.append(current)
        current += step
    
    return result


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration (e.g., "2h 30m")
    """
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration string (e.g., "2h", "30m", "1h 30m")
    
    Returns:
        Duration in seconds
    """
    import re
    
    total_seconds = 0
    
    # Match patterns like "2h", "30m", "45s"
    patterns = {
        r"(\d+)\s*h": 3600,
        r"(\d+)\s*m": 60,
        r"(\d+)\s*s": 1,
        r"(\d+)\s*d": 86400,
    }
    
    for pattern, multiplier in patterns.items():
        match = re.search(pattern, duration_str, re.IGNORECASE)
        if match:
            total_seconds += int(match.group(1)) * multiplier
    
    return total_seconds