"""Utility functions for portfolio operations."""

from typing import Any


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, handling strings and other types.

    Args:
        value: Value to convert to float
        default: Default value if conversion fails

    Returns:
        Float value or default if conversion fails
    """
    if value is None:
        return default

    try:
        # Handle string values that might have currency symbols or formatting
        if isinstance(value, str):
            # Remove common currency symbols, percentage signs, and whitespace
            cleaned_value = (
                value.replace("€", "")
                .replace("$", "")
                .replace("%", "")
                .replace(",", "")
                .strip()
            )
            if cleaned_value == "" or cleaned_value == "-":
                return default
            return float(cleaned_value)

        # Handle numeric types
        return float(value)
    except (ValueError, TypeError):
        return default
