"""Business Unit: portfolio assessment & management; Status: current.

Pure calculation logic for portfolio rebalancing.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.math.trading_math import calculate_rebalance_amounts
from .rebalance_plan import RebalancePlan


class RebalanceCalculator:
    """Pure calculation logic for portfolio rebalancing.

    This class contains no side effects and only performs calculations.
    It delegates to the existing trading_math module but returns proper domain objects.
    """

    def __init__(self, min_trade_threshold: Decimal = Decimal("0.01")) -> None:
        """Initialize the calculator with a minimum trade threshold.

        Args:
            min_trade_threshold: Minimum weight difference to trigger a trade (default 1%)

        """
        self.min_trade_threshold = min_trade_threshold

    def calculate_rebalance_plan(
        self,
        target_weights: dict[str, Decimal],
        current_values: dict[str, Decimal],
        total_portfolio_value: Decimal,
    ) -> dict[str, RebalancePlan]:
        """Calculate comprehensive rebalancing plan using existing trading_math.

        Args:
            target_weights: Dictionary mapping symbols to target weights (0.0 to 1.0)
            current_values: Dictionary mapping symbols to current position values in dollars
            total_portfolio_value: Total portfolio value in dollars

        Returns:
            Dictionary mapping symbols to RebalancePlan domain objects

        """
        # Delegate to existing calculate_rebalance_amounts but return proper domain objects
        raw_plan = calculate_rebalance_amounts(
            {k: float(v) for k, v in target_weights.items()},
            {k: float(v) for k, v in current_values.items()},
            float(total_portfolio_value),
            float(self.min_trade_threshold),
        )

        return {
            symbol: RebalancePlan(
                symbol=symbol,
                current_weight=Decimal(str(data["current_weight"])),
                target_weight=Decimal(str(data["target_weight"])),
                weight_diff=Decimal(str(data["weight_diff"])),
                target_value=Decimal(str(data["target_value"])),
                current_value=Decimal(str(data["current_value"])),
                trade_amount=Decimal(str(data["trade_amount"])),
                needs_rebalance=bool(data.get("needs_rebalance", False)),
            )
            for symbol, data in raw_plan.items()
        }

    def get_symbols_needing_rebalance(
        self, rebalance_plan: dict[str, RebalancePlan]
    ) -> dict[str, RebalancePlan]:
        """Filter rebalance plan to only symbols that need rebalancing."""
        return {symbol: plan for symbol, plan in rebalance_plan.items() if plan.needs_rebalance}

    def get_sell_plans(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, RebalancePlan]:
        """Get rebalance plans that require selling (negative trade amounts)."""
        return {
            symbol: plan
            for symbol, plan in rebalance_plan.items()
            if plan.needs_rebalance and plan.trade_amount < 0
        }

    def get_buy_plans(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, RebalancePlan]:
        """Get rebalance plans that require buying (positive trade amounts)."""
        return {
            symbol: plan
            for symbol, plan in rebalance_plan.items()
            if plan.needs_rebalance and plan.trade_amount > 0
        }

    def calculate_total_trade_value(self, rebalance_plan: dict[str, RebalancePlan]) -> Decimal:
        """Calculate the total dollar value of trades needed."""
        return sum(
            (plan.trade_amount_abs for plan in rebalance_plan.values() if plan.needs_rebalance),
            Decimal("0"),
        )
