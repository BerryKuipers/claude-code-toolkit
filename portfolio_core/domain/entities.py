"""
Domain Entities

Core business entities that encapsulate business rules and behavior.
These are the heart of the domain model.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from .value_objects import Money, AssetSymbol, AssetAmount, TradeType, Timestamp


@dataclass
class PurchaseLot:
    """
    Purchase lot entity for FIFO calculations.

    Represents a specific purchase of an asset that can be consumed
    during sell operations using FIFO accounting.
    """
    amount: AssetAmount
    cost: Money
    timestamp: Timestamp
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Validate purchase lot after initialization."""
        if self.amount.is_zero():
            raise ValueError("Purchase lot amount cannot be zero")
        
        # Allow zero cost (for airdrops, rewards) but not negative cost
        from decimal import Decimal
        if self.cost.amount < Decimal('0'):
            raise ValueError("Purchase lot cost cannot be negative")
    
    def consume(self, consume_amount: AssetAmount) -> 'PurchaseLot':
        """
        Consume part of this lot and return the remaining lot.
        
        Args:
            consume_amount: Amount to consume from this lot
            
        Returns:
            New PurchaseLot with remaining amount and proportional cost
            
        Raises:
            ValueError: If consume amount is invalid
        """
        if consume_amount.asset != self.amount.asset:
            raise ValueError("Cannot consume different asset from lot")
        
        if consume_amount.amount > self.amount.amount:
            raise ValueError("Cannot consume more than available in lot")
        
        if consume_amount.is_zero():
            return self
        
        # Calculate proportional cost
        proportion = consume_amount.amount / self.amount.amount
        consumed_cost = self.cost * proportion
        
        # Return new lot with remaining amount and cost
        remaining_amount = self.amount - consume_amount
        remaining_cost = self.cost - consumed_cost
        
        return PurchaseLot(
            id=self.id,
            amount=remaining_amount,
            cost=remaining_cost,
            timestamp=self.timestamp
        )
    
    def get_cost_per_unit(self) -> Money:
        """Get the cost per unit for this lot."""
        if self.amount.is_zero():
            return Money.zero(self.cost.currency)
        return self.cost / self.amount.amount


