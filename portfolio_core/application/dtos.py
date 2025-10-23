"""
Data Transfer Objects (DTOs)

DTOs for transferring data across application boundaries.
These are simple data containers without business logic.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class TradeDTO:
    """Data transfer object for trade information."""
    id: UUID
    asset_symbol: str
    trade_type: str  # "buy" or "sell"
    amount: Decimal
    price: Decimal
    fee: Decimal
    timestamp: int
    currency: str = "EUR"


@dataclass(frozen=True)
class AssetHoldingDTO:
    """Data transfer object for asset holding information."""
    symbol: str
    amount: Decimal
    cost_basis: Decimal
    current_value: Decimal
    current_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    return_percentage: Decimal
    portfolio_percentage: Decimal
    currency: str = "EUR"


@dataclass(frozen=True)
class PortfolioSummaryDTO:
    """Data transfer object for portfolio summary information."""
    total_value: Decimal
    total_cost_basis: Decimal
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    total_pnl: Decimal
    return_percentage: Decimal
    asset_count: int
    last_updated: datetime
    currency: str = "EUR"


@dataclass(frozen=True)
class ReconciliationResultDTO:
    """Data transfer object for reconciliation results."""
    asset_symbol: str
    calculated_balance: Decimal
    actual_balance: Decimal
    discrepancy: Decimal
    discrepancy_percentage: Decimal
    explanation: str
    is_reconciled: bool
    currency: str = "EUR"


@dataclass(frozen=True)
class TransferSummaryDTO:
    """Data transfer object for transfer summary information."""
    asset_symbol: str
    total_deposits: Decimal
    total_withdrawals: Decimal
    net_transfers: Decimal
    deposit_count: int
    withdrawal_count: int
    currency: str = "EUR"


@dataclass(frozen=True)
class MarketDataDTO:
    """Data transfer object for market data."""
    asset_symbol: str
    current_price: Decimal
    price_change_24h: Optional[Decimal]
    volume_24h: Optional[Decimal]
    market_cap: Optional[Decimal]
    last_updated: datetime
    currency: str = "EUR"


@dataclass(frozen=True)
class PortfolioPerformanceDTO:
    """Data transfer object for portfolio performance analysis."""
    total_return: Decimal
    annualized_return: Optional[Decimal]
    volatility: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    max_drawdown: Optional[Decimal]
    best_performing_asset: Optional[str]
    worst_performing_asset: Optional[str]
    analysis_period_days: int
    currency: str = "EUR"
