"""
Query objects for CQRS pattern.

Queries represent requests for data without changing state.
They encapsulate all the parameters needed to retrieve information.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True)
class GetPortfolioSummaryQuery:
    """Query to get portfolio summary information."""
    portfolio_id: UUID
    include_performance_metrics: bool = True


@dataclass(frozen=True)
class GetAssetHoldingsQuery:
    """Query to get detailed asset holdings."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None
    min_value_threshold: Optional[float] = None
    sort_by: str = "value"  # "value", "allocation", "pnl", "symbol"
    sort_descending: bool = True
    include_zero_balances: bool = False  # Include assets with zero holdings


@dataclass(frozen=True)
class GetTradeHistoryQuery:
    """Query to get trade history."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None
    trade_types: Optional[List[str]] = None  # ["buy", "sell"]
    date_range_start: Optional[int] = None
    date_range_end: Optional[int] = None
    limit: Optional[int] = None
    offset: int = 0


@dataclass(frozen=True)
class GetMarketDataQuery:
    """Query to get current market data."""
    asset_symbols: List[str]
    include_24h_change: bool = True
    include_volume: bool = False
    include_market_cap: bool = False


@dataclass(frozen=True)
class GetReconciliationResultsQuery:
    """Query to get portfolio reconciliation results."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None
    only_discrepancies: bool = False
    min_discrepancy_threshold: Optional[float] = None


@dataclass(frozen=True)
class GetTransferHistoryQuery:
    """Query to get transfer (deposit/withdrawal) history."""
    portfolio_id: UUID
    asset_symbols: Optional[List[str]] = None
    transfer_types: Optional[List[str]] = None  # ["deposit", "withdrawal"]
    date_range_start: Optional[int] = None
    date_range_end: Optional[int] = None


@dataclass(frozen=True)
class GetPortfolioPerformanceQuery:
    """Query to get portfolio performance analysis."""
    portfolio_id: UUID
    analysis_period_days: int = 365
    benchmark_symbol: Optional[str] = None  # e.g., "BTC" for comparison
    include_risk_metrics: bool = True


@dataclass(frozen=True)
class GetAssetAllocationQuery:
    """Query to get asset allocation breakdown."""
    portfolio_id: UUID
    min_allocation_percentage: float = 1.0
    group_small_allocations: bool = True
    currency: str = "EUR"
