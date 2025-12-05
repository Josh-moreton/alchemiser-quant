"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Core rebalance plan calculator for translating strategy allocations into trade plans.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.errors.exceptions import PortfolioError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..models.portfolio_snapshot import PortfolioSnapshot

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.core.planner"

# Priority calculation thresholds (in dollars)
PRIORITY_THRESHOLD_10K = Decimal("10000")
PRIORITY_THRESHOLD_1K = Decimal("1000")
PRIORITY_THRESHOLD_100 = Decimal("100")
PRIORITY_THRESHOLD_50 = Decimal("50")

# Portfolio weight validation tolerance
# Allows for Decimal precision errors while catching over-allocation bugs
# Tighter than StrategyAllocation's ±1% since we're validating execution feasibility
# Match the tolerance from StrategyAllocation DTO (0.99 to 1.01)
# Weights should sum to ~100% of deployable capital
TARGET_WEIGHT_SUM_MAX = Decimal("1.01")  # Allow 1% over for strategy flexibility
TARGET_WEIGHT_SUM_MIN = Decimal("0.99")  # Warn if more than 1% under-allocated


class RebalancePlanCalculator:
    """Core calculator for rebalance plans.

    Translates strategy allocation weights into concrete trade plans
    using current portfolio snapshot.
    """

    def build_plan(
        self,
        strategy: StrategyAllocation,
        snapshot: PortfolioSnapshot,
        correlation_id: str,
        causation_id: str | None = None,
    ) -> RebalancePlan:
        """Build rebalance plan from strategy allocation and portfolio snapshot.

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Current portfolio snapshot
            correlation_id: Correlation ID for tracking
            causation_id: Causation ID for event traceability (defaults to correlation_id)

        Returns:
            RebalancePlan with trade items and metadata

        Raises:
            PortfolioError: If plan cannot be calculated

        """
        # Use correlation_id as causation_id if not provided
        if causation_id is None:
            causation_id = correlation_id

        # Validate target weights sum to ~1.0 (distribute 100% of deployable capital)
        # Matches tolerance from StrategyAllocation DTO (0.99 to 1.01)
        total_target_weight = sum(strategy.target_weights.values())
        if total_target_weight > TARGET_WEIGHT_SUM_MAX:
            raise PortfolioError(
                f"Target weights sum to {total_target_weight}, must be <= {TARGET_WEIGHT_SUM_MAX}. "
                f"Weights represent distribution of deployable capital, not leverage. "
                f"Use capital_deployment_pct for leverage control.",
                module=MODULE_NAME,
                operation="build_plan",
                correlation_id=correlation_id,
            )

        # Warn if target weights are significantly under-allocated
        if total_target_weight < TARGET_WEIGHT_SUM_MIN and strategy.target_weights:
            logger.warning(
                f"Target weights sum to less than {TARGET_WEIGHT_SUM_MIN} - verify intentional",
                module=MODULE_NAME,
                action="build_plan",
                correlation_id=correlation_id,
                total_weight=str(total_target_weight),
                target_symbols=sorted(strategy.target_weights.keys()),
            )

        logger.info(
            "Building rebalance plan",
            module=MODULE_NAME,
            action="build_plan",
            correlation_id=correlation_id,
            causation_id=causation_id,
            target_symbols=sorted(strategy.target_weights.keys()),
            portfolio_value=str(snapshot.total_value),
        )

        try:
            # Step 1: Determine portfolio value to use
            portfolio_value = self._determine_portfolio_value(strategy, snapshot)

            # Step 2: Calculate target and current dollar values
            target_values, current_values = self._calculate_dollar_values(strategy, snapshot)

            # Step 3: Calculate trade amounts and actions
            trade_items = self._calculate_trade_items(target_values, current_values)

            # Step 3.5: Suppress micro trades below 1% of total portfolio value
            min_trade_threshold = self._min_trade_threshold(portfolio_value)
            logger.info(
                "Applying minimum trade threshold",
                module=MODULE_NAME,
                action="build_plan",
                correlation_id=correlation_id,
                threshold=str(min_trade_threshold),
                percentage="1%",
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
                causation_id=causation_id,  # Use provided causation_id for event traceability
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
                causation_id=causation_id,
                item_count=len(trade_items),
                total_trade_value=str(total_trade_value),
            )

            return plan

        except (ValueError, KeyError, TypeError, AttributeError, PortfolioError) as e:
            logger.error(
                "Failed to build rebalance plan",
                module=MODULE_NAME,
                action="build_plan",
                correlation_id=correlation_id,
                causation_id=causation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
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
    ) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
        """Calculate target and current dollar values for all symbols.

        Capital Calculation Logic:
        1. Base capital = cash + expected proceeds from positions being fully exited
        2. Deployable capital = base capital * capital_deployment_pct
        3. If leverage enabled (deployment > 100%), validate against buying_power

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Portfolio snapshot (includes margin info if available)

        Returns:
            Tuple of (target_values, current_values) by symbol

        Raises:
            PortfolioError: If target allocation exceeds available capital

        """
        settings = load_settings()
        current_values: dict[str, Decimal] = {}
        all_symbols = set(strategy.target_weights.keys()) | set(snapshot.positions.keys())

        # First pass: Calculate current values for all positions
        for symbol in all_symbols:
            current_quantity = snapshot.positions.get(symbol, Decimal("0"))
            current_price = snapshot.prices.get(symbol, Decimal("0"))

            # CRITICAL: Fail fast if we own a position but have no price data
            if current_quantity > Decimal("0") and current_price <= Decimal("0"):
                raise PortfolioError(
                    f"Missing or invalid price data for owned position {symbol} "
                    f"(qty={current_quantity}, price={current_price}). "
                    f"Cannot safely calculate rebalance without valid pricing.",
                    module=MODULE_NAME,
                    operation="_calculate_dollar_values",
                )

            current_values[symbol] = current_quantity * current_price

        # Calculate expected sell proceeds from positions being fully exited
        expected_full_exit_proceeds = Decimal("0")
        for symbol, current_value in current_values.items():
            target_weight = strategy.target_weights.get(symbol, Decimal("0"))
            if target_weight == Decimal("0") and current_value > Decimal("0"):
                expected_full_exit_proceeds += current_value

        # Calculate deployable capital using the new semantic config
        deployment_pct = Decimal(str(settings.alpaca.effective_deployment_pct))
        base_capital = snapshot.cash + expected_full_exit_proceeds
        deployable_capital = base_capital * deployment_pct

        leverage_enabled = settings.alpaca.is_leverage_enabled
        margin_required = Decimal("0")

        if leverage_enabled:
            # When using leverage, calculate how much margin we need
            margin_required = deployable_capital - base_capital

        logger.info(
            "Calculating deployable capital",
            module=MODULE_NAME,
            action="_calculate_dollar_values",
            current_cash=str(snapshot.cash),
            expected_full_exit_proceeds=str(expected_full_exit_proceeds),
            base_capital=str(base_capital),
            deployment_pct=f"{float(deployment_pct) * 100:.1f}%",
            deployable_capital=str(deployable_capital),
            leverage_enabled=leverage_enabled,
            margin_required=str(margin_required) if leverage_enabled else "N/A",
        )

        # If leverage enabled, validate against buying power
        if leverage_enabled:
            self._validate_leverage_capacity(
                snapshot=snapshot,
                deployable_capital=deployable_capital,
                base_capital=base_capital,
                margin_required=margin_required,
            )

        # Second pass: Calculate target values based on deployable capital
        target_values: dict[str, Decimal] = {}
        for symbol in all_symbols:
            target_weight = strategy.target_weights.get(symbol, Decimal("0"))
            target_values[symbol] = target_weight * deployable_capital

        # Final validation: total buy amount must not exceed what we can actually get
        self._validate_capital_constraints(
            snapshot=snapshot,
            target_values=target_values,
            current_values=current_values,
            deployable_capital=deployable_capital,
            leverage_enabled=leverage_enabled,
        )

        return target_values, current_values

    def _validate_leverage_capacity(
        self,
        snapshot: PortfolioSnapshot,
        deployable_capital: Decimal,
        base_capital: Decimal,
        margin_required: Decimal,
    ) -> None:
        """Validate that leverage request can be fulfilled by buying power.

        Args:
            snapshot: Portfolio snapshot with margin info
            deployable_capital: Total capital we want to deploy
            base_capital: Cash + sell proceeds (without leverage)
            margin_required: How much margin we need beyond cash

        Raises:
            PortfolioError: If buying power is insufficient for leverage

        """
        # Check if margin info is available
        if not snapshot.margin.is_margin_available():
            # Fallback: No margin data, be conservative and reduce to cash-only
            logger.warning(
                "Leverage requested but margin data unavailable - falling back to cash-only",
                module=MODULE_NAME,
                action="_validate_leverage_capacity",
                deployable_capital_requested=str(deployable_capital),
                base_capital_available=str(base_capital),
                margin_required=str(margin_required),
            )
            raise PortfolioError(
                f"Cannot use leverage: margin data unavailable from broker. "
                f"Requested ${deployable_capital} but only ${base_capital} cash available. "
                f"Reduce capital_deployment_pct to 1.0 or below for cash-only mode.",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        buying_power = snapshot.margin.buying_power
        if buying_power is None:
            # Defensive check - should not reach here if is_margin_available() was called
            raise PortfolioError(
                "buying_power unexpectedly None after margin availability check",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        # Check if buying power can cover our deployment
        if deployable_capital > buying_power:
            logger.error(
                "Insufficient buying power for leverage request",
                module=MODULE_NAME,
                action="_validate_leverage_capacity",
                deployable_capital_requested=str(deployable_capital),
                buying_power_available=str(buying_power),
                base_capital=str(base_capital),
                margin_required=str(margin_required),
                deficit=str(deployable_capital - buying_power),
            )
            raise PortfolioError(
                f"Insufficient buying power: need ${deployable_capital} but only "
                f"${buying_power} buying power available. "
                f"Consider reducing capital_deployment_pct.",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        # Log margin utilization for monitoring
        margin_info = snapshot.margin
        logger.info(
            "Leverage capacity validated",
            module=MODULE_NAME,
            action="_validate_leverage_capacity",
            deployable_capital=str(deployable_capital),
            buying_power=str(buying_power),
            buying_power_utilization_pct=f"{float(deployable_capital / buying_power) * 100:.1f}%",
            margin_utilization_pct=(
                f"{float(margin_info.margin_utilization_pct):.1f}%"
                if margin_info.margin_utilization_pct
                else "N/A"
            ),
            maintenance_buffer_pct=(
                f"{float(margin_info.maintenance_margin_buffer_pct):.1f}%"
                if margin_info.maintenance_margin_buffer_pct
                else "N/A"
            ),
        )

    def _validate_capital_constraints(
        self,
        snapshot: PortfolioSnapshot,
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
        deployable_capital: Decimal,
        *,
        leverage_enabled: bool,
    ) -> None:
        """Validate that total buy orders don't exceed available capital.

        Args:
            snapshot: Portfolio snapshot
            target_values: Target dollar values by symbol
            current_values: Current dollar values by symbol
            deployable_capital: Total capital to deploy
            leverage_enabled: Whether leverage mode is active

        Raises:
            PortfolioError: If buy orders exceed available capital

        """
        total_buy_amount = Decimal("0")
        total_sell_proceeds = Decimal("0")

        all_symbols = set(target_values.keys()) | set(current_values.keys())

        for symbol in all_symbols:
            target_value = target_values.get(symbol, Decimal("0"))
            current_value = current_values.get(symbol, Decimal("0"))
            trade_amount = target_value - current_value

            if trade_amount > Decimal("0"):
                total_buy_amount += trade_amount
            elif trade_amount < Decimal("0"):
                total_sell_proceeds += abs(trade_amount)

        available_capital = snapshot.cash + total_sell_proceeds

        if leverage_enabled:
            # In leverage mode, we already validated against buying_power
            # Just check that buys are covered by cash + sells + margin
            margin_available = (
                snapshot.margin.buying_power - available_capital
                if snapshot.margin.buying_power
                else Decimal("0")
            )
            total_available = available_capital + margin_available

            if total_buy_amount > total_available:
                raise PortfolioError(
                    f"Cannot execute rebalance: requires ${total_buy_amount} in BUY orders "
                    f"but only ${total_available} available (cash + sells + margin). "
                    f"Deficit: ${total_buy_amount - total_available}",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )
        else:
            # Cash-only mode: buys must be covered by cash + sells
            if total_buy_amount > available_capital:
                raise PortfolioError(
                    f"Cannot execute rebalance: requires ${total_buy_amount} in BUY orders "
                    f"but only ${available_capital} available "
                    f"(current cash: ${snapshot.cash}, sell proceeds: ${total_sell_proceeds}). "
                    f"Deficit: ${total_buy_amount - available_capital}",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )

        logger.info(
            "Capital constraint validation passed",
            module=MODULE_NAME,
            action="_validate_capital_constraints",
            total_buy_amount=str(total_buy_amount),
            total_sell_proceeds=str(total_sell_proceeds),
            current_cash=str(snapshot.cash),
            available_capital=str(available_capital),
            leverage_enabled=leverage_enabled,
            deployable_capital=str(deployable_capital),
        )

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
        """Compute minimum trade threshold to avoid dust trades.

        Uses MIN_TRADE_AMOUNT_USD ($5) as the absolute minimum to prevent broker rejections.
        For small accounts (<$1000), scales proportionally to avoid suppressing all trades.

        Always returns a non-negative Decimal quantized to cents.
        """
        from the_alchemiser.shared.constants import MIN_TRADE_AMOUNT_USD

        if portfolio_value <= Decimal("0"):
            return Decimal("0.00")

        # For accounts < $1000, use 1% to avoid suppressing everything
        # For larger accounts, use the fixed $5 minimum
        if portfolio_value < Decimal("1000"):
            threshold = (portfolio_value * Decimal("0.01")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            threshold = MIN_TRADE_AMOUNT_USD

        return threshold

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
                        "Suppressing micro trade",
                        module=MODULE_NAME,
                        action="suppress_small_trades",
                        symbol=item.symbol,
                        trade_amount=str(item.trade_amount),
                        threshold=str(min_threshold),
                        new_action="HOLD",
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
        if trade_amount >= PRIORITY_THRESHOLD_10K:
            return 1
        if trade_amount >= PRIORITY_THRESHOLD_1K:
            return 2
        if trade_amount >= PRIORITY_THRESHOLD_100:
            return 3
        if trade_amount >= PRIORITY_THRESHOLD_50:
            return 4
        return 5
