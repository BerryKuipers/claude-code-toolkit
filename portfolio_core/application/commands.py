"""
Command objects for CQRS pattern.

Commands represent actions that change state in the system.
They encapsulate all the data needed to perform an operation.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class CalculatePortfolioCommand:
    """Command to calculate portfolio P&L and holdings."""
    portfolio_id: UUID
    force_refresh: bool = False
    include_transfers: bool = True


@dataclass(frozen=True)
class RefreshPortfolioDataCommand:
    """Command to refresh portfolio data from external sources."""
    portfolio_id: UUID
    refresh_trades: bool = True
    refresh_prices: bool = True
    refresh_balances: bool = True


@dataclass(frozen=True)
class ReconcilePortfolioCommand:
    """Command to reconcile portfolio balances."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None
    include_transfer_analysis: bool = True


@dataclass(frozen=True)
class AddTradeCommand:
    """Command to add a new trade to the portfolio."""
    portfolio_id: UUID
    asset_symbol: str
    trade_type: str  # "buy" or "sell"
    amount: str  # String to preserve precision
    price: str   # String to preserve precision
    fee: str     # String to preserve precision
    timestamp: int


@dataclass(frozen=True)
class UpdateAssetPricesCommand:
    """Command to update current prices for portfolio assets."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None


@dataclass(frozen=True)
class AnalyzePortfolioPerformanceCommand:
    """Command to analyze portfolio performance metrics."""
    portfolio_id: UUID
    analysis_period_days: int = 365
    include_risk_metrics: bool = True


@dataclass(frozen=True)
class ExportPortfolioDataCommand:
    """Command to export portfolio data."""
    portfolio_id: UUID
    export_format: str  # "csv", "json", "excel"
    include_trades: bool = True
    include_transfers: bool = True
    date_range_start: Optional[int] = None
    date_range_end: Optional[int] = None
