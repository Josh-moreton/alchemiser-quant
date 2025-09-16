"""Business Unit: shared | Status: current.

Trade model definitions for The Alchemiser trading system.

This module contains the Trade class that represents individual trade transactions
with methods for creating, updating, and serializing trade data.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.value_objects.symbol import Symbol


class Trade:
    """Represents an individual trade transaction in the trading system.
    
    The Trade class encapsulates all information about a single trade including
    entry/exit points, quantities, pricing, and fill tracking. It provides
    methods for updating trade state and converting to/from serializable formats.
    """

    def __init__(
        self,
        symbol: Symbol | str,
        quantity: Decimal | float,
        entry_price: Money | Decimal | float,
        trade_type: str = "BUY",
        *,
        trade_id: str | None = None,
        exit_price: Money | Decimal | float | None = None,
        fill_quantity: Decimal | float = Decimal("0"),
        status: str = "PENDING",
    ) -> None:
        """Initialize a new Trade instance.
        
        Args:
            symbol: The trading symbol (e.g., 'AAPL', 'SPY')
            quantity: The number of shares/contracts to trade
            entry_price: The price at which the trade was entered
            trade_type: The type of trade ('BUY' or 'SELL')
            trade_id: Optional unique identifier for the trade
            exit_price: The price at which the trade was/will be exited
            fill_quantity: The quantity that has been filled so far
            status: Current status of the trade ('PENDING', 'FILLED', 'CANCELED')

        """
        self.symbol = Symbol(symbol) if isinstance(symbol, str) else symbol
        self.quantity = Decimal(str(quantity))
        self.entry_price = Money(entry_price) if not isinstance(entry_price, Money) else entry_price
        self.trade_type = trade_type
        self.trade_id = trade_id
        self.exit_price = Money(exit_price) if exit_price and not isinstance(exit_price, Money) else exit_price
        self.fill_quantity = Decimal(str(fill_quantity))
        self.status = status

    def __str__(self) -> str:
        """Return a human-readable string representation of the trade."""
        return (
            f"Trade({self.trade_type} {self.quantity} {self.symbol} "
            f"@ {self.entry_price}, Status: {self.status})"
        )

    def update(
        self,
        *,
        quantity: Decimal | float | None = None,
        entry_price: Money | Decimal | float | None = None,
        exit_price: Money | Decimal | float | None = None,
        status: str | None = None,
        fill_quantity: Decimal | float | None = None,
    ) -> None:
        """Update the trade with new information.
        
        Args:
            quantity: New quantity for the trade
            entry_price: New entry price for the trade
            exit_price: New exit price for the trade
            status: New status for the trade
            fill_quantity: New fill quantity for the trade

        """
        if quantity is not None:
            self.quantity = Decimal(str(quantity))
        if entry_price is not None:
            self.entry_price = Money(entry_price) if not isinstance(entry_price, Money) else entry_price
        if exit_price is not None:
            self.exit_price = Money(exit_price) if not isinstance(exit_price, Money) else exit_price
        if status is not None:
            self.status = status
        if fill_quantity is not None:
            self.fill_quantity = Decimal(str(fill_quantity))

    def to_dict(self) -> dict[str, Any]:
        """Convert the trade to a dictionary representation.
        
        Returns:
            Dictionary containing all trade data in serializable format

        """
        return {
            "symbol": str(self.symbol),
            "quantity": str(self.quantity),
            "entry_price": str(self.entry_price.amount),
            "trade_type": self.trade_type,
            "trade_id": self.trade_id,
            "exit_price": str(self.exit_price.amount) if self.exit_price else None,
            "fill_quantity": str(self.fill_quantity),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trade:
        """Create a Trade instance from a dictionary representation.
        
        Args:
            data: Dictionary containing trade data
            
        Returns:
            Trade instance created from the dictionary data

        """
        return cls(
            symbol=data["symbol"],
            quantity=Decimal(data["quantity"]),
            entry_price=Decimal(data["entry_price"]),
            trade_type=data.get("trade_type", "BUY"),
            trade_id=data.get("trade_id"),
            exit_price=Decimal(data["exit_price"]) if data.get("exit_price") else None,
            fill_quantity=Decimal(data.get("fill_quantity", "0")),
            status=data.get("status", "PENDING"),
        )

    def apply_fill(
        self,
        fill_quantity: Decimal | float,
        fill_price: Money | Decimal | float,
    ) -> None:
        """Apply a partial or complete fill to the trade.
        
        Args:
            fill_quantity: The quantity that was filled
            fill_price: The price at which the fill occurred

        """
        fill_qty = Decimal(str(fill_quantity))
        self.fill_quantity += fill_qty
        
        # Update status based on fill completion
        if self.fill_quantity >= self.quantity:
            self.status = "FILLED"
        elif self.fill_quantity > Decimal("0"):
            self.status = "PARTIALLY_FILLED"
        
        # Update entry price with weighted average if this is an entry fill
        if self.trade_type in ("BUY", "SELL") and fill_qty > Decimal("0"):
            fill_price_money = Money(fill_price) if not isinstance(fill_price, Money) else fill_price
            
            # Calculate weighted average entry price
            total_cost = (self.entry_price.amount * (self.fill_quantity - fill_qty) + 
                         fill_price_money.amount * fill_qty)
            self.entry_price = Money(total_cost / self.fill_quantity)