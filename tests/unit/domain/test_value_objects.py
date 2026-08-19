"""
Unit tests for value objects.
"""
import pytest
from datetime import datetime, timedelta

from src.domain.value_objects.email import Email
from src.domain.value_objects.model_parameters import ModelParameters
from src.domain.value_objects.time_range import TimeRange
from src.domain.value_objects.api_key import ApiKey, ApiKeyScope
from src.domain.exceptions import DomainValidationError
from src.shared.enums import DateRangePreset


class TestEmailValueObject:
    """Test cases for Email value object."""
    
    def test_create_valid_email(self):
        """Test creating a valid email."""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
        assert str(email) == "test@example.com"
    
    def test_create_invalid_email_no_at(self):
        """Test creating email without @ fails."""
        with pytest.raises(DomainValidationError, match="Invalid email format"):
            Email("testexample.com")
    
    def test_create_invalid_email_no_domain(self):
        """Test creating email without domain fails."""
        with pytest.raises(DomainValidationError, match="Invalid email format"):
            Email("test@")
    
    def test_create_empty_email(self):
        """Test creating empty email fails."""
        with pytest.raises(DomainValidationError, match="Email cannot be empty"):
            Email("")
    
    def test_email_local_part(self):
        """Test extracting local part."""
        email = Email("user@example.com")
        assert email.local_part == "user"
    
    def test_email_domain(self):
        """Test extracting domain."""
        email = Email("user@example.com")
        assert email.domain == "example.com"
    
    def test_email_masked(self):
        """Test masking email for privacy."""
        email = Email("john.doe@example.com")
        masked = email.masked
        assert "@example.com" in masked
        assert "john.doe" not in masked
    
    def test_email_masked_short(self):
        """Test masking short email."""
        email = Email("a@example.com")
        masked = email.masked
        assert masked.startswith("a*")
    
    def test_is_disposable(self):
        """Test detecting disposable email."""
        email = Email("test@mailinator.com")
        assert email.is_disposable is True
        
        email2 = Email("test@gmail.com")
        assert email2.is_disposable is False
    
    def test_is_common_domain(self):
        """Test detecting common email domains."""
        email = Email("test@gmail.com")
        assert email.is_common_domain is True
        
        email2 = Email("test@custom-domain.org")
        assert email2.is_common_domain is False
    
    def test_equals_case_insensitive(self):
        """Test case-insensitive equality."""
        email1 = Email("Test@Example.com")
        email2 = Email("test@example.com")
        
        assert email1.equals(email2) is True


class TestModelParametersValueObject:
    """Test cases for ModelParameters value object."""
    
    def test_create_default_parameters(self):
        """Test creating default parameters."""
        params = ModelParameters()
        
        assert params.temperature == 0.7
        assert params.top_p == 0.9
        assert params.max_tokens == 2048
    
    def test_create_custom_parameters(self):
        """Test creating custom parameters."""
        params = ModelParameters(
            temperature=0.5,
            top_p=0.8,
            max_tokens=1024,
            seed=42,
        )
        
        assert params.temperature == 0.5
        assert params.top_p == 0.8
        assert params.max_tokens == 1024
        assert params.seed == 42
    
    def test_invalid_temperature(self):
        """Test invalid temperature fails."""
        with pytest.raises(DomainValidationError):
            ModelParameters(temperature=2.5)
        
        with pytest.raises(DomainValidationError):
            ModelParameters(temperature=-0.1)
    
    def test_invalid_top_p(self):
        """Test invalid top_p fails."""
        with pytest.raises(DomainValidationError):
            ModelParameters(top_p=1.5)
        
        with pytest.raises(DomainValidationError):
            ModelParameters(top_p=-0.1)
    
    def test_invalid_max_tokens(self):
        """Test invalid max_tokens fails."""
        with pytest.raises(DomainValidationError):
            ModelParameters(max_tokens=0)
        
        with pytest.raises(DomainValidationError):
            ModelParameters(max_tokens=50000)
    
    def test_creative_factory(self):
        """Test creative parameters factory."""
        params = ModelParameters.creative()
        assert params.temperature == 0.9
        assert params.top_p == 0.95
    
    def test_precise_factory(self):
        """Test precise parameters factory."""
        params = ModelParameters.precise()
        assert params.temperature == 0.1
        assert params.top_p == 0.1
    
    def test_balanced_factory(self):
        """Test balanced parameters factory."""
        params = ModelParameters.balanced()
        assert params.temperature == 0.7
        assert params.top_p == 0.9
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        params = ModelParameters(temperature=0.8, top_p=0.9, max_tokens=1000)
        data = params.to_dict()
        
        assert data["temperature"] == 0.8
        assert data["top_p"] == 0.9
        assert data["max_tokens"] == 1000
    
    def test_with_temperature(self):
        """Test creating copy with new temperature."""
        params = ModelParameters(temperature=0.5)
        new_params = params.with_temperature(0.8)
        
        assert new_params.temperature == 0.8
        assert new_params.top_p == params.top_p
        assert new_params.max_tokens == params.max_tokens


