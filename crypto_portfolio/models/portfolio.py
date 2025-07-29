"""
Portfolio data models.

Centralized data models for all portfolio operations with proper
type safety and validation.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class PurchaseLot:
    """Represents a purchase lot for FIFO calculations."""
    amount: Decimal
    cost_eur: Decimal
    timestamp: int


@dataclass
class TransferSummary:
    """Summary of transfer operations for an asset."""
    asset: str
    total_deposits: Decimal
    total_withdrawals: Decimal
    net_transfers: Decimal
    deposit_count: int
    withdrawal_count: int


@dataclass
class AssetHolding:
    """Represents a single asset holding in the portfolio."""
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
    last_updated: datetime


@dataclass
class PortfolioSummary:
    """Summary of the entire portfolio."""
    total_value: Decimal
    total_cost: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    total_return_percentage: Decimal
    asset_count: int
    last_updated: datetime


@dataclass
class ReconciliationResult:
    """Result of portfolio reconciliation analysis."""
    asset: str
    calculated_balance: Decimal
    actual_balance: Decimal
    discrepancy: Decimal
    discrepancy_percentage: Decimal
    explanation: str
    is_reconciled: bool
