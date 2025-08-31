"""Business Unit: utilities | Status: current.

Anti-corruption layer for Alpaca order transformations.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import PlannedOrderV1
from the_alchemiser.shared_kernel.value_objects.action_type import ActionType


class AlpacaOrderMapper:
    """Maps between domain order objects and Alpaca API requests."""

    def planned_order_to_alpaca_request(self, order: PlannedOrderV1) -> dict[str, Any]:
        """Convert PlannedOrderV1 to Alpaca order request parameters.

        Args:
            order: Planned order from Portfolio context

        Returns:
            Dictionary with Alpaca API parameters

        Raises:
            ValueError: Invalid order data

        """
        # Convert domain side to Alpaca side
        side_map = {ActionType.BUY: "buy", ActionType.SELL: "sell"}

        if order.side not in side_map:
            raise ValueError(f"Invalid order side: {order.side}")

        alpaca_request = {
            "symbol": order.symbol.value,
            "side": side_map[order.side],
            "qty": float(order.quantity),
            "type": "limit" if order.limit_price else "market",
            "time_in_force": "day",
            "client_order_id": str(order.order_id),
        }

        # Add limit price if specified
        if order.limit_price:
            alpaca_request["limit_price"] = float(order.limit_price)

        return alpaca_request
