"""
Base service class providing common functionality for all services.

This class implements common patterns and reduces code duplication across services,
following DRY and SOLID principles.
"""

import logging
import os
import sys
from abc import ABC
from typing import Any, Dict, Optional

from ..core.config import Settings
from ..core.exceptions import APIException

# Note: Shared portfolio logic is imported via relative imports
# This eliminates the need for sys.path manipulation


class BaseService(ABC):
    """
    Base service class providing common functionality.

    This class follows the Single Responsibility Principle by handling
    only common service concerns like logging, error handling, and configuration.
    """

    def __init__(self, settings: Settings, service_name: str):
        """
        Initialize base service.

        Args:
            settings: Application settings
            service_name: Name of the service for logging
        """
        self.settings = settings
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

        self.logger.info(f"{service_name} service initialized")

    def _handle_service_error(
        self, operation: str, error: Exception, exception_class: type = APIException
    ) -> None:
        """
        Handle service errors with consistent logging and exception raising.

        Args:
            operation: Description of the operation that failed
            error: The original exception
            exception_class: Exception class to raise

        Raises:
            exception_class: The specified exception with formatted message
        """
        error_message = f"Failed to {operation}: {str(error)}"
        self.logger.error(f"Error in {self.service_name}: {error_message}")
        raise exception_class(error_message)

    def _log_operation_start(self, operation: str, **kwargs) -> None:
        """Log the start of an operation with parameters."""
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        params_str = f" with {params}" if params else ""
        self.logger.info(f"{operation}{params_str}")

    def _log_operation_success(self, operation: str, result_info: str = "") -> None:
        """Log successful completion of an operation."""
        info_str = f" - {result_info}" if result_info else ""
        self.logger.debug(f"{operation} completed successfully{info_str}")

    def _validate_required_param(self, param_name: str, param_value: Any) -> None:
        """
        Validate that a required parameter is provided and not empty.

        Args:
            param_name: Name of the parameter
            param_value: Value to validate

        Raises:
            ValueError: If parameter is None or empty
        """
        if param_value is None:
            raise ValueError(f"{param_name} is required")

        if isinstance(param_value, str) and not param_value.strip():
            raise ValueError(f"{param_name} cannot be empty")

    def _safe_decimal_conversion(self, value: Any, field_name: str) -> Any:
        """
        Safely convert values for Decimal fields with error handling.

        Args:
            value: Value to convert
            field_name: Name of the field for error messages

        Returns:
            Converted value or original if conversion not needed
        """
        if value is None:
            return value

        try:
            # Convert to string first to handle various numeric types
            return str(value)
        except Exception as e:
            self.logger.warning(f"Could not convert {field_name} value {value}: {e}")
            return "0"

    def _create_cache_key(self, *args, **kwargs) -> str:
        """
        Create a cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Cache key
        """
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{self.service_name}:{':'.join(key_parts)}"
