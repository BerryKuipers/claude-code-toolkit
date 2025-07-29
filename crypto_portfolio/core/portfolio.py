"""
Core portfolio calculation logic using FIFO accounting.

Provides high-precision FIFO P&L calculations with proper decimal arithmetic
and comprehensive error handling.
"""

import logging
from collections import deque
from decimal import Decimal, getcontext
from typing import Dict, List, Deque

from ..models.portfolio import PurchaseLot
from .exceptions import CalculationError, DataValidationError

logger = logging.getLogger(__name__)

# Set high precision for Decimal calculations
getcontext().prec = 28


class PortfolioCalculator:
    """
    Core portfolio calculation engine using FIFO accounting.
    
    Provides high-precision calculations for P&L analysis, cost basis tracking,
    and portfolio performance metrics using FIFO (First-In-First-Out) accounting.
    """
    
    @staticmethod
    def _decimal(value: str) -> Decimal:
        """Convert string to Decimal with error handling."""
        try:
            return Decimal(str(value))
        except (ValueError, TypeError) as e:
            raise DataValidationError(f"Invalid decimal value: {value}") from e
    
    def calculate_pnl(self, trades: List[Dict[str, str]], current_price: Decimal) -> Dict[str, Decimal]:
        """
        Process trades using FIFO accounting and return P&L metrics.
        
        Args:
            trades: List of trade dictionaries with keys: side, amount, price, fee, timestamp
            current_price: Current market price for unrealized P&L calculation
            
        Returns:
            Dictionary with keys:
            - amount: Remaining crypto amount
            - cost_eur: Remaining cost basis in EUR
            - value_eur: Current market value in EUR
            - realised_eur: Realized P&L in EUR
            - unrealised_eur: Unrealized P&L in EUR
            - total_buys_eur: Total amount invested (for return % calculation)
            
        Raises:
            CalculationError: If calculation fails
            DataValidationError: If input data is invalid
        """
        try:
            lots: Deque[PurchaseLot] = deque()
            realised_eur = Decimal("0")
            total_buys_eur = Decimal("0")  # denominator for true return %
            
            for trade in trades:
                try:
                    amt = self._decimal(trade["amount"])
                    price = self._decimal(trade["price"])
                    fee = self._decimal(trade.get("fee", "0"))
                    side = trade["side"].lower()
                    ts = int(trade.get("timestamp", "0"))
                except (KeyError, ValueError) as e:
                    raise DataValidationError(f"Invalid trade data: {trade}") from e
                
                if side == "buy":
                    cost = amt * price + fee
                    total_buys_eur += cost
                    lots.append(PurchaseLot(amount=amt, cost_eur=cost, timestamp=ts))
                    
                elif side == "sell":
                    proceeds = amt * price - fee
                    sold_left = amt
                    cost_basis = Decimal("0")
                    
                    while sold_left > 0 and lots:
                        lot = lots[0]
                        if lot.amount <= sold_left:
                            # Consume entire lot
                            cost_basis += lot.cost_eur
                            sold_left -= lot.amount
                            lots.popleft()
                        else:
                            # Partial lot consumption
                            consumed_cost = lot.cost_eur * (sold_left / lot.amount)
                            cost_basis += consumed_cost
                            lot.amount -= sold_left
                            lot.cost_eur -= consumed_cost
                            sold_left = Decimal("0")
                    
                    if sold_left > 0:
                        logger.warning(f"Sold more than available: {sold_left} remaining")
                    
                    realised_eur += proceeds - cost_basis
            
            # Calculate remaining position
            remaining_amount = sum(lot.amount for lot in lots)
            remaining_cost = sum(lot.cost_eur for lot in lots)
            current_value = remaining_amount * current_price
            unrealised_eur = current_value - remaining_cost
            
            return {
                "amount": remaining_amount,
                "cost_eur": remaining_cost,
                "value_eur": current_value,
                "realised_eur": realised_eur,
                "unrealised_eur": unrealised_eur,
                "total_buys_eur": total_buys_eur,
            }
            
        except Exception as e:
            if isinstance(e, (DataValidationError, CalculationError)):
                raise
            raise CalculationError(f"Failed to calculate P&L: {e}") from e
    
    def calculate_portfolio_totals(self, asset_pnl_data: Dict[str, Dict[str, Decimal]]) -> Dict[str, Decimal]:
        """
        Calculate portfolio-wide totals from individual asset P&L data.
        
        Args:
            asset_pnl_data: Dictionary mapping asset symbols to their P&L data
            
        Returns:
            Dictionary with portfolio totals:
            - total_value: Total portfolio value
            - total_cost: Total cost basis
            - total_realized_pnl: Total realized P&L
            - total_unrealized_pnl: Total unrealized P&L
            - total_pnl: Total P&L (realized + unrealized)
            - total_return_percentage: Total return percentage
            - asset_count: Number of assets with holdings
        """
        try:
            totals = {
                "total_value": Decimal("0"),
                "total_cost": Decimal("0"),
                "total_realized_pnl": Decimal("0"),
                "total_unrealized_pnl": Decimal("0"),
                "asset_count": 0,
            }
            
            for asset, pnl_data in asset_pnl_data.items():
                if pnl_data.get("amount", Decimal("0")) > 0:  # Only count assets with holdings
                    totals["total_value"] += pnl_data.get("value_eur", Decimal("0"))
                    totals["total_cost"] += pnl_data.get("cost_eur", Decimal("0"))
                    totals["total_realized_pnl"] += pnl_data.get("realised_eur", Decimal("0"))
                    totals["total_unrealized_pnl"] += pnl_data.get("unrealised_eur", Decimal("0"))
                    totals["asset_count"] += 1
            
            totals["total_pnl"] = totals["total_realized_pnl"] + totals["total_unrealized_pnl"]
            totals["total_return_percentage"] = (
                (totals["total_pnl"] / totals["total_cost"] * 100)
                if totals["total_cost"] > 0
                else Decimal("0")
            )
            
            return totals
            
        except Exception as e:
            raise CalculationError(f"Failed to calculate portfolio totals: {e}") from e
    
    def calculate_asset_percentage(self, asset_value: Decimal, total_portfolio_value: Decimal) -> Decimal:
        """Calculate an asset's percentage of the total portfolio."""
        try:
            if total_portfolio_value <= 0:
                return Decimal("0")
            return (asset_value / total_portfolio_value) * 100
        except Exception as e:
            raise CalculationError(f"Failed to calculate asset percentage: {e}") from e
    
    def calculate_return_percentage(self, pnl: Decimal, cost_basis: Decimal) -> Decimal:
        """Calculate return percentage for an asset or portfolio."""
        try:
            if cost_basis <= 0:
                return Decimal("0")
            return (pnl / cost_basis) * 100
        except Exception as e:
            raise CalculationError(f"Failed to calculate return percentage: {e}") from e
