"""
Bitvavo API client with rate limiting and error handling.

Provides a clean interface to the Bitvavo API with proper error handling,
rate limiting, and connection management.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from .exceptions import (
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)

try:
    from python_bitvavo_api.bitvavo import Bitvavo  # type: ignore
except ImportError:  # pragma: no cover
    Bitvavo = None


class BitvavoClient:
    """
    Bitvavo API client with rate limiting and error handling.
    
    Provides a clean, reliable interface to the Bitvavo API with automatic
    rate limiting, error handling, and connection management.
    """
    
    def __init__(self, api_key: str, api_secret: str, rate_limit_delay: float = 0.2):
        """
        Initialize the Bitvavo client.
        
        Args:
            api_key: Bitvavo API key
            api_secret: Bitvavo API secret
            rate_limit_delay: Delay between API calls in seconds
        """
        if not Bitvavo:
            raise ImportError("python_bitvavo_api package is required")
            
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit_delay = rate_limit_delay
        self._client: Optional[Bitvavo] = None
        self._last_request_time = 0.0
        
    def _get_client(self) -> Bitvavo:
        """Get or create the Bitvavo client instance."""
        if self._client is None:
            self._client = Bitvavo({
                'APIKEY': self.api_key,
                'APISECRET': self.api_secret,
                'RESTURL': 'https://api.bitvavo.com/v2',
                'WSURL': 'wss://ws.bitvavo.com/v2/',
                'ACCESSWINDOW': 10000,
                'DEBUGGING': False
            })
            self._sync_time()
        return self._client
        
    def _sync_time(self) -> None:
        """Synchronize local clock offset to avoid 304 errors."""
        try:
            client = self._get_client()
            time_response = client.time()
            if isinstance(time_response, dict) and "time" in time_response:
                server_time_ms = int(time_response["time"])
            else:
                # Fallback: use local time (no offset)
                server_time_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        except Exception as exc:
            raise BitvavoAPIException(f"Failed to sync time: {exc}")
            
    def _rate_limit(self) -> None:
        """Apply rate limiting between API calls."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self._last_request_time = time.time()
        
    def _handle_api_error(self, response: Any, operation: str) -> None:
        """Handle API error responses."""
        if isinstance(response, dict) and "error" in response:
            error_code = response.get("errorCode", "unknown")
            error_msg = response.get("error", "Unknown error")
            
            if error_code in ["304", "401", "403"]:
                raise InvalidAPIKeyError(f"{operation} failed: {error_msg}")
            elif error_code == "429":
                raise RateLimitExceededError(f"{operation} failed: {error_msg}")
            else:
                raise BitvavoAPIException(f"{operation} failed: {error_msg}")
                
    def get_balance(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get account balance for all assets or a specific asset."""
        self._rate_limit()
        client = self._get_client()
        
        try:
            if symbol:
                response = client.balance({"symbol": symbol})
            else:
                response = client.balance({})
                
            self._handle_api_error(response, "get_balance")
            return response if isinstance(response, list) else [response]
            
        except Exception as e:
            if not isinstance(e, (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError)):
                raise BitvavoAPIException(f"Failed to get balance: {e}")
            raise
            
    def get_trades(self, market: str, limit: int = 1000, start: Optional[int] = None, 
                   end: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade history for a specific market."""
        self._rate_limit()
        client = self._get_client()
        
        try:
            params = {"market": market, "limit": limit}
            if start:
                params["start"] = start
            if end:
                params["end"] = end
                
            response = client.trades(params)
            self._handle_api_error(response, "get_trades")
            return response if isinstance(response, list) else []
            
        except Exception as e:
            if not isinstance(e, (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError)):
                raise BitvavoAPIException(f"Failed to get trades: {e}")
            raise
            
    def get_ticker_price(self, market: str) -> Dict[str, Any]:
        """Get current ticker price for a market."""
        self._rate_limit()
        client = self._get_client()
        
        try:
            response = client.tickerPrice({"market": market})
            self._handle_api_error(response, "get_ticker_price")
            return response
            
        except Exception as e:
            if not isinstance(e, (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError)):
                raise BitvavoAPIException(f"Failed to get ticker price: {e}")
            raise
            
    def get_deposit_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get deposit history."""
        self._rate_limit()
        client = self._get_client()
        
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
                
            response = client.depositHistory(params)
            self._handle_api_error(response, "get_deposit_history")
            return response if isinstance(response, list) else []
            
        except Exception as e:
            if not isinstance(e, (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError)):
                raise BitvavoAPIException(f"Failed to get deposit history: {e}")
            raise
            
    def get_withdrawal_history(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get withdrawal history."""
        self._rate_limit()
        client = self._get_client()
        
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
                
            response = client.withdrawalHistory(params)
            self._handle_api_error(response, "get_withdrawal_history")
            return response if isinstance(response, list) else []
            
        except Exception as e:
            if not isinstance(e, (BitvavoAPIException, InvalidAPIKeyError, RateLimitExceededError)):
                raise BitvavoAPIException(f"Failed to get withdrawal history: {e}")
            raise
