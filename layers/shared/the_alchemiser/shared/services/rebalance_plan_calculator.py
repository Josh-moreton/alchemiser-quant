"""Business Unit: shared | Status: current.

Core rebalance plan calculator for translating strategy allocations into trade plans.

Moved from portfolio_v2 to shared layer to enable reuse by
strategy workers in the per-strategy books architecture.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.config.config import MarginSafetyConfig, load_settings
from the_alchemiser.shared.errors.exceptions import PortfolioError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.utils.strategy_attribution import (
    get_primary_strategy_for_symbol,
    get_single_strategy_id,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.schemas.portfolio_snapshot import PortfolioSnapshot
    from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

logger = get_logger(__name__)

MODULE_NAME = "shared.services.rebalance_plan_calculator"

# Priority calculation thresholds (in dollars)
PRIORITY_THRESHOLD_10K = Decimal("10000")
PRIORITY_THRESHOLD_1K = Decimal("1000")
PRIORITY_THRESHOLD_100 = Decimal("100")
PRIORITY_THRESHOLD_50 = Decimal("50")

# Capital constraint validation tolerance
CAPITAL_CONSTRAINT_TOLERANCE = Decimal("0.01")

# Portfolio weight validation tolerance
TARGET_WEIGHT_SUM_MAX = Decimal("1.01")
TARGET_WEIGHT_SUM_MIN = Decimal("0.99")


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
        strategy_contributions: dict[str, dict[str, Decimal]] | None = None,
    ) -> RebalancePlan:
        """Build rebalance plan from strategy allocation and portfolio snapshot.

        Args:
            strategy: Strategy allocation with target weights
            snapshot: Current portfolio snapshot
            correlation_id: Correlation ID for tracking
            causation_id: Causation ID for event traceability
            strategy_contributions: Per-strategy allocation breakdown for attribution

        Returns:
            RebalancePlan with trade items and metadata

        Raises:
            PortfolioError: If plan cannot be calculated

        """
        if causation_id is None:
            causation_id = correlation_id

        total_target_weight = sum(strategy.target_weights.values())
        if total_target_weight > TARGET_WEIGHT_SUM_MAX:
            raise PortfolioError(
                f"Target weights sum to {total_target_weight}, must be <= {TARGET_WEIGHT_SUM_MAX}. "
                f"Weights represent distribution of deployable capital, not leverage. "
                f"Use equity_deployment_pct for leverage control.",
                module=MODULE_NAME,
                operation="build_plan",
                correlation_id=correlation_id,
            )

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
            portfolio_value = self._determine_portfolio_value(strategy, snapshot)
            target_values, current_values = self._calculate_dollar_values(strategy, snapshot)
            trade_items = self._calculate_trade_items(
                target_values, current_values, strategy_contributions
            )

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

            plan_strategy_id = get_single_strategy_id(strategy_contributions or {})

            if not trade_items:
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
                        strategy_id=plan_strategy_id,
                    )
                ]

            total_trade_value = Decimal("0")
            for item in trade_items:
                total_trade_value += abs(item.trade_amount)

            plan = RebalancePlan(
                correlation_id=correlation_id,
                causation_id=causation_id,
                timestamp=datetime.now(UTC),
                plan_id=f"rebalance_{correlation_id}_{int(datetime.now(UTC).timestamp())}",
                strategy_id=plan_strategy_id,
                items=trade_items,
                total_portfolio_value=portfolio_value,
                total_trade_value=total_trade_value,
                max_drift_tolerance=Decimal("0.05"),
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
                strategy_id=plan_strategy_id,
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
        """Determine portfolio value to use for calculations."""
        if strategy.portfolio_value is not None:
            return strategy.portfolio_value
        return snapshot.total_value

    def _calculate_dollar_values(
        self,
        strategy: StrategyAllocation,
        snapshot: PortfolioSnapshot,
    ) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
        """Calculate target and current dollar values for all symbols.

        Uses equity-based deployment calculation with optional leverage validation.
        """
        settings = load_settings()
        current_values: dict[str, Decimal] = {}
        all_symbols = set(strategy.target_weights.keys()) | set(snapshot.positions.keys())

        for symbol in all_symbols:
            current_quantity = snapshot.positions.get(symbol, Decimal("0"))
            current_price = snapshot.prices.get(symbol, Decimal("0"))

            if current_quantity > Decimal("0") and current_price <= Decimal("0"):
                raise PortfolioError(
                    f"Missing or invalid price data for owned position {symbol} "
                    f"(qty={current_quantity}, price={current_price}). "
                    f"Cannot safely calculate rebalance without valid pricing.",
                    module=MODULE_NAME,
                    operation="_calculate_dollar_values",
                )

            current_values[symbol] = current_quantity * current_price

        deployment_pct = Decimal(str(settings.alpaca.effective_deployment_pct))
        equity = snapshot.total_value
        deployable_capital = equity * deployment_pct

        leverage_enabled = settings.alpaca.is_leverage_enabled
        margin_required = deployable_capital - equity if leverage_enabled else Decimal("0")

        logger.info(
            "Calculating deployable capital (equity-based)",
            module=MODULE_NAME,
            action="_calculate_dollar_values",
            portfolio_equity=str(equity),
            current_cash=str(snapshot.cash),
            deployment_pct=f"{float(deployment_pct) * 100:.1f}%",
            deployable_capital=str(deployable_capital),
            leverage_enabled=leverage_enabled,
            margin_required=str(margin_required) if leverage_enabled else "N/A",
        )

        if leverage_enabled:
            deployable_capital = self._validate_leverage_capacity(
                snapshot=snapshot,
                deployable_capital=deployable_capital,
                equity=equity,
                margin_required=margin_required,
                margin_safety_config=settings.alpaca.margin_safety,
            )

        target_values: dict[str, Decimal] = {}
        for symbol in all_symbols:
            target_weight = strategy.target_weights.get(symbol, Decimal("0"))
            target_values[symbol] = target_weight * deployable_capital

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
        equity: Decimal,
        margin_required: Decimal,
        margin_safety_config: MarginSafetyConfig,
    ) -> Decimal:
        """Validate that leverage request can be fulfilled safely."""
        if not snapshot.margin.is_margin_available():
            logger.warning(
                "Leverage requested but margin data unavailable - falling back to cash-only",
                module=MODULE_NAME,
                action="_validate_leverage_capacity",
                deployable_capital_requested=str(deployable_capital),
                equity=str(equity),
                margin_required=str(margin_required),
            )
            raise PortfolioError(
                f"Cannot use leverage: margin data unavailable from broker. "
                f"Requested ${deployable_capital} but only ${equity} equity available. "
                f"Reduce equity_deployment_pct to 1.0 or below for cash-only mode.",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        margin_info = snapshot.margin
        buying_power = margin_info.effective_buying_power
        if buying_power is None:
            buying_power = margin_info.buying_power

        if buying_power is None:
            raise PortfolioError(
                "buying_power unexpectedly None after margin availability check",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        logger.info(
            "Margin capacity check",
            module=MODULE_NAME,
            action="_validate_leverage_capacity",
            deployable_capital_target=str(deployable_capital),
            buying_power_available=str(buying_power),
            equity=str(equity),
            margin_required=str(margin_required),
        )

        is_safe, safety_reason = margin_info.is_within_safety_limits(margin_safety_config)
        if not is_safe:
            logger.error(
                "Margin safety limit exceeded",
                module=MODULE_NAME,
                action="_validate_leverage_capacity",
                safety_reason=safety_reason,
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
            raise PortfolioError(
                f"Margin safety limit exceeded: {safety_reason}. "
                f"Reduce equity_deployment_pct or wait for margin conditions to improve.",
                module=MODULE_NAME,
                operation="_validate_leverage_capacity",
            )

        is_warning, warning_msg = margin_info.is_approaching_warning_threshold(margin_safety_config)
        if is_warning:
            logger.warning(
                "Margin approaching warning threshold",
                module=MODULE_NAME,
                action="_validate_leverage_capacity",
                warning_message=warning_msg,
                margin_utilization_pct=(
                    f"{float(margin_info.margin_utilization_pct):.1f}%"
                    if margin_info.margin_utilization_pct
                    else "N/A"
                ),
            )

        original_deployable_capital = deployable_capital
        intraday_bp = margin_info.intraday_buying_power

        if intraday_bp is not None:
            effective_constraint = min(intraday_bp, buying_power)
            if deployable_capital > effective_constraint:
                deployable_capital = effective_constraint
                logger.warning(
                    "Deployable capital constrained by buying power limits",
                    module=MODULE_NAME,
                    action="_validate_leverage_capacity",
                    original_deployable_capital=str(original_deployable_capital),
                    constrained_deployable_capital=str(deployable_capital),
                    intraday_buying_power=str(intraday_bp),
                    overnight_buying_power=str(buying_power),
                    is_pdt_account=margin_info.is_pdt_account,
                    reason=(
                        "daytrading_buying_power constraint (PDT account)"
                        if margin_info.is_pdt_account
                        else "buying power constraint"
                    ),
                )

        logger.info(
            "Leverage capacity validated with margin safety",
            module=MODULE_NAME,
            action="_validate_leverage_capacity",
            deployable_capital=str(deployable_capital),
            original_deployable_capital=str(original_deployable_capital),
            buying_power=str(buying_power),
            intraday_buying_power=str(intraday_bp) if intraday_bp else "N/A",
            buying_power_utilization_pct=(
                f"{float(deployable_capital / buying_power) * 100:.1f}%"
                if buying_power > Decimal("0")
                else "N/A"
            ),
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
            is_margin_account=margin_info.is_margin_account,
            is_pdt_account=margin_info.is_pdt_account,
            multiplier=margin_info.multiplier,
        )

        return deployable_capital

    def _validate_capital_constraints(
        self,
        snapshot: PortfolioSnapshot,
        target_values: dict[str, Decimal],
        current_values: dict[str, Decimal],
        deployable_capital: Decimal,
        *,
        leverage_enabled: bool,
    ) -> None:
        """Validate that total buy orders don't exceed available capital."""
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
            if snapshot.margin.buying_power is None:
                raise PortfolioError(
                    "Margin buying power is not available in leverage mode.",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )
            intraday_bp = snapshot.margin.intraday_buying_power
            effective_bp = snapshot.margin.effective_buying_power or snapshot.margin.buying_power

            if intraday_bp is not None and effective_bp is not None:
                constraint_bp = min(intraday_bp, effective_bp)
            else:
                constraint_bp = intraday_bp or effective_bp

            if constraint_bp is None:
                raise PortfolioError(
                    "Unable to determine buying power constraint for capital validation.",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )

            net_buy_needed = total_buy_amount - total_sell_proceeds
            deficit = net_buy_needed - constraint_bp
            if deficit > CAPITAL_CONSTRAINT_TOLERANCE:
                bp_info = f"intraday: ${intraday_bp}, overnight: ${effective_bp}"
                if snapshot.margin.is_pdt_account:
                    bp_info = f"daytrading_buying_power: ${intraday_bp} (PDT account)"
                raise PortfolioError(
                    f"Cannot execute rebalance: requires ${net_buy_needed} net BUY capital "
                    f"(total buys: ${total_buy_amount}, sell proceeds: ${total_sell_proceeds}) "
                    f"but only ${constraint_bp} buying power available ({bp_info}). "
                    f"Deficit: ${deficit}. "
                    f"Consider reducing equity_deployment_pct.",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )

            logger.info(
                "Capital constraint validation passed (leverage mode)",
                module=MODULE_NAME,
                action="_validate_capital_constraints",
                total_buy_amount=str(total_buy_amount),
                total_sell_proceeds=str(total_sell_proceeds),
                net_buy_needed=str(net_buy_needed),
                current_cash=str(snapshot.cash),
                intraday_buying_power=str(intraday_bp) if intraday_bp else "N/A",
                effective_buying_power=str(effective_bp) if effective_bp else "N/A",
                constraint_buying_power=str(constraint_bp),
                is_pdt_account=snapshot.margin.is_pdt_account,
                leverage_enabled=leverage_enabled,
                deployable_capital=str(deployable_capital),
            )
        else:
            deficit = total_buy_amount - available_capital
            if deficit > CAPITAL_CONSTRAINT_TOLERANCE:
                raise PortfolioError(
                    f"Cannot execute rebalance: requires ${total_buy_amount} in BUY orders "
                    f"but only ${available_capital} available "
                    f"(current cash: ${snapshot.cash}, sell proceeds: ${total_sell_proceeds}). "
                    f"Deficit: ${deficit}",
                    module=MODULE_NAME,
                    operation="_validate_capital_constraints",
                )

            logger.info(
                "Capital constraint validation passed (cash mode)",
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
        strategy_contributions: dict[str, dict[str, Decimal]] | None = None,
    ) -> list[RebalancePlanItem]:
        """Calculate trade items with amounts and actions."""
        items = []
        all_symbols = set(target_values.keys()) | set(current_values.keys())

        total_current_value = sum(current_values.values())
        total_target_value = sum(target_values.values())
        portfolio_value_for_weights = max(total_current_value, total_target_value)

        if portfolio_value_for_weights == Decimal("0"):
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
                    strategy_id=get_primary_strategy_for_symbol(
                        symbol, strategy_contributions or {}
                    ),
                )
                items.append(item)
            return items

        for symbol in sorted(all_symbols):
            target_value = target_values.get(symbol, Decimal("0"))
            current_value = current_values.get(symbol, Decimal("0"))
            final_trade_amount = target_value - current_value

            if final_trade_amount > Decimal("0"):
                action = "BUY"
            elif final_trade_amount < Decimal("0"):
                action = "SELL"
            else:
                action = "HOLD"

            current_weight = current_value / portfolio_value_for_weights
            target_weight = target_value / portfolio_value_for_weights
            priority = self._calculate_priority(abs(final_trade_amount))
            symbol_strategy_id = get_primary_strategy_for_symbol(
                symbol, strategy_contributions or {}
            )

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
                strategy_id=symbol_strategy_id,
            )
            items.append(item)

        def order_priority(item: RebalancePlanItem) -> tuple[int, int]:
            action_priority = {"SELL": 0, "BUY": 1, "HOLD": 2}.get(item.action, 3)
            return (action_priority, item.priority)

        items.sort(key=order_priority)
        return items

    def _min_trade_threshold(self, portfolio_value: Decimal) -> Decimal:
        """Compute minimum trade threshold to avoid dust trades."""
        from the_alchemiser.shared.constants import MIN_TRADE_AMOUNT_USD

        if portfolio_value <= Decimal("0"):
            return Decimal("0.00")

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
        """Convert BUY/SELL items below the threshold into HOLDs."""
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
        """Calculate execution priority based on trade amount (1=highest, 5=lowest)."""
        if trade_amount >= PRIORITY_THRESHOLD_10K:
            return 1
        if trade_amount >= PRIORITY_THRESHOLD_1K:
            return 2
        if trade_amount >= PRIORITY_THRESHOLD_100:
            return 3
        if trade_amount >= PRIORITY_THRESHOLD_50:
            return 4
        return 5
