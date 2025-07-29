"""
Dependency Injection Container

Wires up all Clean Architecture components with proper dependency injection.
This is the composition root where all dependencies are configured.
"""

import logging
import sys
import os
from uuid import UUID, uuid4
from typing import Optional

# Add project root to Python path for portfolio_core imports
_current_file = os.path.abspath(__file__)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))  # backend/app/core -> backend
_project_root = os.path.dirname(_backend_dir)  # backend -> crypto_insight

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from .config import Settings

# Import from real Clean Architecture modules
from portfolio_core.application.services import PortfolioApplicationService, MarketDataApplicationService
from portfolio_core.domain.services import FIFOCalculationService, PortfolioCalculationService
from portfolio_core.infrastructure.repositories import BitvavoPortfolioRepository, BitvavoMarketDataRepository
from portfolio_core.infrastructure.mappers import BitvavoDataMapper
from portfolio_core.infrastructure.clients import BitvavoAPIClient

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency injection container for Clean Architecture components.
    
    This container follows the Dependency Inversion Principle by ensuring
    that high-level modules don't depend on low-level modules, but both
    depend on abstractions.
    """
    
    def __init__(self, settings: Settings):
        """Initialize container with application settings."""
        self.settings = settings
        self._instances = {}
        self._default_portfolio_id = uuid4()  # Default portfolio for single-user scenario
        
        logger.info("Initializing Clean Architecture dependency container")
    
    def get_bitvavo_api_client(self) -> BitvavoAPIClient:
        """Get or create Bitvavo API client."""
        if "bitvavo_api_client" not in self._instances:
            try:
                client = BitvavoAPIClient(
                    api_key=self.settings.bitvavo_api_key,
                    api_secret=self.settings.bitvavo_api_secret,
                    rate_limit_delay=self.settings.bitvavo_rate_limit_delay
                )
                self._instances["bitvavo_api_client"] = client
                logger.info("✅ Created Bitvavo API client")
            except Exception as e:
                logger.error(f"❌ Failed to create Bitvavo API client: {e}")
                raise
        
        return self._instances["bitvavo_api_client"]
    
    def get_bitvavo_data_mapper(self) -> BitvavoDataMapper:
        """Get or create Bitvavo data mapper."""
        if "bitvavo_data_mapper" not in self._instances:
            self._instances["bitvavo_data_mapper"] = BitvavoDataMapper()
            logger.debug("Created Bitvavo data mapper")
        
        return self._instances["bitvavo_data_mapper"]
    
    def get_portfolio_repository(self) -> BitvavoPortfolioRepository:
        """Get or create portfolio repository."""
        if "portfolio_repository" not in self._instances:
            bitvavo_client = self.get_bitvavo_api_client()
            data_mapper = self.get_bitvavo_data_mapper()
            
            repository = BitvavoPortfolioRepository(bitvavo_client, data_mapper)
            self._instances["portfolio_repository"] = repository
            logger.debug("Created portfolio repository")
        
        return self._instances["portfolio_repository"]
    
    def get_market_data_repository(self) -> BitvavoMarketDataRepository:
        """Get or create market data repository."""
        if "market_data_repository" not in self._instances:
            bitvavo_client = self.get_bitvavo_api_client()
            data_mapper = self.get_bitvavo_data_mapper()
            
            repository = BitvavoMarketDataRepository(bitvavo_client, data_mapper)
            self._instances["market_data_repository"] = repository
            logger.debug("Created market data repository")
        
        return self._instances["market_data_repository"]
    
    def get_fifo_calculation_service(self) -> FIFOCalculationService:
        """Get or create FIFO calculation service."""
        if "fifo_calculation_service" not in self._instances:
            self._instances["fifo_calculation_service"] = FIFOCalculationService()
            logger.debug("Created FIFO calculation service")
        
        return self._instances["fifo_calculation_service"]
    
    def get_portfolio_calculation_service(self) -> PortfolioCalculationService:
        """Get or create portfolio calculation service."""
        if "portfolio_calculation_service" not in self._instances:
            fifo_service = self.get_fifo_calculation_service()
            
            service = PortfolioCalculationService(fifo_service)
            self._instances["portfolio_calculation_service"] = service
            logger.debug("Created portfolio calculation service")
        
        return self._instances["portfolio_calculation_service"]
    
    def get_portfolio_application_service(self) -> PortfolioApplicationService:
        """Get or create portfolio application service."""
        if "portfolio_application_service" not in self._instances:
            portfolio_repository = self.get_portfolio_repository()
            market_data_repository = self.get_market_data_repository()
            fifo_service = self.get_fifo_calculation_service()
            portfolio_calculation_service = self.get_portfolio_calculation_service()
            
            service = PortfolioApplicationService(
                portfolio_repository=portfolio_repository,
                market_data_repository=market_data_repository,
                fifo_service=fifo_service,
                portfolio_calculation_service=portfolio_calculation_service,
            )
            self._instances["portfolio_application_service"] = service
            logger.info("✅ Created portfolio application service")
        
        return self._instances["portfolio_application_service"]
    
    def get_market_data_application_service(self) -> MarketDataApplicationService:
        """Get or create market data application service."""
        if "market_data_application_service" not in self._instances:
            market_data_repository = self.get_market_data_repository()
            
            service = MarketDataApplicationService(market_data_repository)
            self._instances["market_data_application_service"] = service
            logger.debug("Created market data application service")
        
        return self._instances["market_data_application_service"]
    
    def get_default_portfolio_id(self) -> UUID:
        """Get the default portfolio ID for single-user scenarios."""
        return self._default_portfolio_id
    
    def health_check(self) -> dict:
        """
        Perform health check on all components.
        
        Returns:
            Dictionary with health status of each component
        """
        health_status = {
            "container": "healthy",
            "components": {}
        }
        
        try:
            # Check Bitvavo API client
            bitvavo_client = self.get_bitvavo_api_client()
            health_status["components"]["bitvavo_api_client"] = "healthy"
        except Exception as e:
            health_status["components"]["bitvavo_api_client"] = f"unhealthy: {e}"
            health_status["container"] = "degraded"
        
        try:
            # Check application services
            portfolio_service = self.get_portfolio_application_service()
            health_status["components"]["portfolio_application_service"] = "healthy"
        except Exception as e:
            health_status["components"]["portfolio_application_service"] = f"unhealthy: {e}"
            health_status["container"] = "degraded"
        
        try:
            # Check market data service
            market_service = self.get_market_data_application_service()
            health_status["components"]["market_data_application_service"] = "healthy"
        except Exception as e:
            health_status["components"]["market_data_application_service"] = f"unhealthy: {e}"
            health_status["container"] = "degraded"
        
        return health_status
    
    def cleanup(self) -> None:
        """Clean up resources and connections."""
        logger.info("Cleaning up dependency container")
        
        # Clear all instances
        self._instances.clear()
        
        logger.info("Dependency container cleanup complete")


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container(settings: Optional[Settings] = None) -> DependencyContainer:
    """
    Get the global dependency container instance.
    
    Args:
        settings: Application settings (required for first call)
        
    Returns:
        DependencyContainer instance
    """
    global _container
    
    if _container is None:
        if settings is None:
            raise ValueError("Settings required for first container initialization")
        _container = DependencyContainer(settings)
    
    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container
    if _container:
        _container.cleanup()
    _container = None
