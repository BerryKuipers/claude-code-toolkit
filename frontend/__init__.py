"""
Frontend module for the crypto portfolio dashboard.

This module provides strongly typed API clients and utilities for the
Streamlit frontend to communicate with the FastAPI backend.
"""

from .api_client import CryptoPortfolioAPIClient

__all__ = [
    "CryptoPortfolioAPIClient",
]
