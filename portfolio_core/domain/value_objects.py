"""
Domain Value Objects

Immutable objects that describe aspects of the domain with built-in validation
and business rules. Following DDD principles for value objects.
"""

from dataclasses import dataclass
from decimal import Decimal, getcontext
from enum import Enum
from typing import Union

# Set high precision for financial calculations
getcontext().prec = 28


class TradeType(Enum):
    """Trade type enumeration."""
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class Money:
    """
    Money value object with currency and amount.
    
    Immutable representation of monetary value with proper decimal precision
    for financial calculations.
    """
    amount: Decimal
    currency: str = "EUR"
    
    def __post_init__(self):
        """Validate money object after initialization."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        # Allow negative amounts for fees, rebates, and PnL calculations
        # Negative amounts are valid in financial contexts (rebates, losses, etc.)
        
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
    
    def __add__(self, other: 'Money') -> 'Money':
        """Add two money objects."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract two money objects."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Subtraction would result in negative money")
        return Money(result_amount, self.currency)
    
    def __mul__(self, multiplier: Union[Decimal, int, float]) -> 'Money':
        """Multiply money by a scalar."""
        if not isinstance(multiplier, Decimal):
            multiplier = Decimal(str(multiplier))
        return Money(self.amount * multiplier, self.currency)
    
    def __truediv__(self, divisor: Union[Decimal, int, float]) -> 'Money':
        """Divide money by a scalar."""
        if not isinstance(divisor, Decimal):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Money(self.amount / divisor, self.currency)
    
    def is_zero(self) -> bool:
        """Check if money amount is zero."""
        return self.amount == Decimal('0')
    
    def is_positive(self) -> bool:
        """Check if money amount is positive."""
        return self.amount > Decimal('0')
    
    @classmethod
    def zero(cls, currency: str = "EUR") -> 'Money':
        """Create zero money object."""
        return cls(Decimal('0'), currency)


@dataclass(frozen=True)
class AssetSymbol:
    """
    Asset symbol value object.
    
    Represents a cryptocurrency or asset symbol with validation.
    """
    symbol: str
    
    def __post_init__(self):
        """Validate asset symbol after initialization."""
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("Asset symbol must be a non-empty string")
        
        # Convert to uppercase for consistency
        object.__setattr__(self, 'symbol', self.symbol.upper())
        
        if len(self.symbol) < 1 or len(self.symbol) > 15:
            raise ValueError("Asset symbol must be between 1 and 15 characters")
    
    def __str__(self) -> str:
        """String representation of asset symbol."""
        return self.symbol


@dataclass(frozen=True)
class Timestamp:
    """
    Timestamp value object for trade timestamps.
    
    Represents a point in time with validation.
    """
    value: int
    
    def __post_init__(self):
        """Validate timestamp after initialization."""
        if not isinstance(self.value, int) or self.value < 0:
            raise ValueError("Timestamp must be a non-negative integer")
    
    def __lt__(self, other: 'Timestamp') -> bool:
        """Compare timestamps for ordering."""
        return self.value < other.value
    
    def __le__(self, other: 'Timestamp') -> bool:
        """Compare timestamps for ordering."""
        return self.value <= other.value
    
    def __gt__(self, other: 'Timestamp') -> bool:
        """Compare timestamps for ordering."""
        return self.value > other.value
    
    def __ge__(self, other: 'Timestamp') -> bool:
        """Compare timestamps for ordering."""
        return self.value >= other.value


@dataclass(frozen=True)
class AssetAmount:
    """
    Asset amount value object.
    
    Represents an amount of a specific asset with proper decimal precision.
    """
    amount: Decimal
    asset: AssetSymbol
    
    def __post_init__(self):
        """Validate asset amount after initialization."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
        
        if self.amount < 0:
            raise ValueError("Asset amount cannot be negative")
    
    def __add__(self, other: 'AssetAmount') -> 'AssetAmount':
        """Add two asset amounts."""
        if self.asset != other.asset:
            raise ValueError(f"Cannot add {self.asset} and {other.asset}")
        return AssetAmount(self.amount + other.amount, self.asset)
    
    def __sub__(self, other: 'AssetAmount') -> 'AssetAmount':
        """Subtract two asset amounts."""
        if self.asset != other.asset:
            raise ValueError(f"Cannot subtract {self.asset} and {other.asset}")
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Subtraction would result in negative asset amount")
        return AssetAmount(result_amount, self.asset)
    
    def is_zero(self) -> bool:
        """Check if asset amount is zero."""
        return self.amount == Decimal('0')
    
    def is_positive(self) -> bool:
        """Check if asset amount is positive."""
        return self.amount > Decimal('0')
    
    @classmethod
    def zero(cls, asset: AssetSymbol) -> 'AssetAmount':
        """Create zero asset amount."""
        return cls(Decimal('0'), asset)
