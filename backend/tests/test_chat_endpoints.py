"""
Unit tests for Chat API endpoints.

Tests all chat endpoints with proper mocking and validation.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_chat_service
from app.core.exceptions import (
    ChatServiceException,
    ConversationNotFoundException,
    FunctionNotFoundException,
    InvalidRequestException,
)
from app.models.chat import (
    ChatResponse,
    AvailableFunctionsResponse,
    FunctionDefinition,
    CreateConversationResponse,
    ChatHistoryResponse,
    DeleteConversationResponse,
)


class TestChatEndpoints:
    """Test chat API endpoints."""

    @pytest.fixture
    def mock_chat_service(self):
        """Create mock chat service."""
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_chat_service):
        """Create test client with mocked dependencies."""
        app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
        client = TestClient(app)
        yield client
        # Clean up after test
        app.dependency_overrides.clear()

    @pytest.fixture
    def sample_chat_request(self):
        """Sample chat request."""
        return {
            "message": "What is my portfolio value?",
            "model": "claude-sonnet-4",
            "temperature": 0.1,
            "max_tokens": 4000,
            "conversation_id": "conv-123",
            "enable_function_calling": True,
        }

    @pytest.fixture
    def sample_chat_response(self):
        """Sample chat response."""
        from datetime import datetime
        from app.models.chat import FunctionCallResponse

        function_call = FunctionCallResponse(
            function_name="get_portfolio_summary",
            result={"total_value": "36885.34"},
            success=True,
            execution_time_ms=150.5,
        )

        return ChatResponse(
            success=True,
            timestamp=datetime.now(),
            message="Your portfolio is currently valued at €36,885.34",
            conversation_id="conv-123",
            model_used="claude-sonnet-4",
            function_calls=[function_call],
            token_usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
            response_time_ms=1250.0,
            cost_estimate=0.0045,
        )

    @pytest.fixture
    def sample_function_definition(self):
        """Sample function definition."""
        return FunctionDefinition(
            name="get_portfolio_summary",
            description="Get comprehensive portfolio summary",
            parameters=[],  # No parameters for this simple function
        )

    def test_process_chat_query_success(self, client, mock_chat_service, sample_chat_request, sample_chat_response):
        """Test successful chat query processing."""
        mock_chat_service.process_chat_request.return_value = sample_chat_response

        response = client.post("/api/v1/chat/query", json=sample_chat_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "portfolio" in data["message"].lower()
        assert data["model_used"] == "claude-sonnet-4"
        assert len(data["function_calls"]) == 1

    def test_process_chat_query_invalid_request(self, client, mock_chat_service, sample_chat_request):
        """Test chat query with invalid request."""
        mock_chat_service.process_chat_request.side_effect = InvalidRequestException("Invalid model specified")

        response = client.post("/api/v1/chat/query", json=sample_chat_request)

        assert response.status_code == 400
        assert "Invalid model specified" in response.json()["detail"]

    def test_process_chat_query_service_error(self, client, mock_chat_service, sample_chat_request):
        """Test chat query with service error."""
        mock_chat_service.process_chat_request.side_effect = ChatServiceException("AI service unavailable")

        response = client.post("/api/v1/chat/query", json=sample_chat_request)

        assert response.status_code == 500
        assert "AI service unavailable" in response.json()["detail"]

    def test_process_chat_query_missing_message(self, client, mock_chat_service):
        """Test chat query with missing message."""
        invalid_request = {
            "model": "claude-sonnet-4",
            "temperature": 0.1,
        }
        
        response = client.post("/api/v1/chat/query", json=invalid_request)
        
        assert response.status_code == 422  # Validation error

    def test_get_available_functions_success(self, client, mock_chat_service, sample_function_definition):
        """Test successful available functions retrieval."""
        from datetime import datetime
        functions_response = AvailableFunctionsResponse(
            success=True,
            timestamp=datetime.now(),
            functions=[sample_function_definition],
            total_functions=1,
            categories={"portfolio": ["get_portfolio_summary"]},
        )
        
        mock_chat_service.get_available_functions.return_value = functions_response

        response = client.get("/api/v1/chat/functions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_functions"] == 1
        assert len(data["functions"]) == 1
        assert data["functions"][0]["name"] == "get_portfolio_summary"

    def test_get_available_functions_service_error(self, client, mock_chat_service):
        """Test available functions with service error."""
        mock_chat_service.get_available_functions.side_effect = ChatServiceException("Function registry unavailable")

        response = client.get("/api/v1/chat/functions")

        assert response.status_code == 500
        assert "Function registry unavailable" in response.json()["detail"]

    def test_get_function_definition_success(self, client, mock_chat_service, sample_function_definition):
        """Test successful function definition retrieval."""
        mock_chat_service.get_function_definition.return_value = sample_function_definition

        response = client.get("/api/v1/chat/functions/get_portfolio_summary")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get_portfolio_summary"
        assert "portfolio summary" in data["description"].lower()

    def test_get_function_definition_not_found(self, client, mock_chat_service):
        """Test function definition for non-existent function."""
        mock_chat_service.get_function_definition.side_effect = FunctionNotFoundException("Function not found")

        response = client.get("/api/v1/chat/functions/invalid_function")

        assert response.status_code == 404
        assert "Function not found" in response.json()["detail"]

    def test_create_conversation_success(self, client, mock_chat_service):
        """Test successful conversation creation."""
        create_response = CreateConversationResponse(
            success=True,
            conversation_id="conv-456",
            message="Conversation created successfully",
            timestamp="2025-01-01T00:00:00",
        )
        
        mock_chat_service.create_conversation.return_value = create_response

        response = client.post("/api/v1/chat/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == "conv-456"

    def test_get_conversation_history_success(self, client, mock_chat_service):
        """Test successful conversation history retrieval."""
        history_response = ChatHistoryResponse(
            success=True,
            conversation_id="conv-123",
            messages=[
                {
                    "role": "user",
                    "content": "What is my portfolio value?",
                    "timestamp": "2025-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": "Your portfolio is valued at €36,885.34",
                    "timestamp": "2025-01-01T00:00:01",
                },
            ],
            message_count=2,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:01",
        )
        
        mock_chat_service.get_conversation_history.return_value = history_response

        response = client.get("/api/v1/chat/conversations/conv-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == "conv-123"
        assert data["message_count"] == 2

    def test_get_conversation_history_not_found(self, client, mock_chat_service):
        """Test conversation history for non-existent conversation."""
        mock_chat_service.get_conversation_history.side_effect = ConversationNotFoundException("Conversation not found")

        response = client.get("/api/v1/chat/conversations/invalid-conv")

        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    def test_delete_conversation_success(self, client, mock_chat_service):
        """Test successful conversation deletion."""
        delete_response = DeleteConversationResponse(
            success=True,
            conversation_id="conv-123",
            message="Conversation deleted successfully",
            timestamp="2025-01-01T00:00:00",
        )
        
        mock_chat_service.delete_conversation.return_value = delete_response

        response = client.delete("/api/v1/chat/conversations/conv-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == "conv-123"

    def test_delete_conversation_not_found(self, client, mock_chat_service):
        """Test deletion of non-existent conversation."""
        mock_chat_service.delete_conversation.side_effect = ConversationNotFoundException("Conversation not found")

        response = client.delete("/api/v1/chat/conversations/invalid-conv")

        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    def test_get_function_definition_success(self, client, mock_chat_service, sample_function_definition):
        """Test successful function definition retrieval."""
        mock_chat_service.get_function_definition.return_value = sample_function_definition

        response = client.get("/api/v1/chat/functions/get_portfolio_summary")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get_portfolio_summary"
        assert data["description"] == "Get portfolio summary with total value and holdings"
        assert "parameters" in data

    def test_get_function_definition_not_found(self, client, mock_chat_service):
        """Test function definition for non-existent function."""
        mock_chat_service.get_function_definition.side_effect = FunctionNotFoundException("Function not found")

        response = client.get("/api/v1/chat/functions/invalid_function")

        assert response.status_code == 404
        assert "Function not found" in response.json()["detail"]

    def test_get_function_definition_service_error(self, client, mock_chat_service):
        """Test function definition with service error."""
        mock_chat_service.get_function_definition.side_effect = ChatServiceException("Service unavailable")

        response = client.get("/api/v1/chat/functions/get_portfolio_summary")

        assert response.status_code == 500
        assert "Service unavailable" in response.json()["detail"]

    def test_process_chat_query_invalid_temperature(self, client, mock_chat_service):
        """Test chat query with invalid temperature value."""
        invalid_request = {
            "message": "Test message",
            "temperature": 2.0,  # Invalid: should be between 0.0 and 1.0
        }

        response = client.post("/api/v1/chat/query", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_process_chat_query_empty_message(self, client, mock_chat_service):
        """Test chat query with empty message."""
        invalid_request = {
            "message": "",  # Empty message should be invalid
            "model": "claude-sonnet-4",
        }

        response = client.post("/api/v1/chat/query", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_process_chat_query_invalid_request_exception(self, client, mock_chat_service, sample_chat_request):
        """Test chat query with invalid request exception."""
        mock_chat_service.process_chat_request.side_effect = InvalidRequestException("Invalid request format")

        response = client.post("/api/v1/chat/query", json=sample_chat_request)

        assert response.status_code == 400
        assert "Invalid request format" in response.json()["detail"]

    def test_create_conversation_service_error(self, client, mock_chat_service):
        """Test conversation creation with service error."""
        mock_chat_service.create_conversation.side_effect = ChatServiceException("Failed to create conversation")

        response = client.post("/api/v1/chat/conversations")

        assert response.status_code == 500
        assert "Failed to create conversation" in response.json()["detail"]

    def test_get_conversation_history_service_error(self, client, mock_chat_service):
        """Test conversation history with service error."""
        mock_chat_service.get_conversation_history.side_effect = ChatServiceException("Database unavailable")

        response = client.get("/api/v1/chat/conversations/conv-123")

        assert response.status_code == 500
        assert "Database unavailable" in response.json()["detail"]

    def test_delete_conversation_service_error(self, client, mock_chat_service):
        """Test conversation deletion with service error."""
        mock_chat_service.delete_conversation.side_effect = ChatServiceException("Failed to delete")

        response = client.delete("/api/v1/chat/conversations/conv-123")

        assert response.status_code == 500
        assert "Failed to delete" in response.json()["detail"]
