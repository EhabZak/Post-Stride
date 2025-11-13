"""
Timezone utilities for handling conversions between UTC and user timezones.

Golden Rules:
1. Store ALL datetimes in DB as naive UTC (no tzinfo)
2. Remember each user's timezone (IANA name)
3. Interpret naive timestamps using user's timezone, then convert to UTC
4. Return both UTC (for backend/RQ) and user-local time (for UI)
"""

from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
import pytz


def to_utc_naive(dt: datetime) -> datetime:
    """
    Convert any datetime to naive UTC (no tzinfo).
    
    - If dt has tzinfo, convert to UTC then strip tzinfo
    - If dt is naive, assume it's already UTC
    
    This is what we store in the database.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_iso_to_utc(iso_string: str, user_tz: Optional[str] = None) -> datetime:
    """
    Parse ISO 8601 datetime string to naive UTC.
    
    Args:
        iso_string: ISO format datetime (e.g., "2025-10-04T21:10:00Z" or "2025-10-04T21:10:00")
        user_tz: IANA timezone name (e.g., "America/New_York"). 
                 If provided and iso_string is naive, interpret as user's local time.
    
    Returns:
        Naive UTC datetime for database storage
    
    Examples:
        parse_iso_to_utc("2025-10-04T21:10:00Z") -> naive UTC
        parse_iso_to_utc("2025-10-04T21:10:00", "America/New_York") -> interprets as NY time, returns UTC
    """
    if not iso_string:
        return None
    
    # Handle 'Z' suffix (UTC marker)
    s = iso_string.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {iso_string}") from e
    
    # If datetime has timezone info, convert to UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    # If naive and user_tz provided, interpret as user's local time
    if user_tz:
        try:
            user_timezone = pytz.timezone(user_tz)
            # Localize naive datetime to user's timezone, then convert to UTC
            dt_localized = user_timezone.localize(dt)
            return dt_localized.astimezone(timezone.utc).replace(tzinfo=None)
        except pytz.exceptions.UnknownTimeZoneError:
            # If invalid timezone, treat as UTC
            pass
    
    # Naive datetime without user_tz: assume UTC
    return dt


def utc_to_user_tz(utc_dt: datetime, user_tz: str) -> datetime:
    """
    Convert naive UTC datetime to user's timezone (as aware datetime).
    
    Args:
        utc_dt: Naive UTC datetime from database
        user_tz: IANA timezone name (e.g., "Europe/Amsterdam")
    
    Returns:
        Timezone-aware datetime in user's timezone
    """
    if utc_dt is None:
        return None
    
    try:
        # Make UTC datetime aware
        utc_aware = pytz.utc.localize(utc_dt)
        # Convert to user's timezone
        user_timezone = pytz.timezone(user_tz)
        return utc_aware.astimezone(user_timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback: return as UTC if timezone is invalid
        return pytz.utc.localize(utc_dt)


def format_dual_time(utc_dt: datetime, user_tz: str) -> Dict[str, str]:
    """
    Format datetime as both UTC and user's local time for API responses.
    
    Args:
        utc_dt: Naive UTC datetime from database
        user_tz: IANA timezone name
    
    Returns:
        Dictionary with 'utc' and 'local' ISO strings:
        {
            "utc": "2025-10-04T21:10:00Z",
            "local": "2025-10-04T17:10:00-04:00",
            "timezone": "America/New_York"
        }
    """
    if utc_dt is None:
        return None
    
    # UTC format with 'Z' suffix
    utc_iso = utc_dt.isoformat() + 'Z'
    
    # User's local time with offset
    local_dt = utc_to_user_tz(utc_dt, user_tz)
    local_iso = local_dt.isoformat()
    
    return {
        'utc': utc_iso,
        'local': local_iso,
        'timezone': user_tz
    }


def format_utc_with_z(utc_dt: Optional[datetime]) -> Optional[str]:
    """
    Format naive UTC datetime as ISO string with 'Z' suffix.
    
    Args:
        utc_dt: Naive UTC datetime from database
    
    Returns:
        ISO string with 'Z' (e.g., "2025-10-04T21:10:00Z") or None
    """
    if utc_dt is None:
        return None
    return utc_dt.isoformat() + 'Z'


def validate_timezone(tz_name: str) -> bool:
    """
    Check if a timezone name is valid IANA timezone.
    
    Args:
        tz_name: IANA timezone name to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        pytz.timezone(tz_name)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False


def get_common_timezones() -> list:
    """
    Get list of common IANA timezone names for UI dropdowns.
    
    Returns:
        List of common timezone strings
    """
    return pytz.common_timezones