@dataclass
class Trade:
    """
    Trade entity representing a buy or sell transaction.

    Core business entity that encapsulates all trade information
    and business rules.
    """
    asset: AssetSymbol
    trade_type: TradeType
    amount: AssetAmount
    price: Money  # Price per unit
    fee: Money
    timestamp: Timestamp
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Validate trade after initialization."""
        if self.amount.asset != self.asset:
            raise ValueError("Trade amount asset must match trade asset")
        
        if self.amount.is_zero():
            raise ValueError("Trade amount cannot be zero")
        
        if not self.price.is_positive():
            raise ValueError("Trade price must be positive")
        
        # Note: Fees can be negative (rebates/maker fees), so we don't validate this
        # if self.fee.amount < 0:
        #     raise ValueError("Trade fee cannot be negative")
    
    def get_total_cost(self) -> Money:
        """
        Get total cost of the trade including fees.
        
        For buy trades: (amount * price) + fee
        For sell trades: (amount * price) - fee
        """
        base_value = Money(self.amount.amount * self.price.amount, self.price.currency)
        
        if self.trade_type == TradeType.BUY:
            return base_value + self.fee
        else:  # SELL
            return base_value - self.fee
    
    def get_proceeds(self) -> Money:
        """Get proceeds from a sell trade (amount * price - fee)."""
        if self.trade_type != TradeType.SELL:
            raise ValueError("Can only get proceeds from sell trades")
        
        base_value = Money(self.amount.amount * self.price.amount, self.price.currency)
        return base_value - self.fee


@dataclass
class Asset:
    """
    Asset entity representing a cryptocurrency or financial instrument.
    
    Contains current holdings and provides methods for portfolio calculations.
    """
    symbol: AssetSymbol
    current_price: Money
    holdings: AssetAmount = field(default_factory=lambda: AssetAmount.zero(AssetSymbol("BTC")))
    cost_basis: Money = field(default_factory=lambda: Money.zero())
    realized_pnl: Money = field(default_factory=lambda: Money.zero())
    
    def __post_init__(self):
        """Validate asset after initialization."""
        if self.holdings.asset != self.symbol:
            # Fix the default holdings to match the symbol
            object.__setattr__(self, 'holdings', AssetAmount.zero(self.symbol))
    
    def get_current_value(self) -> Money:
        """Get current market value of holdings."""
        return Money(self.holdings.amount * self.current_price.amount, self.current_price.currency)
    
    def get_unrealized_pnl(self) -> Money:
        """Get unrealized P&L (current value - cost basis)."""
        current_value = self.get_current_value()
        return Money(current_value.amount - self.cost_basis.amount, current_value.currency)
    
    def get_total_pnl(self) -> Money:
        """Get total P&L (realized + unrealized)."""
        unrealized = self.get_unrealized_pnl()
        return Money(self.realized_pnl.amount + unrealized.amount, self.realized_pnl.currency)
    
    def get_return_percentage(self) -> Decimal:
        """Get return percentage based on cost basis."""
        if self.cost_basis.is_zero():
            return Decimal('0')
        
        total_pnl = self.get_total_pnl()
        return (total_pnl.amount / self.cost_basis.amount) * Decimal('100')


@dataclass
class Portfolio:
    """
    Portfolio entity representing a collection of assets.

    Root aggregate that manages all portfolio-level business rules
    and calculations.
    """
    assets: List[Asset] = field(default_factory=list)
    name: str = "Default Portfolio"
    id: UUID = field(default_factory=uuid4)
    
    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the portfolio."""
        # Check if asset already exists
        existing_asset = self.get_asset(asset.symbol)
        if existing_asset:
            raise ValueError(f"Asset {asset.symbol} already exists in portfolio")
        
        self.assets.append(asset)
    
    def get_asset(self, symbol: AssetSymbol) -> Optional[Asset]:
        """Get an asset by symbol."""
        for asset in self.assets:
            if asset.symbol == symbol:
                return asset
        return None
    
    def get_total_value(self) -> Money:
        """Get total portfolio value."""
        if not self.assets:
            return Money.zero()
        
        total = Money.zero(self.assets[0].current_price.currency)
        for asset in self.assets:
            if asset.holdings.is_positive():
                total = total + asset.get_current_value()
        
        return total
    
    def get_total_cost_basis(self) -> Money:
        """Get total portfolio cost basis."""
        if not self.assets:
            return Money.zero()
        
        total = Money.zero(self.assets[0].cost_basis.currency)
        for asset in self.assets:
            if asset.holdings.is_positive():
                total = total + asset.cost_basis
        
        return total
    
    def get_total_realized_pnl(self) -> Money:
        """Get total realized P&L."""
        if not self.assets:
            return Money.zero()
        
        total = Money.zero(self.assets[0].realized_pnl.currency)
        for asset in self.assets:
            total = total + asset.realized_pnl
        
        return total
    
    def get_total_unrealized_pnl(self) -> Money:
        """Get total unrealized P&L."""
        if not self.assets:
            return Money.zero()
        
        total_value = self.get_total_value()
        total_cost = self.get_total_cost_basis()
        
        return Money(total_value.amount - total_cost.amount, total_value.currency)
    
    def get_total_pnl(self) -> Money:
        """Get total P&L (realized + unrealized)."""
        realized = self.get_total_realized_pnl()
        unrealized = self.get_total_unrealized_pnl()
        
        return Money(realized.amount + unrealized.amount, realized.currency)
    
    def get_return_percentage(self) -> Decimal:
        """Get portfolio return percentage."""
        total_cost = self.get_total_cost_basis()
        if total_cost.is_zero():
            return Decimal('0')
        
        total_pnl = self.get_total_pnl()
        return (total_pnl.amount / total_cost.amount) * Decimal('100')
    
    def get_asset_count(self) -> int:
        """Get count of assets with holdings."""
        return sum(1 for asset in self.assets if asset.holdings.is_positive())
