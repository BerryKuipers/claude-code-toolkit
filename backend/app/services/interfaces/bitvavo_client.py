"""
Bitvavo client interface definition.

Defines the contract for Bitvavo exchange API operations
with full type safety and error handling.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional


class IBitvavoClient(ABC):
    """
    Bitvavo client interface providing C#-like contract definition.
    
    This interface defines all Bitvavo API operations with strong typing
    and clear error handling patterns.
    """
    
    @abstractmethod
    async def get_balance(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get account balance for all assets or a specific asset.
        
        Args:
            symbol: Optional asset symbol to filter by
            
        Returns:
            List[Dict[str, Any]]: Balance data from Bitvavo API
            
        Raises:
            BitvavoAPIException: If API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_trade_history(self, market: str) -> List[Dict[str, Any]]:
        """
        Get trade history for a specific market.
        
        Args:
            market: Market symbol (e.g., 'BTC-EUR')
            
        Returns:
            List[Dict[str, Any]]: Trade history from Bitvavo API
            
        Raises:
            BitvavoAPIException: If API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_deposit_history(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get deposit history for a specific asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List[Dict[str, Any]]: Deposit history from Bitvavo API
            
        Raises:
            BitvavoAPIException: If API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_withdrawal_history(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get withdrawal history for a specific asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List[Dict[str, Any]]: Withdrawal history from Bitvavo API
            
        Raises:
            BitvavoAPIException: If API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_ticker_price(self, market: str) -> Dict[str, Any]:
        """
        Get current ticker price for a market.
        
        Args:
            market: Market symbol (e.g., 'BTC-EUR')
            
        Returns:
            Dict[str, Any]: Ticker price data from Bitvavo API
            
        Raises:
            BitvavoAPIException: If API call fails
            RateLimitExceededError: If rate limit is exceeded
        """
        pass
    
    @abstractmethod
    async def get_remaining_limit(self) -> int:
        """
        Get remaining API rate limit.
        
        Returns:
            int: Remaining API calls
            
        Raises:
            BitvavoAPIException: If API call fails
        """
        pass
    
    @abstractmethod
    async def sync_time(self) -> bool:
        """
        Synchronize time with Bitvavo servers.
        
        Returns:
            bool: True if time sync was successful
            
        Raises:
            BitvavoAPIException: If time sync fails
        """
        pass
