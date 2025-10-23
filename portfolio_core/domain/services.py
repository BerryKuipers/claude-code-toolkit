"""
Domain Services

Business logic that doesn't naturally fit within entities.
Contains the core FIFO calculation logic - the SINGLE SOURCE OF TRUTH.
"""

import logging
from collections import deque
from decimal import Decimal
from typing import Dict, List, Deque, Tuple, Optional

from .entities import Asset, Portfolio, PurchaseLot, Trade
from .value_objects import Money, AssetSymbol, AssetAmount, TradeType, Timestamp

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class FIFOCalculationService:
    """
    FIFO calculation service - SINGLE SOURCE OF TRUTH for all FIFO calculations.
    
    This service contains the core business logic for First-In-First-Out
    accounting calculations. All other parts of the system MUST use this
    service for FIFO calculations to maintain consistency.
    """
    
    def calculate_asset_pnl(self, trades: List[Trade], current_price: Money,
                           deposits: Optional[List[Dict]] = None) -> Dict[str, Decimal]:
        """
        Calculate P&L for an asset using FIFO accounting.
        
        This is the SINGLE SOURCE OF TRUTH for FIFO P&L calculations.
        
        Args:
            trades: List of trades sorted by timestamp (oldest first)
            current_price: Current market price per unit
            
        Returns:
            Dictionary with P&L metrics:
            - amount: Remaining asset amount
            - cost_eur: Remaining cost basis in EUR
            - value_eur: Current market value in EUR
            - realised_eur: Realized P&L in EUR
            - unrealised_eur: Unrealized P&L in EUR
            - total_buys_eur: Total amount invested
        """
        if not trades:
            return self._create_empty_pnl_result()
        
        # Validate all trades are for the same asset
        asset_symbol = trades[0].asset
        for trade in trades:
            if trade.asset != asset_symbol:
                raise ValueError(f"All trades must be for the same asset. Found {trade.asset} and {asset_symbol}")
        
        # Sort trades by timestamp to ensure FIFO order
        sorted_trades = sorted(trades, key=lambda t: t.timestamp.value)

        # Initialize FIFO lots queue and tracking variables
        lots: Deque[PurchaseLot] = deque()
        realized_pnl = Money.zero(current_price.currency)
        total_invested = Money.zero(current_price.currency)

        # Process deposits as zero-cost purchases to account for external transfers
        if deposits:
            for deposit in deposits:
                if deposit.get("status") == "completed":
                    try:
                        amount = Decimal(str(deposit.get("amount", "0")))
                        timestamp = int(deposit.get("timestamp", "0"))

                        if amount > 0:
                            # Create zero-cost purchase lot for deposit
                            deposit_amount = AssetAmount(amount, asset_symbol)
                            deposit_cost = Money.zero(current_price.currency)
                            deposit_lot = PurchaseLot(
                                amount=deposit_amount,
                                cost=deposit_cost,
                                timestamp=Timestamp(timestamp)
                            )
                            lots.append(deposit_lot)

                            logger.info(
                                f"Added deposit as zero-cost lot for {asset_symbol}: "
                                f"amount={amount}, timestamp={timestamp}"
                            )
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping invalid deposit data: {e}")
                        continue
        
        # Process each trade
        for trade in sorted_trades:
            if trade.trade_type == TradeType.BUY:
                # Add new lot to the queue
                total_cost = trade.get_total_cost()
                total_invested = total_invested + total_cost

                lot = PurchaseLot(
                    amount=trade.amount,
                    cost=total_cost,
                    timestamp=trade.timestamp
                )
                lots.append(lot)
                
            elif trade.trade_type == TradeType.SELL:
                # Consume lots using FIFO
                proceeds = trade.get_proceeds()
                cost_basis = Money.zero(current_price.currency)
                remaining_to_sell = trade.amount
                
                while remaining_to_sell.is_positive() and lots:
                    lot = lots[0]
                    
                    if lot.amount.amount <= remaining_to_sell.amount:
                        # Consume entire lot
                        cost_basis = cost_basis + lot.cost
                        remaining_to_sell = remaining_to_sell - lot.amount
                        lots.popleft()
                    else:
                        # Partial lot consumption
                        consume_amount = remaining_to_sell
                        proportion = consume_amount.amount / lot.amount.amount
                        consumed_cost = lot.cost * proportion
                        cost_basis = cost_basis + consumed_cost
                        
                        # Update lot with remaining amount
                        remaining_lot = lot.consume(consume_amount)
                        lots[0] = remaining_lot
                        remaining_to_sell = AssetAmount.zero(asset_symbol)
                
                # Calculate realized P&L for this sell
                trade_pnl = Money(proceeds.amount - cost_basis.amount, proceeds.currency)
                realized_pnl = realized_pnl + trade_pnl
                
                if remaining_to_sell.is_positive():
                    # Define tolerance thresholds for micro-discrepancies
                    MICRO_TOLERANCE = Decimal("0.01")  # Ignore discrepancies < 0.01
                    MINOR_TOLERANCE = Decimal("0.1")   # Log warnings for 0.01-0.1

                    if remaining_to_sell.amount < MICRO_TOLERANCE:
                        # Micro-discrepancy: likely precision/rounding artifact
                        logger.debug(
                            f"Micro-discrepancy in {asset_symbol}: {remaining_to_sell.amount}. "
                            f"Likely precision artifact from exchange API. "
                            f"Trade timestamp: {trade.timestamp.value}, amount: {trade.amount.amount}"
                        )
                        # Don't create synthetic lot for micro-discrepancies

                    elif remaining_to_sell.amount < MINOR_TOLERANCE:
                        # Minor discrepancy: log as warning but don't create synthetic lot
                        logger.warning(
                            f"Minor discrepancy in {asset_symbol}: {remaining_to_sell.amount}. "
                            f"Possible timing/precision issue. "
                            f"Trade timestamp: {trade.timestamp.value}, amount: {trade.amount.amount}"
                        )

                    else:
                        # Significant discrepancy: create synthetic lot and log as error
                        logger.error(
                            f"Significant overselling in {asset_symbol}: {remaining_to_sell.amount}. "
                            f"This indicates missing trade/deposit data. "
                            f"Trade timestamp: {trade.timestamp.value}, amount: {trade.amount.amount}"
                        )

                        # Create a synthetic purchase lot for significant discrepancies only
                        synthetic_cost = Money(
                            remaining_to_sell.amount * trade.price.amount,
                            trade.price.currency
                        )
                        synthetic_lot = PurchaseLot(
                            amount=remaining_to_sell,
                            cost=synthetic_cost,
                            timestamp=Timestamp(trade.timestamp.value - 1)  # Slightly earlier
                        )
                        lots.append(synthetic_lot)

                        logger.info(
                            f"Created synthetic purchase lot for {asset_symbol}: "
                            f"amount={remaining_to_sell.amount}, cost={synthetic_cost.amount}"
                        )
        
        # Calculate remaining position
        remaining_amount = sum(lot.amount.amount for lot in lots)
        remaining_cost = sum(lot.cost.amount for lot in lots)
        current_value = remaining_amount * current_price.amount
        unrealized_pnl = current_value - remaining_cost
        
        return {
            "amount": remaining_amount,
            "cost_eur": remaining_cost,
            "value_eur": current_value,
            "realised_eur": realized_pnl.amount,
            "unrealised_eur": unrealized_pnl,
            "total_buys_eur": total_invested.amount,
        }
    
    def _create_empty_pnl_result(self) -> Dict[str, Decimal]:
        """Create empty P&L result for assets with no trades."""
        return {
            "amount": Decimal("0"),
            "cost_eur": Decimal("0"),
            "value_eur": Decimal("0"),
            "realised_eur": Decimal("0"),
            "unrealised_eur": Decimal("0"),
            "total_buys_eur": Decimal("0"),
        }


