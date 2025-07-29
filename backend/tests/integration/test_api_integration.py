"""
Integration tests for API endpoints.

Tests end-to-end functionality with real service integration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

from app.main import app


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_bitvavo_client(self):
        """Mock Bitvavo client for integration tests."""
        client = AsyncMock()
        
        # Mock balance response
        client.get_balance.return_value = [
            {"symbol": "BTC", "available": "0.5", "inOrder": "0.0"},
            {"symbol": "ETH", "available": "2.0", "inOrder": "0.0"},
        ]
        
        # Mock trades response
        client.get_trades.return_value = [
            {
                "id": "trade1",
                "timestamp": "1640995200000",
                "market": "BTC-EUR",
                "side": "buy",
                "amount": "0.5",
                "price": "40000.00",
                "fee": "20.00",
                "feeCurrency": "EUR",
            }
        ]
        
        # Mock deposit history
        client.get_deposit_history.return_value = [
            {
                "symbol": "BTC",
                "amount": "0.5",
                "status": "completed",
                "timestamp": "1640995100000",
            }
        ]
        
        # Mock ticker prices
        client.get_ticker_price.return_value = {"price": "50000.00"}
        
        return client

    @pytest.mark.integration
    def test_portfolio_workflow_integration(self, client, mock_bitvavo_client):
        """Test complete portfolio workflow integration."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            # 1. Get portfolio summary
            summary_response = client.get("/api/v1/portfolio/summary")
            assert summary_response.status_code == 200
            summary_data = summary_response.json()
            assert summary_data["success"] is True
            
            # 2. Get portfolio holdings
            holdings_response = client.get("/api/v1/portfolio/holdings")
            assert holdings_response.status_code == 200
            holdings_data = holdings_response.json()
            assert holdings_data["success"] is True
            assert len(holdings_data["holdings"]) > 0
            
            # 3. Get transaction history
            transactions_response = client.get("/api/v1/portfolio/transactions")
            assert transactions_response.status_code == 200
            transactions_data = transactions_response.json()
            assert isinstance(transactions_data, list)
            
            # 4. Reconcile portfolio
            reconciliation_response = client.get("/api/v1/portfolio/reconciliation")
            assert reconciliation_response.status_code == 200
            reconciliation_data = reconciliation_response.json()
            assert isinstance(reconciliation_data, list)

    @pytest.mark.integration
    def test_market_data_workflow_integration(self, client, mock_bitvavo_client):
        """Test complete market data workflow integration."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            # 1. Get market data
            market_response = client.get("/api/v1/market/data")
            assert market_response.status_code == 200
            market_data = market_response.json()
            assert market_data["success"] is True
            
            # 2. Get current prices
            prices_response = client.get("/api/v1/market/prices")
            assert prices_response.status_code == 200
            prices_data = prices_response.json()
            assert isinstance(prices_data, dict)
            
            # 3. Get specific asset price
            btc_price_response = client.get("/api/v1/market/prices/BTC")
            assert btc_price_response.status_code == 200
            btc_price_data = btc_price_response.json()
            assert btc_price_data["symbol"] == "BTC"

    @pytest.mark.integration
    def test_chat_workflow_integration(self, client):
        """Test chat workflow integration with mocked AI."""
        mock_chat_response = {
            "success": True,
            "message": "Your portfolio is currently valued at €25,000.00",
            "model": "claude-sonnet-4",
            "tokens_used": 150,
            "cost_eur": "0.0045",
            "conversation_id": "test-conv",
            "function_calls": [],
            "timestamp": "2025-01-01T00:00:00",
        }
        
        with patch("app.services.chat_service.ChatService.process_chat_request", return_value=mock_chat_response):
            # 1. Get available functions
            functions_response = client.get("/api/v1/chat/functions")
            assert functions_response.status_code == 200
            
            # 2. Create conversation
            conversation_response = client.post("/api/v1/chat/conversations")
            assert conversation_response.status_code == 200
            
            # 3. Process chat query
            chat_request = {
                "message": "What is my portfolio value?",
                "model": "claude-sonnet-4",
                "enable_function_calling": True,
            }
            chat_response = client.post("/api/v1/chat/query", json=chat_request)
            assert chat_response.status_code == 200

    @pytest.mark.integration
    def test_error_handling_integration(self, client):
        """Test error handling across API endpoints."""
        # Test invalid asset
        invalid_asset_response = client.get("/api/v1/market/prices/INVALID")
        assert invalid_asset_response.status_code in [404, 500]
        
        # Test invalid conversation
        invalid_conv_response = client.get("/api/v1/chat/conversations/invalid-id")
        assert invalid_conv_response.status_code in [404, 500]
        
        # Test malformed chat request
        malformed_chat = {"invalid": "request"}
        malformed_response = client.post("/api/v1/chat/query", json=malformed_chat)
        assert malformed_response.status_code == 422

    @pytest.mark.integration
    def test_data_consistency_integration(self, client, mock_bitvavo_client):
        """Test data consistency across different endpoints."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            # Get portfolio summary
            summary_response = client.get("/api/v1/portfolio/summary")
            summary_data = summary_response.json()
            
            # Get portfolio holdings
            holdings_response = client.get("/api/v1/portfolio/holdings")
            holdings_data = holdings_response.json()
            
            # Verify data consistency
            assert summary_data["total_value"] == holdings_data["total_value"]
            assert summary_data["asset_count"] == holdings_data["asset_count"]

    @pytest.mark.integration
    def test_refresh_data_integration(self, client, mock_bitvavo_client):
        """Test data refresh functionality integration."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            # Refresh portfolio data
            portfolio_refresh = client.post("/api/v1/portfolio/refresh")
            assert portfolio_refresh.status_code == 200
            refresh_data = portfolio_refresh.json()
            assert refresh_data["success"] is True
            
            # Refresh market data
            market_refresh = client.post("/api/v1/market/refresh")
            assert market_refresh.status_code == 200
            market_refresh_data = market_refresh.json()
            assert market_refresh_data["success"] is True

    @pytest.mark.integration
    def test_performance_integration(self, client, mock_bitvavo_client):
        """Test API performance under normal load."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            import time
            
            # Test multiple concurrent requests
            start_time = time.time()
            
            responses = []
            for _ in range(5):
                response = client.get("/api/v1/portfolio/summary")
                responses.append(response)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Should complete within reasonable time (5 seconds for 5 requests)
            assert total_time < 5.0

    @pytest.mark.integration
    def test_health_check_integration(self, client):
        """Test health check endpoint integration."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data

    @pytest.mark.integration
    def test_cors_integration(self, client):
        """Test CORS configuration integration."""
        # Test preflight request
        response = client.options(
            "/api/v1/portfolio/summary",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            }
        )
        # Should not fail (exact status depends on CORS setup)
        assert response.status_code in [200, 204]

    @pytest.mark.integration
    def test_api_documentation_integration(self, client):
        """Test API documentation endpoints."""
        # Test OpenAPI JSON
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200
        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data
        
        # Test Swagger UI (should redirect or serve HTML)
        docs_response = client.get("/docs")
        assert docs_response.status_code in [200, 307]  # 307 for redirect

    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_workflow_integration(self, client, mock_bitvavo_client):
        """Test complete application workflow integration."""
        with patch("app.clients.bitvavo_client.BitvavoAPIClient", return_value=mock_bitvavo_client):
            # 1. Check health
            health_response = client.get("/health")
            assert health_response.status_code == 200
            
            # 2. Get portfolio data
            portfolio_response = client.get("/api/v1/portfolio/holdings")
            assert portfolio_response.status_code == 200
            
            # 3. Get market data
            market_response = client.get("/api/v1/market/data")
            assert market_response.status_code == 200
            
            # 4. Get available chat functions
            functions_response = client.get("/api/v1/chat/functions")
            assert functions_response.status_code == 200
            
            # 5. Refresh all data
            portfolio_refresh = client.post("/api/v1/portfolio/refresh")
            market_refresh = client.post("/api/v1/market/refresh")
            assert portfolio_refresh.status_code == 200
            assert market_refresh.status_code == 200
            
            # All operations should complete successfully
            print("✅ Full workflow integration test completed successfully")
