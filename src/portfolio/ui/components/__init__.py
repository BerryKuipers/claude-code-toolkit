"""UI Components package."""

from .sticky_header import get_current_tab
from .sticky_header import render as render_sticky_header

__all__ = ["render_sticky_header", "get_current_tab"]
