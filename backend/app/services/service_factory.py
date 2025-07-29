"""
Service factory for creating service instances with proper dependency injection.

This factory follows the Dependency Inversion Principle by abstracting
service creation and managing dependencies centrally.
"""

from typing import Dict, Optional

from ..clients.bitvavo_client import BitvavoAPIClient
from ..core.config import Settings
from .interfaces.bitvavo_client import IBitvavoClient
from .interfaces.chat_service import IChatService
from .interfaces.market_service import IMarketService
from .interfaces.portfolio_service import IPortfolioService


class ServiceFactory:
    """
    Factory for creating service instances with proper dependency management.

    This class follows the Factory Pattern and Dependency Inversion Principle
    to centralize service creation and dependency management.
    """

    def __init__(self, settings: Settings):
        """
        Initialize service factory.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._clients: Dict[str, any] = {}
        self._services: Dict[str, any] = {}

    def get_bitvavo_client(self) -> IBitvavoClient:
        """
        Get or create Bitvavo client instance.

        Returns:
            IBitvavoClient: Bitvavo client instance
        """
        if "bitvavo" not in self._clients:
            self._clients["bitvavo"] = BitvavoAPIClient(self.settings)
        return self._clients["bitvavo"]

    def get_portfolio_service(self) -> IPortfolioService:
        """
        Get or create portfolio service instance.

        Returns:
            IPortfolioService: Portfolio service instance
        """
        if "portfolio" not in self._services:
            # Import here to avoid circular imports
            from .portfolio_service import PortfolioService

            # Use Clean Architecture service
            self._services["portfolio"] = PortfolioService(
                self.settings, self.get_bitvavo_client()
            )
        return self._services["portfolio"]

    def get_market_service(self) -> IMarketService:
        """
        Get or create market service instance.

        Returns:
            IMarketService: Market service instance
        """
        if "market" not in self._services:
            # Import here to avoid circular imports
            from .market_service import MarketService

            self._services["market"] = MarketService(
                self.settings, self.get_bitvavo_client()
            )
        return self._services["market"]

    def get_chat_service(self) -> IChatService:
        """
        Get or create chat service instance.

        Returns:
            IChatService: Chat service instance
        """
        if "chat" not in self._services:
            # Import here to avoid circular imports
            from .chat_service import ChatService

            self._services["chat"] = ChatService(
                self.settings, self.get_portfolio_service()
            )
        return self._services["chat"]

    def clear_cache(self) -> None:
        """Clear all cached service instances."""
        self._clients.clear()
        self._services.clear()

    def get_service_health(self) -> Dict[str, str]:
        """
        Get health status of all created services.

        Returns:
            Dict[str, str]: Service health status
        """
        health = {}

        for service_name, service in self._services.items():
            try:
                # Check if service has a health check method
                if hasattr(service, "health_check"):
                    health[service_name] = (
                        "healthy" if service.health_check() else "unhealthy"
                    )
                else:
                    health[service_name] = (
                        "healthy"  # Assume healthy if no check method
                    )
            except Exception:
                health[service_name] = "unhealthy"

        return health
