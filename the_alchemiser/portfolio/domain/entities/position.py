"""Business Unit: portfolio assessment & management | Status: current

Position entity for portfolio holdings.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.shared_kernel.value_objects.money import Money


@dataclass
class Position:
    """Position entity representing a holding in the portfolio."""
    symbol: Symbol
    quantity: Decimal
    average_cost: Money
    current_value: Money
    unrealized_pnl: Money
    market_price: Money
    last_updated: datetime
    
    def __post_init__(self) -> None:
        """Validate position data.
        
        TODO: Add more comprehensive validation rules
        FIXME: Consider adding validation for currency consistency
        """
        if self.quantity < Decimal('0'):
            raise ValueError("Quantity cannot be negative")
        if self.average_cost.amount < Decimal('0'):
            raise ValueError("Average cost cannot be negative")
    
    @property
    def cost_basis(self) -> Money:
        """Calculate total cost basis of the position.
        
        TODO: Consider impact of stock splits and dividends on cost basis
        """
        return Money(self.average_cost.amount * self.quantity, self.average_cost.currency)
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable."""
        return self.unrealized_pnl.amount > Decimal('0')