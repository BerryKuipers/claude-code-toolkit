"""Crypto Portfolio FIFO P&L Analysis Package

A comprehensive toolkit for analyzing cryptocurrency portfolio performance
using FIFO (First-In-First-Out) accounting with high-precision Decimal arithmetic.

Features:
- FIFO P&L calculation with Decimal precision
- Bitvavo API integration for trade history and live prices
- CLI interface with Typer
- Streamlit dashboard for interactive analysis
- Comprehensive test suite
"""

__version__ = "1.0.0"
__author__ = "Crypto Insight"

from .core import (
    BitvavoAPIException,
    InvalidAPIKeyError,
    PurchaseLot,
    RateLimitExceededError,
    TransferSummary,
    analyze_transfers,
    calculate_discrepancy_breakdown,
    calculate_pnl,
    fetch_deposit_history,
    fetch_trade_history,
    fetch_withdrawal_history,
    reconcile_portfolio_balances,
    sync_time,
)

__all__ = [
    "PurchaseLot",
    "calculate_pnl",
    "fetch_trade_history",
    "sync_time",
    "BitvavoAPIException",
    "InvalidAPIKeyError",
    "RateLimitExceededError",
]
