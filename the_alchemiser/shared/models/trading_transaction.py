"""Business Unit: shared | Status: current.

Trading transaction model for recording completed trades and their details.

Provides a data model for storing trading transaction information
including execution details, pricing, and metadata.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TradingTransaction(BaseModel):
    """Model representing a completed trading transaction.
    
    Records the details of a completed trade including symbol, side,
    quantity, price, and execution timestamp for transaction tracking
    and audit purposes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize a trading transaction.

        Args:
            **data: Transaction data including transaction_id, symbol, side,
                   quantity, price, executed_at, and optional fields

        """
        super().__init__(**data)

    # Transaction identification
    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    
    # Trade details
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    side: Literal["BUY", "SELL"] = Field(..., description="Transaction side")
    quantity: Decimal = Field(..., gt=0, description="Quantity transacted")
    price: Decimal = Field(..., gt=0, description="Price per unit")
    
    # Execution details
    executed_at: datetime = Field(..., description="Execution timestamp")
    
    # Optional fields
    order_id: str | None = Field(default=None, description="Associated order ID")
    portfolio_id: str | None = Field(default=None, description="Portfolio identifier")
    strategy_id: str | None = Field(default=None, description="Strategy identifier")
    
    @property
    def total_value(self) -> Decimal:
        """Calculate total transaction value."""
        return self.quantity * self.price

    def __str__(self) -> str:
        """Return string representation of the trading transaction.

        Returns a formatted string containing the key transaction details
        including symbol, side, quantity, price, and execution timestamp
        for human-readable display and logging purposes.

        Returns:
            Formatted string representation of the transaction

        """
        return (
            f"TradingTransaction({self.side} {self.quantity} {self.symbol} "
            f"@ ${self.price} on {self.executed_at.strftime('%Y-%m-%d %H:%M:%S')})"
        )