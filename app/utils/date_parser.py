"""Date parsing utilities for natural language date handling."""
from datetime import datetime, timedelta
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_natural_date(date_string: str) -> Optional[datetime]:
    """Parse natural language date strings.

    Supports:
    - Relative dates: "tomorrow", "next week", "in 3 days"
    - Day names: "Monday", "Friday"
    - Specific dates: "January 15", "15/01/2025", "29th jan", "jan 29th"
    - Ordinal dates: "1st", "2nd", "3rd", "29th"
    """
    if not date_string:
        return None

    date_string = date_string.lower().strip()
    now = datetime.utcnow()
    current_year = now.year

    # Handle relative dates
    if date_string == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_string == "tomorrow":
        return (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif date_string == "yesterday":
        return (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Handle "next week", "this week", etc.
    if date_string.startswith("next "):
        period = date_string.replace("next ", "")
        if period == "week":
            return (now + timedelta(weeks=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif period == "month":
            return (now + timedelta(days=30)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

    if date_string.startswith("this "):
        period = date_string.replace("this ", "")
        if period == "week":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Handle "in X days"
    match = re.match(r"in (\d+) days?", date_string)
    if match:
        days = int(match.group(1))
        return (now + timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Handle day names (Monday, Friday, etc.)
    days_of_week = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for day_name, day_num in days_of_week.items():
        if day_name in date_string:
            current_day = now.weekday()
            days_ahead = day_num - current_day
            if days_ahead <= 0:
                days_ahead += 7
            return (now + timedelta(days=days_ahead)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

    # Month name mappings (short and full)
    month_map = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    # Handle ordinal dates like "29th jan", "jan 29th", "january 29"
    # Pattern: (day with optional ordinal) (month name)
    ordinal_pattern = r"(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(month_map.keys()) + r")(?:\s+(\d{4}))?"
    match = re.search(ordinal_pattern, date_string)
    if match:
        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3)) if match.group(3) else current_year
        month = month_map[month_name]
        
        try:
            parsed_date = datetime(year, month, day)
            # If date is in the past and no year specified, assume next year
            if not match.group(3) and parsed_date < now:
                parsed_date = datetime(year + 1, month, day)
            logger.debug(f"Parsed ordinal date '{date_string}' as {parsed_date}")
            return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError as e:
            logger.warning(f"Invalid date parsed from '{date_string}': {e}")
    
    # Pattern: (month name) (day with optional ordinal)
    reverse_pattern = r"(" + "|".join(month_map.keys()) + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?"
    match = re.search(reverse_pattern, date_string)
    if match:
        month_name = match.group(1)
        day = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else current_year
        month = month_map[month_name]
        
        try:
            parsed_date = datetime(year, month, day)
            # If date is in the past and no year specified, assume next year
            if not match.group(3) and parsed_date < now:
                parsed_date = datetime(year + 1, month, day)
            logger.debug(f"Parsed date '{date_string}' as {parsed_date}")
            return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError as e:
            logger.warning(f"Invalid date parsed from '{date_string}': {e}")

    # Try to parse explicit dates
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%B %d",
        "%d %B",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    return None


def parse_time_from_string(time_string: str) -> Optional[Tuple[int, int]]:
    """Extract time (hour, minute) from string.
    
    Supports:
    - 12-hour format: "2pm", "3:30pm", "2:30 PM", "at 2pm"
    - 24-hour format: "14:00", "15:30"
    - Flexible spacing: "2 pm", "3: 30 pm"

    Returns:
        Tuple of (hour, minute) or None if no time found.
    """
    if not time_string:
        return None
        
    time_string = time_string.lower().strip()
    
    # Remove common prefixes
    time_string = time_string.replace("at ", "").replace("on ", "")
    
    # Match various time patterns
    # Pattern 1: HH:MM AM/PM or HH AM/PM
    match = re.search(
        r"(\d{1,2})\s*:?\s*(\d{2})?\s*(am|pm)?",
        time_string,
    )
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        am_pm = match.group(3)

        # Convert 12-hour to 24-hour format
        if am_pm:
            if am_pm == "pm" and hour != 12:
                hour += 12
            elif am_pm == "am" and hour == 12:
                hour = 0
        
        # Validate time
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            logger.debug(f"Parsed time '{time_string}' as {hour:02d}:{minute:02d}")
            return (hour, minute)

    return None


def combine_date_and_time(
    date_obj: Optional[datetime],
    time_string: str = "",
) -> Optional[datetime]:
    """Combine date with time from string."""
    if not date_obj:
        return None

    if not time_string:
        return date_obj

    time_parts = parse_time_from_string(time_string)
    if time_parts:
        hour, minute = time_parts
        return date_obj.replace(hour=hour, minute=minute)

    return date_obj


def is_overdue(due_date: datetime) -> bool:
    """Check if a task is overdue."""
    if not due_date:
        return False
    return due_date < datetime.utcnow()


def get_date_range_for_filter(filter_type: str) -> Tuple[Optional[datetime],
                                                          Optional[datetime]]:
    """Get date range for common filter types.

    Returns:
        Tuple of (start_date, end_date).
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    if filter_type == "today":
        return (today_start, today_end)
    elif filter_type == "this_week":
        week_start = today_start - timedelta(days=today_start.weekday())
        week_end = week_start + timedelta(days=7)
        return (week_start, week_end)
    elif filter_type == "this_month":
        month_start = today_start.replace(day=1)
        if today_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        return (month_start, month_end)
    elif filter_type == "overdue":
        return (None, now)

    return (None, None)
