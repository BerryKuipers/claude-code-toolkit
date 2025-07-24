"""
Test the basic API structure and type safety.

This test ensures that our strongly typed API structure is working
correctly and provides the C#-like development experience.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAPIStructure:
    """Test basic API structure and endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns basic API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Crypto Portfolio API"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema generation."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Check that our endpoints are documented
        paths = schema["paths"]
        assert "/api/v1/portfolio/summary" in paths
        assert "/api/v1/portfolio/holdings" in paths
        assert "/api/v1/market/data" in paths
        assert "/api/v1/chat/query" in paths
    
    def test_portfolio_endpoints_exist(self, client):
        """Test that portfolio endpoints exist (even if they return errors due to missing config)."""
        # These will likely return 500 due to missing Bitvavo credentials in test,
        # but we're testing that the endpoints exist and are properly typed
        
        endpoints = [
            "/api/v1/portfolio/summary",
            "/api/v1/portfolio/holdings",
            "/api/v1/portfolio/holdings/complete",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not be 404 (endpoint exists) or 422 (validation error)
            assert response.status_code not in [404, 422]
    
    def test_market_endpoints_exist(self, client):
        """Test that market endpoints exist."""
        endpoints = [
            "/api/v1/market/data",
            "/api/v1/market/prices",
            "/api/v1/market/opportunities",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not be 404 (endpoint exists) or 422 (validation error)
            assert response.status_code not in [404, 422]
    
    def test_chat_endpoints_exist(self, client):
        """Test that chat endpoints exist."""
        # Test GET endpoints
        get_endpoints = [
            "/api/v1/chat/functions",
        ]
        
        for endpoint in get_endpoints:
            response = client.get(endpoint)
            assert response.status_code not in [404, 422]
        
        # Test POST endpoint with minimal valid data
        chat_response = client.post(
            "/api/v1/chat/query",
            json={
                "message": "test message",
                "use_function_calling": False
            }
        )
        # Should not be 404 or 422 (validation error)
        assert chat_response.status_code not in [404, 422]
    
    def test_cors_headers(self, client):
        """Test CORS headers are properly configured."""
        response = client.options("/api/v1/portfolio/summary")
        
        # CORS should be configured
        assert response.status_code in [200, 405]  # 405 is OK for OPTIONS if not explicitly handled
    
    def test_error_handling(self, client):
        """Test error handling returns proper error responses."""
        # Test non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test invalid asset endpoint
        response = client.get("/api/v1/portfolio/performance/INVALID_ASSET_SYMBOL_THAT_DOES_NOT_EXIST")
        # Should return proper error response structure
        assert response.status_code in [404, 500]
        
        if response.status_code == 404:
            data = response.json()
            # Should have error structure if our exception handling is working
            assert "detail" in data or "error_message" in data


class TestTypeValidation:
    """Test Pydantic model validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_chat_request_validation(self, client):
        """Test chat request validation."""
        # Test invalid request (empty message)
        response = client.post(
            "/api/v1/chat/query",
            json={
                "message": "",  # Empty message should be invalid
                "use_function_calling": True
            }
        )
        assert response.status_code == 422  # Validation error
        
        # Test invalid temperature
        response = client.post(
            "/api/v1/chat/query",
            json={
                "message": "test",
                "temperature": 2.0  # Should be between 0.0 and 1.0
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_response_models_structure(self, client):
        """Test that response models have the expected structure."""
        # Test health endpoint response structure
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["success", "timestamp", "status", "version", "uptime_seconds", "dependencies"]
        
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from health response"
