"""Business Unit: utilities; Status: current.

Portfolio rebalancing decision policy.

This module houses pure functions that decide how a portfolio should be
rebalanced based on target allocations and current positions.  The functions
contain no side effects and are fully typed to enable straightforward unit
testing.
"""

from __future__ import annotations

from collections.abc import Mapping

from the_alchemiser.shared.value_objects.core_types import OrderDetails, PositionsDict


def calculate_rebalance_orders(
    target_allocations: Mapping[str, float],
    current_positions: PositionsDict,
) -> list[OrderDetails]:
    """Calculate required orders to rebalance a portfolio.

    The current implementation is a placeholder returning an empty list.  The
    function will be expanded to generate a list of :class:`OrderDetails`
    representing the trades needed to reach ``target_allocations``.
    """
    # TODO: implement actual rebalancing algorithm
    _ = target_allocations, current_positions
    return []
