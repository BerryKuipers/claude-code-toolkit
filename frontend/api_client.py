"""
Strongly typed API client for the crypto portfolio backend.

This client provides type-safe communication with the FastAPI backend,
giving the frontend the same C# developer experience with full IntelliSense.
"""

import logging
from typing import Dict, List, Optional, Union
from decimal import Decimal
import httpx
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class PortfolioSummary:
    """Portfolio summary data model (mirrors backend PortfolioSummaryResponse)."""
    
    def __init__(self, data: Dict):
        self.total_value = Decimal(str(data.get("total_value", "0")))
        self.total_cost = Decimal(str(data.get("total_cost", "0")))
        self.realized_pnl = Decimal(str(data.get("realized_pnl", "0")))
        self.unrealized_pnl = Decimal(str(data.get("unrealized_pnl", "0")))
        self.total_pnl = Decimal(str(data.get("total_pnl", "0")))
        self.total_return_percentage = Decimal(str(data.get("total_return_percentage", "0")))
        self.asset_count = data.get("asset_count", 0)
        self.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))


class Holding:
    """Individual asset holding data model (mirrors backend HoldingResponse)."""
    
    def __init__(self, data: Dict):
        self.asset = data.get("asset", "")
        self.quantity = Decimal(str(data.get("quantity", "0")))
        self.current_price = Decimal(str(data.get("current_price", "0")))
        self.value_eur = Decimal(str(data.get("value_eur", "0")))
        self.cost_basis = Decimal(str(data.get("cost_basis", "0")))
        self.unrealized_pnl = Decimal(str(data.get("unrealized_pnl", "0")))
        self.realized_pnl = Decimal(str(data.get("realized_pnl", "0")))
        self.portfolio_percentage = Decimal(str(data.get("portfolio_percentage", "0")))
        self.total_return_percentage = Decimal(str(data.get("total_return_percentage", "0")))


class Transaction:
    """Transaction data model (mirrors backend TransactionResponse)."""
    
    def __init__(self, data: Dict):
        self.id = data.get("id", "")
        self.asset = data.get("asset", "")
        self.side = data.get("side", "")
        self.amount = Decimal(str(data.get("amount", "0")))
        self.price = Decimal(str(data.get("price", "0")))
        self.fee = Decimal(str(data.get("fee", "0")))
        self.timestamp = data.get("timestamp", 0)


class ChatResponse:
    """Chat response data model (mirrors backend ChatResponse)."""
    
    def __init__(self, data: Dict):
        self.message = data.get("message", "")
        self.conversation_id = data.get("conversation_id", "")
        self.model_used = data.get("model_used", "")
        self.function_calls = data.get("function_calls", [])
        self.token_usage = data.get("token_usage", {})
        self.response_time_ms = data.get("response_time_ms", 0.0)
        self.cost_estimate = data.get("cost_estimate", 0.0)


