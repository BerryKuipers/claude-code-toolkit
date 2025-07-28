"""
Market data Pydantic models.

These models represent market analysis and price data with full type safety,
providing structured responses for market-related endpoints.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .common import AssetSymbol, BaseResponse


class TrendDirection(str, Enum):
    """Market trend direction."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PriceResponse(BaseModel):
    """Current price data for an asset."""

    asset: AssetSymbol = Field(..., description="Asset symbol")
    price_eur: Decimal = Field(
        ..., description="Current price in EUR", decimal_places=4
    )
    price_change_24h: Decimal = Field(
        ..., description="24h price change %", decimal_places=2
    )
    volume_24h: Decimal = Field(..., description="24h trading volume", decimal_places=2)
    last_updated: datetime = Field(..., description="Price last updated timestamp")

    @field_validator("price_eur", "volume_24h")
    @classmethod
    def validate_positive_values(cls, v):
        if v < 0:
            raise ValueError("Price and volume must be non-negative")
        return v


class TechnicalIndicatorResponse(BaseModel):
    """Technical analysis indicator data."""

    indicator_name: str = Field(..., description="Technical indicator name")
    value: Decimal = Field(..., description="Indicator value", decimal_places=4)
    signal: str = Field(..., description="Trading signal (buy/sell/hold)")
    confidence: Decimal = Field(
        ..., description="Signal confidence (0-1)", decimal_places=2
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class TechnicalAnalysisResponse(BaseModel):
    """Complete technical analysis for an asset."""

    asset: AssetSymbol = Field(..., description="Asset symbol")
    trend_direction: TrendDirection = Field(..., description="Overall trend direction")
    indicators: List[TechnicalIndicatorResponse] = Field(
        ..., description="Technical indicators"
    )
    support_levels: List[Decimal] = Field(..., description="Support price levels")
    resistance_levels: List[Decimal] = Field(..., description="Resistance price levels")
    recommendation: str = Field(..., description="Overall trading recommendation")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    analysis_timestamp: datetime = Field(..., description="Analysis timestamp")


class MarketOpportunityResponse(BaseModel):
    """Market opportunity analysis."""

    asset: AssetSymbol = Field(..., description="Asset symbol")
    opportunity_type: str = Field(..., description="Type of opportunity")
    potential_return: Decimal = Field(
        ..., description="Potential return %", decimal_places=2
    )
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    time_horizon: str = Field(..., description="Recommended time horizon")
    reasoning: str = Field(..., description="Analysis reasoning")
    confidence_score: Decimal = Field(
        ..., description="Confidence score (0-1)", decimal_places=2
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v


class MarketOpportunitiesResponse(BaseResponse):
    """Market opportunities analysis response."""

    opportunities: List[MarketOpportunityResponse] = Field(
        ..., description="Market opportunities"
    )
    market_sentiment: str = Field(..., description="Overall market sentiment")
    analysis_summary: str = Field(..., description="Summary of market analysis")
    last_updated: datetime = Field(..., description="Analysis timestamp")


class MarketDataResponse(BaseResponse):
    """Comprehensive market data response."""

    prices: Dict[str, PriceResponse] = Field(..., description="Current prices by asset")
    market_cap_total: Decimal = Field(
        ..., description="Total market cap", decimal_places=2
    )
    market_trend: TrendDirection = Field(..., description="Overall market trend")
    fear_greed_index: Optional[int] = Field(
        None, description="Fear & Greed Index (0-100)"
    )
    top_gainers: List[PriceResponse] = Field(..., description="Top gaining assets")
    top_losers: List[PriceResponse] = Field(..., description="Top losing assets")
    last_updated: datetime = Field(..., description="Data last updated timestamp")

    @field_validator("fear_greed_index")
    @classmethod
    def validate_fear_greed_range(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Fear & Greed Index must be between 0 and 100")
        return v
