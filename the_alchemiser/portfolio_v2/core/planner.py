"""Business Unit: portfolio | Status: current

Portfolio state management and rebalancing logic.

Core rebalance plan calculator for translating strategy allocations into trade plans.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO
from the_alchemiser.shared.logging.logging_utils import log_with_context
from the_alchemiser.shared.types.exceptions import PortfolioError

if TYPE_CHECKING:
    from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO

from ..models.portfolio_snapshot import PortfolioSnapshot
from ..models.sizing_policy import DEFAULT_SIZING_POLICY, SizingPolicy

logger = logging.getLogger(__name__)


class RebalancePlanCalculator:
    """Core calculator for rebalance plans.

    Translates strategy allocation weights into concrete trade plans
    using current portfolio snapshot and sizing policies.
    """

    def __init__(self, sizing_policy: SizingPolicy | None = None) -> None:
        """Initialize calculator with sizing policy.

        Args:
            sizing_policy: Policy for trade sizing and thresholds.
                          If None, uses DEFAULT_SIZING_POLICY.

        """
        self._sizing_policy = sizing_policy or DEFAULT_SIZING_POLICY

    def build_plan(
        self, strategy: StrategyAllocationDTO, snapshot: PortfolioSnapshot, correlation_id: str
    ) -> RebalancePlanDTO:
        """Build rebalance plan from strategy allocation and portfolio snapshot.

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Current portfolio snapshot
            correlation_id: Correlation ID for tracking

        Returns:
            RebalancePlanDTO with trade items and metadata

        Raises:
            PortfolioError: If plan cannot be calculated

        """
        log_with_context(
            logger,
            logging.INFO,
            "Building rebalance plan",
            module="portfolio_v2.core.planner",
            action="build_plan",
            correlation_id=correlation_id,
            target_symbols=sorted(strategy.target_weights.keys()),
            portfolio_value=str(snapshot.total_value),
        )

        try:
            # Step 1: Determine portfolio value to use
            portfolio_value = self._determine_portfolio_value(strategy, snapshot)

            # Step 2: Calculate target and current dollar values
            target_values, current_values = self._calculate_dollar_values(
                strategy, snapshot, portfolio_value
            )

            # Step 3: Calculate trade amounts and actions
            trade_items = self._calculate_trade_items(
                target_values, current_values, snapshot.prices
            )

            # Ensure we have at least one item (required by DTO)
            if not trade_items:
                # Create a dummy HOLD item if no trades are needed
                dummy_symbol = (
                    list(strategy.target_weights.keys())[0] if strategy.target_weights else "CASH"
                )
                trade_items = [
                    RebalancePlanItemDTO(
                        symbol=dummy_symbol,
                        current_weight=Decimal("0"),
                        target_weight=Decimal("0"),
                        weight_diff=Decimal("0"),
                        target_value=Decimal("0"),
                        current_value=Decimal("0"),
                        trade_amount=Decimal("0"),
                        action="HOLD",
                        priority=5,
                    )
                ]

            # Step 4: Calculate plan-level metrics
            total_trade_value = Decimal("0")
            for item in trade_items:
                total_trade_value += abs(item.trade_amount)

            # Step 5: Create rebalance plan
            plan = RebalancePlanDTO(
                correlation_id=correlation_id,
                causation_id=correlation_id,  # Use same ID for causation tracking
                timestamp=datetime.now(UTC),
                plan_id=f"portfolio_v2_{correlation_id}_{int(datetime.now(UTC).timestamp())}",
                items=trade_items,
                total_portfolio_value=portfolio_value,
                total_trade_value=total_trade_value,
                max_drift_tolerance=Decimal("0.05"),  # Default tolerance
                execution_urgency="NORMAL",
                metadata={
                    "portfolio_value": str(portfolio_value),
                    "cash_balance": str(snapshot.cash),
                    "position_count": len(snapshot.positions),
                    "module": "portfolio_v2.core.planner",
                },
            )

            log_with_context(
                logger,
                logging.INFO,
                "Rebalance plan built successfully",
                module="portfolio_v2.core.planner",
                action="build_plan",
                correlation_id=correlation_id,
                item_count=len(trade_items),
                total_trade_value=str(total_trade_value),
            )

            return plan

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to build rebalance plan: {e}",
                module="portfolio_v2.core.planner",
                action="build_plan",
                correlation_id=correlation_id,
                error=str(e),
            )
            raise PortfolioError(f"Failed to build rebalance plan: {e}") from e

    def _determine_portfolio_value(
        self, strategy: StrategyAllocationDTO, snapshot: PortfolioSnapshot
    ) -> Decimal:
        """Determine portfolio value to use for calculations.

        Args:
            strategy: Strategy allocation (may have portfolio_value override)
            snapshot: Portfolio snapshot with calculated total_value

        Returns:
            Portfolio value to use for target calculations

        """
        if strategy.portfolio_value is not None:
            return strategy.portfolio_value
        return snapshot.total_value

    def _calculate_dollar_values(
        self, strategy: StrategyAllocationDTO, snapshot: PortfolioSnapshot, portfolio_value: Decimal
    ) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
        """Calculate target and current dollar values for all symbols.

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Portfolio snapshot
            portfolio_value: Total portfolio value to use

        Returns:
            Tuple of (target_values, current_values) by symbol

        """
        target_values = {}
        current_values = {}

        # Get all symbols we need to consider
        all_symbols = set(strategy.target_weights.keys()) | set(snapshot.positions.keys())

        for symbol in all_symbols:
            # Calculate target value
            target_weight = strategy.target_weights.get(symbol, Decimal("0"))
            target_values[symbol] = target_weight * portfolio_value

            # Calculate current value
            current_quantity = snapshot.positions.get(symbol, Decimal("0"))
            current_price = snapshot.prices.get(symbol, Decimal("0"))
            current_values[symbol] = current_quantity * current_price

        return target_values, current_values

    def _calculate_trade_items(
        self,
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
        prices: dict[str, Decimal],
    ) -> list[RebalancePlanItemDTO]:
        """Calculate trade items with amounts and actions.

        Args:
            target_values: Target dollar values by symbol
            current_values: Current dollar values by symbol
            prices: Current prices by symbol

        Returns:
            List of RebalancePlanItemDTO items

        """
        items = []

        # Get all symbols
        all_symbols = set(target_values.keys()) | set(current_values.keys())

        for symbol in sorted(all_symbols):
            target_value = target_values.get(symbol, Decimal("0"))
            current_value = current_values.get(symbol, Decimal("0"))

            # Calculate raw trade amount
            raw_trade_amount = target_value - current_value

            # Apply sizing policy
            final_trade_amount, action = self._sizing_policy.apply_sizing_rules(raw_trade_amount)

            # Calculate weights (handle division by zero)
            current_weight = Decimal("0")
            target_weight = Decimal("0")

            # Note: We don't have total values easily accessible here, so weights will be approximate
            # This is acceptable for the DTO as weights are mainly for display/validation

            # Calculate priority (higher trade amounts get higher priority)
            priority = self._calculate_priority(abs(final_trade_amount))

            # Create trade item
            item = RebalancePlanItemDTO(
                symbol=symbol,
                current_weight=current_weight,
                target_weight=target_weight,
                weight_diff=target_weight - current_weight,
                target_value=target_value,
                current_value=current_value,
                trade_amount=final_trade_amount,
                action=action,
                priority=priority,
            )

            items.append(item)

        # Sort items to ensure SELL orders are processed before BUY orders
        # This allows SELL orders to free up buying power for BUY orders
        def order_priority(item: RebalancePlanItemDTO) -> tuple[int, int]:
            # Primary sort: action priority (SELL=0, BUY=1, HOLD=2)
            action_priority = {"SELL": 0, "BUY": 1, "HOLD": 2}.get(item.action, 3)
            # Secondary sort: item priority (lower number = higher priority)
            return (action_priority, item.priority)
        
        items.sort(key=order_priority)

        return items

    def _calculate_priority(self, trade_amount: Decimal) -> int:
        """Calculate execution priority based on trade amount.

        Args:
            trade_amount: Absolute trade amount

        Returns:
            Priority level (1=highest, 5=lowest)

        """
        if trade_amount >= Decimal("10000"):  # $10k+
            return 1
        if trade_amount >= Decimal("1000"):  # $1k+
            return 2
        if trade_amount >= Decimal("100"):  # $100+
            return 3
        if trade_amount >= Decimal("50"):  # $50+
            return 4
        return 5
