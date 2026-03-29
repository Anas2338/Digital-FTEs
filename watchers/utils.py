"""Utility functions for the Digital FTE watcher system."""

import re
from datetime import datetime


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    Sanitize text for use in filenames.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the sanitized filename (default: 50)

    Returns:
        Sanitized filename string (lowercase, safe characters only)

    Examples:
        >>> sanitize_filename("Hello World!")
        'hello-world'
        >>> sanitize_filename("Test@Email#Subject$")
        'test-email-subject'
    """
    # Convert to lowercase
    text = text.lower()

    # Remove unsafe characters (keep alphanumeric, spaces, hyphens, underscores)
    text = re.sub(r'[^a-z0-9\s\-_]', '', text)

    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)

    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Strip leading/trailing hyphens
    text = text.strip('-')

    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')

    return text


def format_timestamp_filename() -> str:
    """
    Generate a timestamp string for use in filenames.

    Returns:
        Timestamp string in format YYYYMMDD-HHMMSS

    Examples:
        >>> format_timestamp_filename()
        '20260329-143022'
    """
    return datetime.now().strftime('%Y%m%d-%H%M%S')


def format_iso8601(dt: datetime = None) -> str:
    """
    Format a datetime object as ISO 8601 string.

    Args:
        dt: Datetime object to format (default: current time)

    Returns:
        ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SSZ)

    Examples:
        >>> format_iso8601(datetime(2026, 3, 29, 14, 30, 22))
        '2026-03-29T14:30:22Z'
    """
    if dt is None:
        dt = datetime.now()

    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
