"""
Strongly typed Bitvavo API client implementation.

This client integrates the existing Bitvavo API logic with the new
strongly typed interface, providing proper error handling and rate limiting.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi.concurrency import run_in_threadpool

from ..core.config import Settings
from ..core.exceptions import (
    BitvavoAPIException,
    InvalidAPIKeyError,
    RateLimitExceededError,
)
from ..services.interfaces.bitvavo_client import IBitvavoClient

logger = logging.getLogger(__name__)

try:
    from python_bitvavo_api.bitvavo import Bitvavo  # type: ignore
except ImportError:
    Bitvavo = None


class BitvavoClient(IBitvavoClient):
    """
    Strongly typed Bitvavo API client implementation.

    This client wraps the existing Bitvavo API logic with proper typing
    and integrates with the existing rate limiting and error handling.
    """

    def __init__(self, settings: Settings):
        """
        Initialize Bitvavo client with API credentials.

        Args:
            settings: Application settings with API credentials
        """
        self.settings = settings
        self._client: Optional["Bitvavo"] = None

        if Bitvavo is None:
            raise BitvavoAPIException("python-bitvavo-api package not installed")

        logger.info("Bitvavo client initialized")

    def _get_client(self) -> "Bitvavo":
        """Get or create Bitvavo client instance."""
        if self._client is None:
            self._client = Bitvavo(
                {
                    "APIKEY": self.settings.bitvavo_api_key,
                    "APISECRET": self.settings.bitvavo_api_secret,
                    "RESTURL": "https://api.bitvavo.com/v2",
                    "WSURL": "wss://ws.bitvavo.com/v2/",
                    "ACCESSWINDOW": 10000,
                    "DEBUGGING": self.settings.debug,
                }
            )
        return self._client

    def _check_rate_limit(self) -> None:
        """Enforce rate limit using existing rate limiter."""
        # Import here to avoid circular imports
        import os
        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
        from src.portfolio.api import default_rate_limiter

        default_rate_limiter.enforce_rate_limit(self._get_client())

    def _decimal(self, value: str | float | int | Decimal) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

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
        try:
            self._check_rate_limit()
            client = self._get_client()

            if symbol:
                balance = await run_in_threadpool(client.balance, {"symbol": symbol})
            else:
                balance = await run_in_threadpool(client.balance, {})

            if isinstance(balance, dict) and "errorCode" in balance:
                error_code = balance.get("errorCode")
                if error_code == 304:
                    raise InvalidAPIKeyError("API key / time sync issue")
                elif error_code == 105:
                    raise RateLimitExceededError("Hit Bitvavo rate limit")
                else:
                    raise BitvavoAPIException(f"Bitvavo API error: {balance}")

            return balance if isinstance(balance, list) else []

        except (InvalidAPIKeyError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise BitvavoAPIException(f"Failed to get balance: {str(e)}")

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
        try:
            trades: List[Dict[str, Any]] = []
            cursor: Optional[str] = None
            client = self._get_client()

            while True:
                self._check_rate_limit()

                kwargs = {"limit": 1000}
                if cursor:
                    kwargs["tradeIdTo"] = cursor

                batch = await run_in_threadpool(client.trades, market, kwargs)

                if isinstance(batch, dict) and "errorCode" in batch:
                    error_code = batch.get("errorCode")
                    if error_code == 304:
                        raise InvalidAPIKeyError("API key / time sync issue")
                    elif error_code == 105:
                        raise RateLimitExceededError("Hit Bitvavo rate limit")
                    else:
                        raise BitvavoAPIException(f"Bitvavo API error: {batch}")

                if not batch:
                    break

                trades.extend(batch)
                cursor = batch[-1]["id"]

            trades.reverse()  # oldest-first for FIFO
            return trades

        except (InvalidAPIKeyError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error getting trade history for {market}: {e}")
            raise BitvavoAPIException(f"Failed to get trade history: {str(e)}")

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
        try:
            self._check_rate_limit()
            client = self._get_client()

            deposits = await run_in_threadpool(client.depositHistory, {"symbol": symbol})

            if isinstance(deposits, dict) and "errorCode" in deposits:
                logger.warning(f"Bitvavo API error for {symbol} deposits: {deposits}")
                return []

            if not deposits:
                return []

            return deposits if isinstance(deposits, list) else []

        except Exception as e:
            logger.warning(f"Exception fetching deposit history for {symbol}: {e}")
            return []

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
        try:
            self._check_rate_limit()
            client = self._get_client()

            withdrawals = await run_in_threadpool(client.withdrawalHistory, {"symbol": symbol})

            if isinstance(withdrawals, dict) and "errorCode" in withdrawals:
                logger.warning(f"Bitvavo API error for {symbol} withdrawals: {withdrawals}")
                return []

            if not withdrawals:
                return []

            return withdrawals if isinstance(withdrawals, list) else []

        except Exception as e:
            logger.warning(f"Exception fetching withdrawal history for {symbol}: {e}")
            return []

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
        try:
            self._check_rate_limit()
            client = self._get_client()

            ticker = await run_in_threadpool(client.tickerPrice, {"market": market})

            if isinstance(ticker, dict) and "errorCode" in ticker:
                error_code = ticker.get("errorCode")
                if error_code == 304:
                    raise InvalidAPIKeyError("API key / time sync issue")
                elif error_code == 105:
                    raise RateLimitExceededError("Hit Bitvavo rate limit")
                else:
                    raise BitvavoAPIException(f"Bitvavo API error: {ticker}")

            # Handle both dict and list responses
            if isinstance(ticker, dict) and "price" in ticker:
                return ticker
            elif isinstance(ticker, list) and ticker and "price" in ticker[0]:
                return ticker[0]
            else:
                return {"price": "0"}

        except (InvalidAPIKeyError, RateLimitExceededError):
            raise
        except Exception as e:
            logger.error(f"Error getting ticker price for {market}: {e}")
            return {"price": "0"}

    async def get_remaining_limit(self) -> int:
        """
        Get remaining API rate limit.

        Returns:
            int: Remaining API calls

        Raises:
            BitvavoAPIException: If API call fails
        """
        try:
            client = self._get_client()
            return client.getRemainingLimit()
        except Exception as e:
            logger.error(f"Error getting remaining limit: {e}")
            raise BitvavoAPIException(f"Failed to get remaining limit: {str(e)}")

    async def sync_time(self) -> bool:
        """
        Synchronize time with Bitvavo servers.

        Returns:
            bool: True if time sync was successful

        Raises:
            BitvavoAPIException: If time sync fails
        """
        try:
            client = self._get_client()
            response = client.time()
            return response is not None
        except Exception as e:
            logger.error(f"Error syncing time: {e}")
            raise BitvavoAPIException(f"Failed to sync time: {str(e)}")
