from __future__ import annotations

from dataclasses import dataclass

from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_type import OrderType
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.side import Side
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce


@dataclass(frozen=True)
class OrderRequest:
    """Domain value object for order requests.

    Immutable value object representing an order request with all required
    fields for trading. Uses strongly-typed domain value objects for
    validation and type safety.
    """

    symbol: Symbol
    side: Side
    quantity: Quantity
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Money | None = None
    client_order_id: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - validation logic
        # Validate limit price is provided for limit orders
        if self.order_type.value == "limit" and self.limit_price is None:
            raise ValueError("Limit price is required for limit orders")

        # Validate limit price is not provided for market orders (optional constraint)
        if self.order_type.value == "market" and self.limit_price is not None:
            raise ValueError("Limit price should not be provided for market orders")

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.side.value == "buy"

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.side.value == "sell"

    @property
    def is_market_order(self) -> bool:
        """Check if this is a market order."""
        return self.order_type.value == "market"

    @property
    def is_limit_order(self) -> bool:
        """Check if this is a limit order."""
        return self.order_type.value == "limit"
