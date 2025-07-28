"""
External API clients with strong typing.

This module provides strongly typed clients for external APIs
with proper error handling and rate limiting.
"""

from .bitvavo_client import BitvavoClient

__all__ = [
    "BitvavoClient",
]
