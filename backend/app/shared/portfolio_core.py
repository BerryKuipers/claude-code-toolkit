"""
Portfolio core logic - shared between backend and original src/ modules.

This module provides a clean interface to the portfolio calculation logic
without requiring sys.path manipulation.
"""

import sys
import os

# Add src to path for importing the original logic
_src_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import the original portfolio logic
try:
    from src.portfolio.core import (
        calculate_pnl,
        fetch_trade_history,
        get_current_price,
        get_portfolio_assets,
        analyze_transfers,
        reconcile_portfolio_balances,
        PurchaseLot,
        TransferSummary,
    )

    # Re-export for clean imports
    __all__ = [
        "calculate_pnl",
        "fetch_trade_history",
        "get_current_price",
        "get_portfolio_assets",
        "analyze_transfers",
        "reconcile_portfolio_balances",
        "PurchaseLot",
        "TransferSummary",
    ]

except ImportError as e:
    # Fallback for when src/ is not available
    def calculate_pnl(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    def fetch_trade_history(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    def get_current_price(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    def get_portfolio_assets(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    def analyze_transfers(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    def reconcile_portfolio_balances(*args, **kwargs):
        raise NotImplementedError("Portfolio core logic not available")

    class PurchaseLot:
        pass

    class TransferSummary:
        pass
