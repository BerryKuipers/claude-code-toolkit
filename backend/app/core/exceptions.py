"""
Custom exception classes for the API.

Provides strongly typed exception hierarchy similar to C# exception handling
with clear error categorization and HTTP status code mapping.
"""

from typing import Any, Dict, Optional


class APIException(Exception):
    """
    Base API exception class.
    
    Similar to C# custom exception base class with additional context.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class PortfolioServiceException(APIException):
    """Portfolio service specific exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PORTFOLIO_SERVICE_ERROR",
            status_code=500,
            details=details
        )


class MarketServiceException(APIException):
    """Market service specific exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MARKET_SERVICE_ERROR",
            status_code=500,
            details=details
        )


class ChatServiceException(APIException):
    """Chat service specific exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CHAT_SERVICE_ERROR",
            status_code=500,
            details=details
        )


class AssetNotFoundException(APIException):
    """Asset not found exception."""
    
    def __init__(self, asset: str, details: Optional[Dict[str, Any]] = None):
        message = f"Asset '{asset}' not found in portfolio"
        super().__init__(
            message=message,
            error_code="ASSET_NOT_FOUND",
            status_code=404,
            details=details or {"asset": asset}
        )


class ConversationNotFoundException(APIException):
    """Conversation not found exception."""
    
    def __init__(self, conversation_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Conversation '{conversation_id}' not found"
        super().__init__(
            message=message,
            error_code="CONVERSATION_NOT_FOUND",
            status_code=404,
            details=details or {"conversation_id": conversation_id}
        )


class FunctionNotFoundException(APIException):
    """Function not found exception."""
    
    def __init__(self, function_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Function '{function_name}' not found"
        super().__init__(
            message=message,
            error_code="FUNCTION_NOT_FOUND",
            status_code=404,
            details=details or {"function_name": function_name}
        )


class InvalidRequestException(APIException):
    """Invalid request exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST",
            status_code=400,
            details=details
        )


class RateLimitExceededError(APIException):
    """Rate limit exceeded exception."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class BitvavoAPIException(APIException):
    """Bitvavo API specific exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BITVAVO_API_ERROR",
            status_code=502,
            details=details
        )


class InvalidAPIKeyError(APIException):
    """Invalid API key exception."""
    
    def __init__(self, message: str = "Invalid API key", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_API_KEY",
            status_code=401,
            details=details
        )
