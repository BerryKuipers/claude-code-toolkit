"""
Pydantic models for strongly typed API responses and requests.

These models provide C#-like DTOs with runtime validation and auto-generated
OpenAPI documentation.
"""

from .chat import *
from .common import *
from .market import *
from .portfolio import *

__all__ = [
    # Common models
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "SortOrder",
    "AssetSymbol",
    # Portfolio models
    "PortfolioSummaryResponse",
    "HoldingResponse",
    "TransactionResponse",
    "TransferSummaryResponse",
    "ReconciliationResponse",
    "PurchaseLotResponse",
    # Market models
    "MarketDataResponse",
    "PriceResponse",
    "MarketOpportunitiesResponse",
    "TechnicalAnalysisResponse",
    # Chat models
    "ChatRequest",
    "ChatResponse",
    "FunctionCallRequest",
    "FunctionCallResponse",
    "FunctionDefinition",
]
