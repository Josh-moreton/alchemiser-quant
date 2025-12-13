"""Business Unit: execution | Status: current.

Order intent abstraction for unified order placement.

Provides clear semantics for different order types with type-safe enums.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal


class OrderSide(str, Enum):
    """Order side: BUY or SELL."""

    BUY = "BUY"
    SELL = "SELL"

    def to_alpaca(self) -> Literal["buy", "sell"]:
        """Convert to Alpaca API format (lowercase)."""
        return self.value.lower()  # type: ignore[return-value]


class CloseType(str, Enum):
    """Type of position close operation."""

    NONE = "NONE"  # Not a close operation (regular buy or partial sell)
    PARTIAL = "PARTIAL"  # Reduce position size but don't close fully
    FULL = "FULL"  # Fully close position

    def is_closing(self) -> bool:
        """Check if this is any type of close operation."""
        return self in (CloseType.PARTIAL, CloseType.FULL)


class Urgency(str, Enum):
    """Order urgency level affecting execution strategy."""

    LOW = "LOW"  # Use full walk-the-book strategy for best price
    MEDIUM = "MEDIUM"  # Use abbreviated walk-the-book
    HIGH = "HIGH"  # Use market order immediately


@dataclass(frozen=True)
class OrderIntent:
    """Encodes the intent of an order with clear semantics.

    This provides a single, type-safe abstraction for order types that:
    - Clearly distinguishes BUY vs SELL_PARTIAL vs SELL_FULL
    - Captures urgency for execution strategy selection
    - Provides single translation point to Alpaca API parameters
    - Supports client order IDs for enhanced tracking

    Examples:
        >>> # Regular buy order
        >>> intent = OrderIntent(
        ...     side=OrderSide.BUY,
        ...     close_type=CloseType.NONE,
        ...     symbol="AAPL",
        ...     quantity=Decimal("10"),
        ...     urgency=Urgency.MEDIUM
        ... )

        >>> # Partial sell (reduce position)
        >>> intent = OrderIntent(
        ...     side=OrderSide.SELL,
        ...     close_type=CloseType.PARTIAL,
        ...     symbol="AAPL",
        ...     quantity=Decimal("5"),
        ...     urgency=Urgency.LOW
        ... )

        >>> # Full close with custom client order ID
        >>> intent = OrderIntent(
        ...     side=OrderSide.SELL,
        ...     close_type=CloseType.FULL,
        ...     symbol="AAPL",
        ...     quantity=Decimal("10"),  # Full position size
        ...     urgency=Urgency.HIGH,
        ...     client_order_id="custom-AAPL-12345"
        ... )

    """

    side: OrderSide
    close_type: CloseType
    symbol: str
    quantity: Decimal
    urgency: Urgency
    correlation_id: str | None = None
    client_order_id: str | None = None

    def __post_init__(self) -> None:
        """Validate order intent after initialization."""
        # Validate quantity is positive
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")

        # Validate symbol is not empty
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")

        # Validate close_type is consistent with side
        if self.close_type.is_closing() and self.side != OrderSide.SELL:
            raise ValueError(
                f"Close operations must use SELL side, got {self.side} with {self.close_type}"
            )

    @property
    def is_full_close(self) -> bool:
        """Check if this is a full position close."""
        return self.close_type == CloseType.FULL

    @property
    def is_partial_close(self) -> bool:
        """Check if this is a partial position close."""
        return self.close_type == CloseType.PARTIAL

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side == OrderSide.BUY

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side == OrderSide.SELL

    def to_alpaca_params(self) -> dict[str, str | float | bool]:
        """Convert to Alpaca API parameters.

        This is the single translation point from our internal order intent
        to Alpaca's actual order API parameters.

        Returns:
            Dictionary of parameters for Alpaca order submission

        Note:
            client_order_id is intentionally NOT included in this method as it
            needs to be passed separately to the OrderRequest constructor.

        """
        return {
            "symbol": self.symbol,
            "side": self.side.to_alpaca(),
            "qty": float(self.quantity),
            "is_complete_exit": self.is_full_close,
        }

    def describe(self) -> str:
        """Human-readable description of this order intent."""
        if self.is_full_close:
            return f"CLOSE {self.symbol} (full exit of {self.quantity} shares)"
        if self.is_partial_close:
            return f"REDUCE {self.symbol} by {self.quantity} shares"
        if self.is_buy:
            return f"BUY {self.quantity} shares of {self.symbol}"
        return f"SELL {self.quantity} shares of {self.symbol}"
