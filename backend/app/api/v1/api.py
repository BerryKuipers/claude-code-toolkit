"""
Main API router for v1 endpoints.

Combines all endpoint routers into a single API router with proper
organization and documentation.
"""

from fastapi import APIRouter

from .endpoints import chat, market, portfolio, cache

# Create main API router
api_router = APIRouter()

# Include endpoint routers with proper prefixes and tags
api_router.include_router(
    portfolio.router,
    prefix="/portfolio",
    tags=["Portfolio"],
)

api_router.include_router(
    market.router,
    prefix="/market",
    tags=["Market"],
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"],
)

api_router.include_router(
    cache.router,
    prefix="/cache",
    tags=["Cache"],
)
