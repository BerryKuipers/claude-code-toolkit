"""
Portfolio-related Pydantic models.

These models represent portfolio data structures with full type safety
and validation, similar to C# DTOs for financial data.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from .common import AssetSymbol, BaseResponse


class PurchaseLotResponse(BaseModel):
    """Purchase lot data model (FIFO accounting)."""
    
    amount: Decimal = Field(..., description="Crypto units in this lot", decimal_places=8)
    cost_eur: Decimal = Field(..., description="Total EUR cost including fees", decimal_places=2)
    timestamp: int = Field(..., description="Milliseconds since epoch")
    
    @validator('amount', 'cost_eur')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Amount and cost must be positive')
        return v


class TransferSummaryResponse(BaseModel):
    """Transfer summary data model."""
    
    total_deposits: Decimal = Field(..., description="Total amount deposited", decimal_places=8)
    total_withdrawals: Decimal = Field(..., description="Total amount withdrawn", decimal_places=8)
    net_transfers: Decimal = Field(..., description="Net transfer amount", decimal_places=8)
    deposit_count: int = Field(..., description="Number of deposit transactions", ge=0)
    withdrawal_count: int = Field(..., description="Number of withdrawal transactions", ge=0)
    potential_rewards: Decimal = Field(..., description="Estimated staking rewards/airdrops", decimal_places=8)


class HoldingResponse(BaseModel):
    """Individual asset holding data model."""
    
    asset: AssetSymbol = Field(..., description="Asset symbol")
    quantity: Decimal = Field(..., description="Quantity held", decimal_places=8)
    current_price: Decimal = Field(..., description="Current price in EUR", decimal_places=4)
    value_eur: Decimal = Field(..., description="Current value in EUR", decimal_places=2)
    cost_basis: Decimal = Field(..., description="Average cost basis in EUR", decimal_places=2)
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L in EUR", decimal_places=2)
    realized_pnl: Decimal = Field(..., description="Realized P&L in EUR", decimal_places=2)
    portfolio_percentage: Decimal = Field(..., description="Portfolio allocation %", decimal_places=2)
    total_return_percentage: Decimal = Field(..., description="Total return %", decimal_places=2)
    
    @validator('quantity', 'current_price', 'value_eur', 'cost_basis')
    def validate_positive_values(cls, v):
        if v < 0:
            raise ValueError('Financial values must be non-negative')
        return v


class TransactionResponse(BaseModel):
    """Transaction data model."""
    
    id: str = Field(..., description="Transaction ID")
    asset: AssetSymbol = Field(..., description="Asset symbol")
    side: str = Field(..., description="Transaction side (buy/sell)")
    amount: Decimal = Field(..., description="Transaction amount", decimal_places=8)
    price: Decimal = Field(..., description="Transaction price in EUR", decimal_places=4)
    fee: Decimal = Field(..., description="Transaction fee in EUR", decimal_places=4)
    timestamp: int = Field(..., description="Transaction timestamp (ms since epoch)")
    
    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('Side must be buy or sell')
        return v.lower()


class PortfolioSummaryResponse(BaseResponse):
    """Complete portfolio summary with all key metrics."""
    
    total_value: Decimal = Field(..., description="Total portfolio value in EUR", decimal_places=2)
    total_cost: Decimal = Field(..., description="Total cost basis in EUR", decimal_places=2)
    realized_pnl: Decimal = Field(..., description="Realized P&L in EUR", decimal_places=2)
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L in EUR", decimal_places=2)
    total_pnl: Decimal = Field(..., description="Total P&L in EUR", decimal_places=2)
    total_return_percentage: Decimal = Field(..., description="Total return as percentage", decimal_places=2)
    asset_count: int = Field(..., description="Number of different assets held", ge=0)
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    @validator('total_value', 'total_cost')
    def validate_positive_totals(cls, v):
        if v < 0:
            raise ValueError('Total values must be non-negative')
        return v


class ReconciliationResponse(BaseResponse):
    """Portfolio reconciliation data model."""
    
    asset: AssetSymbol = Field(..., description="Asset symbol")
    fifo_amount: Decimal = Field(..., description="FIFO calculated amount", decimal_places=8)
    actual_amount: Decimal = Field(..., description="Actual balance amount", decimal_places=8)
    discrepancy: Decimal = Field(..., description="Difference between FIFO and actual", decimal_places=8)
    transfer_summary: TransferSummaryResponse = Field(..., description="Transfer analysis")
    explanation: str = Field(..., description="Discrepancy explanation")
    confidence_level: str = Field(..., description="Confidence in explanation")


class PortfolioHoldingsResponse(BaseResponse):
    """Response containing all portfolio holdings."""
    
    holdings: List[HoldingResponse] = Field(..., description="List of all holdings")
    summary: PortfolioSummaryResponse = Field(..., description="Portfolio summary")
    last_updated: datetime = Field(..., description="Data last updated timestamp")
