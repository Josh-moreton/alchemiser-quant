"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Core rebalance plan calculator for translating strategy allocations into trade plans.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.errors.exceptions import PortfolioError

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..models.portfolio_snapshot import PortfolioSnapshot

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.core.planner"


class RebalancePlanCalculator:
    """Core calculator for rebalance plans.

    Translates strategy allocation weights into concrete trade plans
    using current portfolio snapshot.
    """

    def __init__(self) -> None:
        """Initialize calculator."""

    def build_plan(
        self,
        strategy: StrategyAllocation,
        snapshot: PortfolioSnapshot,
        correlation_id: str,
    ) -> RebalancePlan:
        """Build rebalance plan from strategy allocation and portfolio snapshot.

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Current portfolio snapshot
            correlation_id: Correlation ID for tracking

        Returns:
            RebalancePlan with trade items and metadata

        Raises:
            PortfolioError: If plan cannot be calculated

        """
        logger.info(
            "Building rebalance plan",
            module=MODULE_NAME,
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
            trade_items = self._calculate_trade_items(target_values, current_values)

            # Step 3.5: Suppress micro trades below 1% of total portfolio value
            min_trade_threshold = self._min_trade_threshold(portfolio_value)
            logger.info(
                f"Applying minimum trade threshold ${min_trade_threshold} (1% of portfolio)"
            )
            trade_items = self._suppress_small_trades(trade_items, min_trade_threshold)

            # Ensure we have at least one item (required by DTO)
            if not trade_items:
                # Create a dummy HOLD item if no trades are needed
                dummy_symbol = (
                    next(iter(strategy.target_weights.keys()))
                    if strategy.target_weights
                    else "CASH"
                )
                trade_items = [
                    RebalancePlanItem(
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
            plan = RebalancePlan(
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
                    "module": MODULE_NAME,
                    "min_trade_threshold": str(min_trade_threshold),
                },
            )

            logger.info(
                "Rebalance plan built successfully",
                module=MODULE_NAME,
                action="build_plan",
                correlation_id=correlation_id,
                item_count=len(trade_items),
                total_trade_value=str(total_trade_value),
            )

            return plan

        except Exception as e:
            logger.error(
                f"Failed to build rebalance plan: {e}",
                module=MODULE_NAME,
                action="build_plan",
                correlation_id=correlation_id,
                error=str(e),
            )
            raise PortfolioError(f"Failed to build rebalance plan: {e}") from e

    def _determine_portfolio_value(
        self, strategy: StrategyAllocation, snapshot: PortfolioSnapshot
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
        self,
        strategy: StrategyAllocation,
        snapshot: PortfolioSnapshot,
        portfolio_value: Decimal,
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

        # Apply cash reserve to avoid buying power issues with broker constraints
        # This ensures we don't try to use 100% of portfolio value which can
        # exceed available buying power
        settings = load_settings()
        usage_multiplier = Decimal(str(1.0 - settings.alpaca.cash_reserve_pct))
        effective_portfolio_value = portfolio_value * usage_multiplier

        for symbol in all_symbols:
            # Calculate target value using effective portfolio value
            target_weight = strategy.target_weights.get(symbol, Decimal("0"))
            target_values[symbol] = target_weight * effective_portfolio_value

            # Calculate current value
            current_quantity = snapshot.positions.get(symbol, Decimal("0"))
            current_price = snapshot.prices.get(symbol, Decimal("0"))
            current_values[symbol] = current_quantity * current_price

        return target_values, current_values

    def _calculate_trade_items(
        self,
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
    ) -> list[RebalancePlanItem]:
        """Calculate trade items with amounts and actions.

        Args:
            target_values: Target dollar values by symbol
            current_values: Current dollar values by symbol

        Returns:
            List of RebalancePlanItem items

        """
        items = []

        # Get all symbols
        all_symbols = set(target_values.keys()) | set(current_values.keys())

        # Calculate total portfolio value for weight calculations
        total_current_value = sum(current_values.values())
        total_target_value = sum(target_values.values())

        # Use the larger of current or target for more stable weight calculations
        portfolio_value_for_weights = max(total_current_value, total_target_value)

        # Handle edge case where both are zero
        if portfolio_value_for_weights == Decimal("0"):
            # Explicitly return zeroed-out items for all symbols
            for symbol in sorted(all_symbols):
                item = RebalancePlanItem(
                    symbol=symbol,
                    current_weight=Decimal("0"),
                    target_weight=Decimal("0"),
                    weight_diff=Decimal("0"),
                    target_value=Decimal("0"),
                    current_value=Decimal("0"),
                    trade_amount=Decimal("0"),
                    action="HOLD",
                    priority=0,
                )
                items.append(item)
            return items

        for symbol in sorted(all_symbols):
            target_value = target_values.get(symbol, Decimal("0"))
            current_value = current_values.get(symbol, Decimal("0"))

            # Calculate raw trade amount
            raw_trade_amount = target_value - current_value

            # Use raw trade amount directly - no sizing policy filtering
            final_trade_amount = raw_trade_amount

            # Determine action based on sign and magnitude
            if final_trade_amount > Decimal("0"):
                action = "BUY"
            elif final_trade_amount < Decimal("0"):
                action = "SELL"
            else:
                action = "HOLD"

            # Calculate actual weights using portfolio value
            # portfolio_value_for_weights is guaranteed > 0 by line 256
            current_weight = current_value / portfolio_value_for_weights
            target_weight = target_value / portfolio_value_for_weights

            # Calculate priority (higher trade amounts get higher priority)
            priority = self._calculate_priority(abs(final_trade_amount))

            # Create trade item
            item = RebalancePlanItem(
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
        def order_priority(item: RebalancePlanItem) -> tuple[int, int]:
            # Primary sort: action priority (SELL=0, BUY=1, HOLD=2)
            action_priority = {"SELL": 0, "BUY": 1, "HOLD": 2}.get(item.action, 3)
            # Secondary sort: item priority (lower number = higher priority)
            return (action_priority, item.priority)

        items.sort(key=order_priority)

        return items

    def _min_trade_threshold(self, portfolio_value: Decimal) -> Decimal:
        """Compute minimum trade threshold as 1% of total portfolio value, in dollars.

        Always returns a non-negative Decimal quantized to cents.
        """
        if portfolio_value <= Decimal("0"):
            return Decimal("0.00")
        return (portfolio_value * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _suppress_small_trades(
        self, items: list[RebalancePlanItem], min_threshold: Decimal
    ) -> list[RebalancePlanItem]:
        """Convert BUY/SELL items below the threshold into HOLDs to avoid micro tweaks.

        This prevents execution of tiny adjustments when running the strategy multiple times per day.
        """
        suppressed: list[RebalancePlanItem] = []
        for item in items:
            try:
                if item.action in ("BUY", "SELL") and abs(item.trade_amount) < min_threshold:
                    logger.debug(
                        f"Suppressing micro trade for {item.symbol}: ${item.trade_amount} < ${min_threshold} → HOLD"
                    )
                    suppressed.append(
                        item.model_copy(
                            update={
                                "action": "HOLD",
                                "trade_amount": Decimal("0.00"),
                                # Keep other fields as-is for transparency
                            }
                        )
                    )
                else:
                    suppressed.append(item)
            except Exception as exc:
                logger.debug(
                    f"Micro-trade suppression skipped for {getattr(item, 'symbol', '?')}: {exc}"
                )
                suppressed.append(item)
        return suppressed

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