class PortfolioCalculationService:
    """
    Portfolio-level calculation service.
    
    Orchestrates FIFO calculations across multiple assets and provides
    portfolio-wide metrics and analysis.
    """
    
    def __init__(self, fifo_service: FIFOCalculationService):
        """Initialize with FIFO calculation service."""
        self.fifo_service = fifo_service
    
    def calculate_portfolio_totals(self, asset_pnl_data: Dict[str, Dict[str, Decimal]]) -> Dict[str, Decimal]:
        """
        Calculate portfolio-wide totals from individual asset P&L data.
        
        Args:
            asset_pnl_data: Dictionary mapping asset symbols to their P&L data
            
        Returns:
            Dictionary with portfolio totals
        """
        totals = {
            "total_value": Decimal("0"),
            "total_cost": Decimal("0"),
            "total_realized_pnl": Decimal("0"),
            "total_unrealized_pnl": Decimal("0"),
            "asset_count": 0,
        }
        
        for asset_symbol, pnl_data in asset_pnl_data.items():
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
    
    def calculate_asset_allocation(self, asset_value: Decimal, total_portfolio_value: Decimal) -> Decimal:
        """Calculate an asset's percentage allocation in the portfolio."""
        if total_portfolio_value <= 0:
            return Decimal("0")
        return (asset_value / total_portfolio_value) * 100
    
    def update_portfolio_from_trades(self, portfolio: Portfolio, trades_by_asset: Dict[AssetSymbol, List[Trade]],
                                   current_prices: Dict[AssetSymbol, Money],
                                   deposits_by_asset: Optional[Dict[AssetSymbol, List[Dict]]] = None) -> Portfolio:
        """
        Update portfolio entities based on trade data using FIFO calculations.
        
        Args:
            portfolio: Portfolio to update
            trades_by_asset: Dictionary mapping asset symbols to their trades
            current_prices: Dictionary mapping asset symbols to current prices
            
        Returns:
            Updated portfolio with calculated holdings and P&L
        """
        for asset_symbol, trades in trades_by_asset.items():
            if not trades:
                continue
            
            current_price = current_prices.get(asset_symbol)
            if not current_price:
                logger.warning(f"No current price available for {asset_symbol}")
                continue
            
            # Get deposits for this asset if available
            deposits = deposits_by_asset.get(asset_symbol, []) if deposits_by_asset else []

            # Calculate P&L using FIFO service with deposit data
            pnl_data = self.fifo_service.calculate_asset_pnl(trades, current_price, deposits)
            
            # Get or create asset in portfolio
            asset = portfolio.get_asset(asset_symbol)
            if not asset:
                asset = Asset(
                    symbol=asset_symbol,
                    current_price=current_price,
                    holdings=AssetAmount(pnl_data["amount"], asset_symbol),
                    cost_basis=Money(pnl_data["cost_eur"]),
                    realized_pnl=Money(pnl_data["realised_eur"])
                )
                portfolio.add_asset(asset)
            else:
                # Update existing asset
                asset.current_price = current_price
                asset.holdings = AssetAmount(pnl_data["amount"], asset_symbol)
                asset.cost_basis = Money(pnl_data["cost_eur"])
                asset.realized_pnl = Money(pnl_data["realised_eur"])
        
        return portfolio
    
    def analyze_portfolio_performance(self, portfolio: Portfolio) -> Dict[str, any]:
        """
        Analyze portfolio performance and provide comprehensive metrics.
        
        Args:
            portfolio: Portfolio to analyze
            
        Returns:
            Dictionary with performance analysis
        """
        total_value = portfolio.get_total_value()
        total_cost = portfolio.get_total_cost_basis()
        total_pnl = portfolio.get_total_pnl()
        return_pct = portfolio.get_return_percentage()
        
        # Asset allocation analysis
        asset_allocations = []
        for asset in portfolio.assets:
            if asset.holdings.is_positive():
                asset_value = asset.get_current_value()
                allocation_pct = self.calculate_asset_allocation(asset_value.amount, total_value.amount)
                
                asset_allocations.append({
                    "symbol": str(asset.symbol),
                    "value": asset_value.amount,
                    "allocation_percentage": allocation_pct,
                    "return_percentage": asset.get_return_percentage(),
                })
        
        # Sort by allocation percentage
        asset_allocations.sort(key=lambda x: x["allocation_percentage"], reverse=True)
        
        return {
            "total_value": total_value.amount,
            "total_cost_basis": total_cost.amount,
            "total_pnl": total_pnl.amount,
            "return_percentage": return_pct,
            "asset_count": portfolio.get_asset_count(),
            "asset_allocations": asset_allocations,
        }