class CryptoPortfolioAPIClient:
    """
    Strongly typed API client for the crypto portfolio backend.
    
    This client provides type-safe methods for all backend endpoints
    with proper error handling and response parsing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """
        Initialize API client.
        
        Args:
            base_url: Backend API base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"API client initialized for {self.base_url}")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self._client.request(method, url, **kwargs)
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    raise APIException(
                        message=error_data.get("error_message", f"HTTP {response.status_code}"),
                        status_code=response.status_code,
                        details=error_data.get("details", {})
                    )
                except ValueError:
                    raise APIException(
                        message=f"HTTP {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )
            
            return response.json()
            
        except httpx.RequestError as e:
            raise APIException(f"Request failed: {str(e)}")
    
    async def health_check(self) -> Dict:
        """Check API health status."""
        return await self._request("GET", "/health")
    
    # Portfolio endpoints
    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get comprehensive portfolio summary."""
        data = await self._request("GET", "/api/v1/portfolio/summary")
        return PortfolioSummary(data)
    
    async def get_current_holdings(self) -> List[Holding]:
        """Get list of all current holdings."""
        data = await self._request("GET", "/api/v1/portfolio/holdings")
        return [Holding(holding) for holding in data]
    
    async def get_asset_performance(self, asset: str) -> Holding:
        """Get performance data for a specific asset."""
        data = await self._request("GET", f"/api/v1/portfolio/performance/{asset}")
        return Holding(data)
    
    async def get_transaction_history(self, asset: Optional[str] = None) -> List[Transaction]:
        """Get transaction history."""
        params = {"asset": asset} if asset else {}
        data = await self._request("GET", "/api/v1/portfolio/transactions", params=params)
        return [Transaction(tx) for tx in data]
    
    async def refresh_portfolio_data(self) -> bool:
        """Force refresh of portfolio data."""
        data = await self._request("POST", "/api/v1/portfolio/refresh")
        return data.get("success", False)
    
    # Market endpoints
    async def get_market_data(self) -> Dict:
        """Get comprehensive market data."""
        return await self._request("GET", "/api/v1/market/data")
    
    async def get_current_prices(self, assets: Optional[List[str]] = None) -> Dict:
        """Get current market prices."""
        params = {"assets": assets} if assets else {}
        return await self._request("GET", "/api/v1/market/prices", params=params)
    
    async def get_market_opportunities(self) -> Dict:
        """Get market investment opportunities."""
        return await self._request("GET", "/api/v1/market/opportunities")
    
    # Chat endpoints
    async def chat_query(self, message: str, conversation_id: Optional[str] = None, 
                        use_function_calling: bool = True, temperature: float = 0.1) -> ChatResponse:
        """Send chat query to AI assistant."""
        data = {
            "message": message,
            "use_function_calling": use_function_calling,
            "temperature": temperature
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        response_data = await self._request("POST", "/api/v1/chat/query", json=data)
        return ChatResponse(response_data)
    
    async def get_available_functions(self) -> Dict:
        """Get list of available AI functions."""
        return await self._request("GET", "/api/v1/chat/functions")
    
    async def create_conversation(self) -> str:
        """Create new chat conversation."""
        data = await self._request("POST", "/api/v1/chat/conversations")
        return data.get("conversation_id", "")
    
    # Utility methods
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Synchronous wrapper for Streamlit compatibility
class SyncCryptoPortfolioAPIClient:
    """
    Synchronous wrapper for the async API client.
    
    This provides a synchronous interface for use in Streamlit
    while maintaining the same type safety.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self._async_client = CryptoPortfolioAPIClient(base_url, timeout)
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def health_check(self) -> Dict:
        """Check API health status."""
        return self._run_async(self._async_client.health_check())
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get comprehensive portfolio summary."""
        return self._run_async(self._async_client.get_portfolio_summary())
    
    def get_current_holdings(self) -> List[Holding]:
        """Get list of all current holdings."""
        return self._run_async(self._async_client.get_current_holdings())
    
    def get_asset_performance(self, asset: str) -> Holding:
        """Get performance data for a specific asset."""
        return self._run_async(self._async_client.get_asset_performance(asset))
    
    def get_transaction_history(self, asset: Optional[str] = None) -> List[Transaction]:
        """Get transaction history."""
        return self._run_async(self._async_client.get_transaction_history(asset))
    
    def refresh_portfolio_data(self) -> bool:
        """Force refresh of portfolio data."""
        return self._run_async(self._async_client.refresh_portfolio_data())
    
    def get_market_data(self) -> Dict:
        """Get comprehensive market data."""
        return self._run_async(self._async_client.get_market_data())
    
    def chat_query(self, message: str, conversation_id: Optional[str] = None, 
                   use_function_calling: bool = True, temperature: float = 0.1) -> ChatResponse:
        """Send chat query to AI assistant."""
        return self._run_async(self._async_client.chat_query(
            message, conversation_id, use_function_calling, temperature
        ))
    
    def get_available_functions(self) -> Dict:
        """Get list of available AI functions."""
        return self._run_async(self._async_client.get_available_functions())
    
    def close(self):
        """Close the HTTP client."""
        self._run_async(self._async_client.close())