class TestTimeRangeValueObject:
    """Test cases for TimeRange value object."""
    
    def test_create_valid_time_range(self):
        """Test creating valid time range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        
        tr = TimeRange(start_date=start, end_date=end)
        
        assert tr.start_date == start
        assert tr.end_date == end
    
    def test_create_invalid_time_range(self):
        """Test creating range where start > end fails."""
        start = datetime(2024, 1, 31)
        end = datetime(2024, 1, 1)
        
        with pytest.raises(DomainValidationError, match="Start date must be before end date"):
            TimeRange(start_date=start, end_date=end)
    
    def test_max_range_exceeded(self):
        """Test exceeding maximum range fails."""
        start = datetime(2020, 1, 1)
        end = datetime(2026, 1, 1)
        
        with pytest.raises(DomainValidationError, match="cannot exceed 5 years"):
            TimeRange(start_date=start, end_date=end)
    
    def test_from_preset_today(self):
        """Test creating from TODAY preset."""
        tr = TimeRange.from_preset(DateRangePreset.TODAY)
        
        assert tr.preset == DateRangePreset.TODAY
        assert tr.start_date.date() == datetime.utcnow().date()
    
    def test_from_preset_last_7_days(self):
        """Test creating from LAST_7_DAYS preset."""
        tr = TimeRange.from_preset(DateRangePreset.LAST_7_DAYS)
        
        assert tr.preset == DateRangePreset.LAST_7_DAYS
        assert tr.duration_days == 7
    
    def test_duration_properties(self):
        """Test duration properties."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 2, 0, 0, 0)
        
        tr = TimeRange(start_date=start, end_date=end)
        
        assert tr.duration_days == 1.0
        assert tr.duration_hours == 24.0
        assert tr.duration_minutes == 1440.0
    
    def test_is_single_day(self):
        """Test checking if range is within single day."""
        start = datetime(2024, 1, 1, 10, 0)
        end = datetime(2024, 1, 1, 18, 0)
        
        tr = TimeRange(start_date=start, end_date=end)
        assert tr.is_single_day is True
        
        start2 = datetime(2024, 1, 1)
        end2 = datetime(2024, 1, 2)
        tr2 = TimeRange(start_date=start2, end_date=end2)
        assert tr2.is_single_day is False
    
    def test_contains(self):
        """Test checking if date is within range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        tr = TimeRange(start_date=start, end_date=end)
        
        assert tr.contains(datetime(2024, 1, 15)) is True
        assert tr.contains(datetime(2023, 12, 31)) is False
        assert tr.contains(datetime(2024, 2, 1)) is False
    
    def test_overlaps(self):
        """Test checking if ranges overlap."""
        tr1 = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 15),
        )
        tr2 = TimeRange(
            start_date=datetime(2024, 1, 10),
            end_date=datetime(2024, 1, 31),
        )
        tr3 = TimeRange(
            start_date=datetime(2024, 2, 1),
            end_date=datetime(2024, 2, 15),
        )
        
        assert tr1.overlaps(tr2) is True
        assert tr1.overlaps(tr3) is False