"""
Comprehensive error handling tests.

Tests all custom exceptions, error handlers, and error response patterns
to ensure robust error handling throughout the application.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.core.exceptions import (
    APIException,
    PortfolioServiceException,
    MarketServiceException,
    ChatServiceException,
    AssetNotFoundException,
    ConversationNotFoundException,
    FunctionNotFoundException,
    InvalidRequestException,
    RateLimitExceededError,
    BitvavoAPIException,
    InvalidAPIKeyError,
)
from app.models.common import ErrorResponse


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_api_exception_base(self):
        """Test base APIException class."""
        exc = APIException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test error"

    def test_api_exception_defaults(self):
        """Test APIException with default values."""
        exc = APIException("Test error")
        
        assert exc.message == "Test error"
        assert exc.error_code == "API_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_portfolio_service_exception(self):
        """Test PortfolioServiceException."""
        exc = PortfolioServiceException("Portfolio error", {"asset": "BTC"})
        
        assert exc.message == "Portfolio error"
        assert exc.error_code == "PORTFOLIO_SERVICE_ERROR"
        assert exc.status_code == 500
        assert exc.details == {"asset": "BTC"}

    def test_market_service_exception(self):
        """Test MarketServiceException."""
        exc = MarketServiceException("Market error")
        
        assert exc.message == "Market error"
        assert exc.error_code == "MARKET_SERVICE_ERROR"
        assert exc.status_code == 500

    def test_chat_service_exception(self):
        """Test ChatServiceException."""
        exc = ChatServiceException("Chat error", {"model": "gpt-4"})
        
        assert exc.message == "Chat error"
        assert exc.error_code == "CHAT_SERVICE_ERROR"
        assert exc.status_code == 500
        assert exc.details == {"model": "gpt-4"}

    def test_asset_not_found_exception(self):
        """Test AssetNotFoundException."""
        exc = AssetNotFoundException("BTC")
        
        assert exc.message == "Asset 'BTC' not found in portfolio"
        assert exc.error_code == "ASSET_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details == {"asset": "BTC"}

    def test_conversation_not_found_exception(self):
        """Test ConversationNotFoundException."""
        exc = ConversationNotFoundException("conv-123")
        
        assert exc.message == "Conversation 'conv-123' not found"
        assert exc.error_code == "CONVERSATION_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details == {"conversation_id": "conv-123"}

    def test_function_not_found_exception(self):
        """Test FunctionNotFoundException."""
        exc = FunctionNotFoundException("get_portfolio")
        
        assert exc.message == "Function 'get_portfolio' not found"
        assert exc.error_code == "FUNCTION_NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details == {"function_name": "get_portfolio"}

    def test_invalid_request_exception(self):
        """Test InvalidRequestException."""
        exc = InvalidRequestException("Invalid data", {"field": "required"})
        
        assert exc.message == "Invalid data"
        assert exc.error_code == "INVALID_REQUEST"
        assert exc.status_code == 400
        assert exc.details == {"field": "required"}

    def test_rate_limit_exceeded_error(self):
        """Test RateLimitExceededError."""
        exc = RateLimitExceededError()
        
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_rate_limit_exceeded_error_custom(self):
        """Test RateLimitExceededError with custom message."""
        exc = RateLimitExceededError("Custom rate limit message", {"retry_after": 60})
        
        assert exc.message == "Custom rate limit message"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429
        assert exc.details == {"retry_after": 60}

    def test_bitvavo_api_exception(self):
        """Test BitvavoAPIException."""
        exc = BitvavoAPIException("API error", {"endpoint": "/ticker"})
        
        assert exc.message == "API error"
        assert exc.error_code == "BITVAVO_API_ERROR"
        assert exc.status_code == 502
        assert exc.details == {"endpoint": "/ticker"}

    def test_invalid_api_key_error(self):
        """Test InvalidAPIKeyError."""
        exc = InvalidAPIKeyError()
        
        assert exc.message == "Invalid API key"
        assert exc.error_code == "INVALID_API_KEY"
        assert exc.status_code == 401

    def test_invalid_api_key_error_custom(self):
        """Test InvalidAPIKeyError with custom message."""
        exc = InvalidAPIKeyError("Custom API key error", {"key_type": "bitvavo"})
        
        assert exc.message == "Custom API key error"
        assert exc.error_code == "INVALID_API_KEY"
        assert exc.status_code == 401
        assert exc.details == {"key_type": "bitvavo"}


class TestErrorResponseModel:
    """Test ErrorResponse model."""

    def test_error_response_creation(self):
        """Test ErrorResponse model creation."""
        error = ErrorResponse(
            error_code="TEST_ERROR",
            error_message="Test error message",
            details={"key": "value"}
        )
        
        assert error.success is False
        assert error.error_code == "TEST_ERROR"
        assert error.error_message == "Test error message"
        assert error.details == {"key": "value"}

    def test_error_response_without_details(self):
        """Test ErrorResponse model without details."""
        error = ErrorResponse(
            error_code="TEST_ERROR",
            error_message="Test error message"
        )
        
        assert error.success is False
        assert error.error_code == "TEST_ERROR"
        assert error.error_message == "Test error message"
        assert error.details is None


class TestGlobalExceptionHandlers:
    """Test global exception handlers."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_api_exception_handler(self, client):
        """Test APIException handler."""
        # Create a test endpoint that raises APIException
        @app.get("/test-api-exception")
        async def test_api_exception():
            raise APIException(
                message="Test API error",
                error_code="TEST_ERROR",
                status_code=400,
                details={"test": "data"}
            )
        
        response = client.get("/test-api-exception")
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "TEST_ERROR"
        assert data["error_message"] == "Test API error"
        assert data["details"] == {"test": "data"}

    def test_general_exception_handler(self, client):
        """Test general exception handler."""
        # Create a test endpoint that raises a general exception
        @app.get("/test-general-exception")
        async def test_general_exception():
            raise ValueError("Test general error")
        
        response = client.get("/test-general-exception")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert data["error_message"] == "An unexpected error occurred"
        assert data["details"]["exception_type"] == "ValueError"

    def test_404_not_found(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_422_validation_error(self, client):
        """Test 422 validation error handling."""
        # Test with invalid JSON data
        response = client.post("/api/v1/chat/query", json={"invalid": "data"})

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestServiceErrorHandling:
    """Test service-level error handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_portfolio_service_error_propagation(self, client):
        """Test portfolio service error propagation."""
        with patch('app.core.dependencies.get_portfolio_service') as mock_service:
            mock_service.return_value.get_portfolio_summary.side_effect = PortfolioServiceException(
                "Portfolio calculation failed", {"error": "division_by_zero"}
            )

            response = client.get("/api/v1/portfolio/summary")

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "PORTFOLIO_SERVICE_ERROR"
            assert "Portfolio calculation failed" in data["error_message"]

    def test_market_service_error_propagation(self, client):
        """Test market service error propagation."""
        with patch('app.core.dependencies.get_market_service') as mock_service:
            mock_service.return_value.get_current_prices.side_effect = MarketServiceException(
                "External API unavailable"
            )

            response = client.get("/api/v1/market/prices")

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "MARKET_SERVICE_ERROR"
            assert "External API unavailable" in data["error_message"]

    def test_chat_service_error_propagation(self, client):
        """Test chat service error propagation."""
        with patch('app.core.dependencies.get_chat_service') as mock_service:
            mock_service.return_value.process_chat_request.side_effect = ChatServiceException(
                "AI model unavailable", {"model": "gpt-4"}
            )

            response = client.post("/api/v1/chat/query", json={
                "message": "Test message",
                "model": "gpt-4"
            })

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "CHAT_SERVICE_ERROR"
            assert "AI model unavailable" in data["error_message"]
            assert data["details"]["model"] == "gpt-4"

    def test_asset_not_found_error_propagation(self, client):
        """Test asset not found error propagation."""
        with patch('app.core.dependencies.get_market_service') as mock_service:
            mock_service.return_value.get_asset_price.side_effect = AssetNotFoundException("INVALID")

            response = client.get("/api/v1/market/prices/INVALID")

            assert response.status_code == 404
            data = response.json()
            assert data["error_code"] == "ASSET_NOT_FOUND"
            assert "Asset 'INVALID' not found" in data["error_message"]
            assert data["details"]["asset"] == "INVALID"

    def test_conversation_not_found_error_propagation(self, client):
        """Test conversation not found error propagation."""
        with patch('app.core.dependencies.get_chat_service') as mock_service:
            mock_service.return_value.get_conversation_history.side_effect = ConversationNotFoundException("invalid-id")

            response = client.get("/api/v1/chat/conversations/invalid-id")

            assert response.status_code == 404
            data = response.json()
            assert data["error_code"] == "CONVERSATION_NOT_FOUND"
            assert "Conversation 'invalid-id' not found" in data["error_message"]
            assert data["details"]["conversation_id"] == "invalid-id"

    def test_function_not_found_error_propagation(self, client):
        """Test function not found error propagation."""
        with patch('app.core.dependencies.get_chat_service') as mock_service:
            mock_service.return_value.get_function_definition.side_effect = FunctionNotFoundException("invalid_func")

            response = client.get("/api/v1/chat/functions/invalid_func")

            assert response.status_code == 404
            data = response.json()
            assert data["error_code"] == "FUNCTION_NOT_FOUND"
            assert "Function 'invalid_func' not found" in data["error_message"]
            assert data["details"]["function_name"] == "invalid_func"

    def test_rate_limit_error_propagation(self, client):
        """Test rate limit error propagation."""
        with patch('app.core.dependencies.get_market_service') as mock_service:
            mock_service.return_value.refresh_market_data.side_effect = RateLimitExceededError(
                "API rate limit exceeded", {"retry_after": 60}
            )

            response = client.post("/api/v1/market/refresh")

            assert response.status_code == 429
            data = response.json()
            assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
            assert "API rate limit exceeded" in data["error_message"]
            assert data["details"]["retry_after"] == 60

    def test_bitvavo_api_error_propagation(self, client):
        """Test Bitvavo API error propagation."""
        with patch('app.core.dependencies.get_portfolio_service') as mock_service:
            mock_service.return_value.get_current_holdings.side_effect = BitvavoAPIException(
                "Bitvavo API error", {"endpoint": "/balance"}
            )

            response = client.get("/api/v1/portfolio/holdings")

            assert response.status_code == 502
            data = response.json()
            assert data["error_code"] == "BITVAVO_API_ERROR"
            assert "Bitvavo API error" in data["error_message"]
            assert data["details"]["endpoint"] == "/balance"

    def test_invalid_api_key_error_propagation(self, client):
        """Test invalid API key error propagation."""
        with patch('app.core.dependencies.get_portfolio_service') as mock_service:
            mock_service.return_value.get_portfolio_summary.side_effect = InvalidAPIKeyError(
                "Invalid Bitvavo API key", {"key_type": "bitvavo"}
            )

            response = client.get("/api/v1/portfolio/summary")

            assert response.status_code == 401
            data = response.json()
            assert data["error_code"] == "INVALID_API_KEY"
            assert "Invalid Bitvavo API key" in data["error_message"]
            assert data["details"]["key_type"] == "bitvavo"


class TestEndpointSpecificErrorHandling:
    """Test endpoint-specific error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_portfolio_summary_error_handling(self, client):
        """Test portfolio summary endpoint error handling."""
        with patch('app.core.dependencies.get_portfolio_service') as mock_service:
            # Test different error scenarios
            mock_service.return_value.get_portfolio_summary.side_effect = Exception("Unexpected error")

            response = client.get("/api/v1/portfolio/summary")

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "INTERNAL_SERVER_ERROR"
            assert data["error_message"] == "An unexpected error occurred"

    def test_market_prices_error_handling(self, client):
        """Test market prices endpoint error handling."""
        with patch('app.core.dependencies.get_market_service') as mock_service:
            mock_service.return_value.get_current_prices.side_effect = ConnectionError("Network error")

            response = client.get("/api/v1/market/prices")

            assert response.status_code == 500
            data = response.json()
            assert data["error_code"] == "INTERNAL_SERVER_ERROR"

    def test_chat_query_validation_errors(self, client):
        """Test chat query validation errors."""
        # Test missing required fields
        response = client.post("/api/v1/chat/query", json={})
        assert response.status_code == 422

        # Test invalid temperature
        response = client.post("/api/v1/chat/query", json={
            "message": "test",
            "temperature": 2.0  # Invalid: should be 0.0-1.0
        })
        assert response.status_code == 422

        # Test empty message
        response = client.post("/api/v1/chat/query", json={
            "message": "",
            "model": "gpt-4"
        })
        assert response.status_code == 422

    def test_invalid_request_handling(self, client):
        """Test invalid request handling."""
        with patch('app.core.dependencies.get_chat_service') as mock_service:
            mock_service.return_value.process_chat_request.side_effect = InvalidRequestException(
                "Invalid message format", {"format": "required"}
            )

            response = client.post("/api/v1/chat/query", json={
                "message": "test message",
                "model": "gpt-4"
            })

            assert response.status_code == 400
            data = response.json()
            assert data["error_code"] == "INVALID_REQUEST"
            assert "Invalid message format" in data["error_message"]
            assert data["details"]["format"] == "required"
