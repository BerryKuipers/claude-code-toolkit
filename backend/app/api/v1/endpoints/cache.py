"""
Cache management endpoints for development.

Provides endpoints to monitor, manage, and control the local development cache.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ....core.dependencies import get_bitvavo_client
from ....clients.bitvavo_client import BitvavoClientDecorator
from ....models.common import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    bitvavo_client=Depends(get_bitvavo_client)
) -> Dict[str, Any]:
    """
    Get cache statistics and health information.
    
    Returns:
        Cache statistics including entry counts and health status
    """
    try:
        # Check if we're using the cached client
        if isinstance(bitvavo_client, BitvavoClientDecorator):
            stats = bitvavo_client.get_cache_stats()
            health = await bitvavo_client.health_check()
            
            return {
                "cache_enabled": True,
                "stats": stats,
                "health": health,
                "message": "Cache statistics retrieved successfully"
            }
        else:
            return {
                "cache_enabled": False,
                "message": "Cache is not enabled - using direct API client"
            }
            
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {e}")


@router.post("/clear-expired", response_model=BaseResponse)
async def clear_expired_cache(
    bitvavo_client=Depends(get_bitvavo_client)
) -> BaseResponse:
    """
    Clear expired cache entries.
    
    Returns:
        Success response
    """
    try:
        if isinstance(bitvavo_client, BitvavoClientDecorator):
            bitvavo_client.clear_expired_cache()
            
            return BaseResponse(
                success=True,
                message="Expired cache entries cleared successfully"
            )
        else:
            return BaseResponse(
                success=False,
                message="Cache is not enabled - no action taken"
            )
            
    except Exception as e:
        logger.error(f"Failed to clear expired cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear expired cache: {e}")


@router.post("/force-refresh", response_model=BaseResponse)
async def force_refresh_cache(
    bitvavo_client=Depends(get_bitvavo_client)
) -> BaseResponse:
    """
    Force refresh all cached data on next API call.
    
    This clears all cache entries to force fresh data retrieval.
    
    Returns:
        Success response
    """
    try:
        if isinstance(bitvavo_client, BitvavoClientDecorator):
            bitvavo_client.force_refresh_cache()
            
            return BaseResponse(
                success=True,
                message="Cache cleared - next API calls will fetch fresh data"
            )
        else:
            return BaseResponse(
                success=False,
                message="Cache is not enabled - no action taken"
            )
            
    except Exception as e:
        logger.error(f"Failed to force refresh cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to force refresh cache: {e}")


@router.get("/health", response_model=Dict[str, Any])
async def get_cache_health(
    bitvavo_client=Depends(get_bitvavo_client)
) -> Dict[str, Any]:
    """
    Get cache and API health status.
    
    Returns:
        Health status including API availability and cache status
    """
    try:
        if isinstance(bitvavo_client, BitvavoClientDecorator):
            health = await bitvavo_client.health_check()
            return health
        else:
            # For non-cached client, just check API availability
            try:
                await bitvavo_client.get_ticker_price("BTC-EUR")
                return {
                    "api_available": True,
                    "cache_enabled": False,
                    "message": "API is available, cache not enabled"
                }
            except Exception as api_error:
                return {
                    "api_available": False,
                    "cache_enabled": False,
                    "last_error": str(api_error),
                    "message": "API is unavailable, cache not enabled"
                }
            
    except Exception as e:
        logger.error(f"Failed to get cache health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache health: {e}")


@router.post("/warm-up", response_model=BaseResponse)
async def warm_up_cache(
    bitvavo_client=Depends(get_bitvavo_client)
) -> BaseResponse:
    """
    Warm up the cache by fetching and caching essential data.
    
    This endpoint fetches portfolio holdings and popular asset prices
    to populate the cache for faster subsequent requests.
    
    Returns:
        Success response with cache warming results
    """
    try:
        if not isinstance(bitvavo_client, BitvavoClientDecorator):
            return BaseResponse(
                success=False,
                message="Cache is not enabled - cannot warm up cache"
            )
        
        cached_items = 0
        errors = []
        
        # Warm up portfolio holdings
        try:
            await bitvavo_client.get_balance()
            cached_items += 1
            logger.info("Portfolio holdings cached during warm-up")
        except Exception as e:
            errors.append(f"Portfolio holdings: {e}")
        
        # Warm up popular asset prices
        popular_assets = ["BTC-EUR", "ETH-EUR", "ADA-EUR", "DOT-EUR", "LINK-EUR"]
        for market in popular_assets:
            try:
                await bitvavo_client.get_ticker_price(market)
                cached_items += 1
                logger.debug(f"Price for {market} cached during warm-up")
            except Exception as e:
                errors.append(f"{market}: {e}")
        
        message = f"Cache warm-up completed: {cached_items} items cached"
        if errors:
            message += f", {len(errors)} errors occurred"
        
        return BaseResponse(
            success=True,
            message=message,
            data={
                "cached_items": cached_items,
                "errors": errors
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to warm up cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm up cache: {e}")


@router.get("/config", response_model=Dict[str, Any])
async def get_cache_config(
    bitvavo_client=Depends(get_bitvavo_client)
) -> Dict[str, Any]:
    """
    Get cache configuration information.
    
    Returns:
        Cache configuration settings
    """
    try:
        if isinstance(bitvavo_client, BitvavoClientDecorator):
            return {
                "cache_enabled": True,
                "settings": {
                    "enable_dev_cache": bitvavo_client.settings.enable_dev_cache,
                    "dev_cache_path": bitvavo_client.settings.dev_cache_path,
                    "cache_portfolio_ttl_hours": bitvavo_client.settings.cache_portfolio_ttl_hours,
                    "cache_prices_ttl_minutes": bitvavo_client.settings.cache_prices_ttl_minutes,
                    "cache_trades_ttl_hours": bitvavo_client.settings.cache_trades_ttl_hours,
                }
            }
        else:
            return {
                "cache_enabled": False,
                "message": "Cache is not enabled"
            }
            
    except Exception as e:
        logger.error(f"Failed to get cache config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache config: {e}")
