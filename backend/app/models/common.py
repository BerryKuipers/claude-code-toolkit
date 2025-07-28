"""
Common Pydantic models and types used across the API.

These provide shared data structures and validation patterns
similar to C# base classes and common types.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


# For now, use simple string type for AssetSymbol to avoid JSON schema issues
# TODO: Implement proper validation with Pydantic v2 patterns
AssetSymbol = str


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(True, description="Whether the request was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    model_config = {
        "json_encoders": {
            Decimal: str,  # Serialize Decimals as strings for precision
            datetime: lambda v: v.isoformat(),
        }
    }


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(False, description="Always false for error responses")
    error_code: str = Field(..., description="Error code for programmatic handling")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class HealthCheckResponse(BaseResponse):
    """Health check response."""

    status: str = Field("healthy", description="Service health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(..., description="Dependency health status")
