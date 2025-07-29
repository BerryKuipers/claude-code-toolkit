"""
Portfolio-specific exceptions.

Centralized exception handling for all portfolio operations.
"""


class PortfolioException(Exception):
    """Base exception for all portfolio-related errors."""
    pass


class BitvavoAPIException(PortfolioException):
    """Exception raised when Bitvavo API operations fail."""
    pass


class InvalidAPIKeyError(BitvavoAPIException):
    """Exception raised when API credentials are invalid."""
    pass


class RateLimitExceededError(BitvavoAPIException):
    """Exception raised when API rate limits are exceeded."""
    pass


class AssetNotFoundException(PortfolioException):
    """Exception raised when a requested asset is not found."""
    pass


class CalculationError(PortfolioException):
    """Exception raised when portfolio calculations fail."""
    pass


class DataValidationError(PortfolioException):
    """Exception raised when input data validation fails."""
    pass
