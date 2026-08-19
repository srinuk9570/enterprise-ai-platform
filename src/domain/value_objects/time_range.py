"""
Time range value object for filtering data by time periods.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.domain.exceptions import DomainValidationError
from src.shared.enums import DateRangePreset


@dataclass(frozen=True)
class TimeRange:
    """
    Time range value object.
    Represents a period between start and end dates.
    """
    
    start_date: datetime
    end_date: datetime
    preset: Optional[DateRangePreset] = None
    
    def __post_init__(self) -> None:
        """Validate time range."""
        if self.start_date >= self.end_date:
            raise DomainValidationError("Start date must be before end date")
        
        # Max range of 5 years
        max_range = timedelta(days=365 * 5)
        if self.end_date - self.start_date > max_range:
            raise DomainValidationError("Time range cannot exceed 5 years")
    
    @classmethod
    def from_preset(cls, preset: DateRangePreset) -> "TimeRange":
        """Create time range from preset."""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        presets = {
            DateRangePreset.TODAY: (today, now),
            DateRangePreset.YESTERDAY: (
                today - timedelta(days=1),
                today - timedelta(microseconds=1),
            ),
            DateRangePreset.LAST_7_DAYS: (
                today - timedelta(days=7),
                now,
            ),
            DateRangePreset.LAST_30_DAYS: (
                today - timedelta(days=30),
                now,
            ),
            DateRangePreset.THIS_MONTH: (
                today.replace(day=1),
                now,
            ),
            DateRangePreset.LAST_MONTH: (
                (today.replace(day=1) - timedelta(days=1)).replace(day=1),
                today.replace(day=1) - timedelta(microseconds=1),
            ),
        }
        
        start, end = presets[preset]
        return cls(start_date=start, end_date=end, preset=preset)
    
    @classmethod
    def custom(cls, start_date: datetime, end_date: datetime) -> "TimeRange":
        """Create custom time range."""
        return cls(
            start_date=start_date,
            end_date=end_date,
            preset=DateRangePreset.CUSTOM,
        )
    
    @property
    def duration_days(self) -> float:
        """Get duration in days."""
        delta = self.end_date - self.start_date
        return delta.total_seconds() / (24 * 3600)
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration_days * 24
    
    @property
    def duration_minutes(self) -> float:
        """Get duration in minutes."""
        return self.duration_hours * 60
    
    @property
    def is_single_day(self) -> bool:
        """Check if range is within a single day."""
        return self.start_date.date() == self.end_date.date()
    
    @property
    def is_current_month(self) -> bool:
        """Check if range is within current month."""
        now = datetime.utcnow()
        return (
            self.start_date.year == now.year
            and self.start_date.month == now.month
            and self.end_date.year == now.year
            and self.end_date.month == now.month
        )
    
    def contains(self, date: datetime) -> bool:
        """Check if date is within range."""
        return self.start_date <= date <= self.end_date
    
    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another."""
        return (
            self.start_date <= other.end_date
            and self.end_date >= other.start_date
        )
    
    def get_interval_points(self, num_points: int = 10) -> list[datetime]:
        """Get evenly spaced points within the range."""
        if num_points < 2:
            raise DomainValidationError("Number of points must be at least 2")
        
        delta = (self.end_date - self.start_date) / (num_points - 1)
        return [self.start_date + i * delta for i in range(num_points)]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "preset": self.preset.value if self.preset else None,
            "duration_days": self.duration_days,
            "is_single_day": self.is_single_day,
        }
    
    def __str__(self) -> str:
        if self.preset and self.preset != DateRangePreset.CUSTOM:
            return self.preset.value.replace("_", " ").title()
        return f"{self.start_date.date()} to {self.end_date.date()}"