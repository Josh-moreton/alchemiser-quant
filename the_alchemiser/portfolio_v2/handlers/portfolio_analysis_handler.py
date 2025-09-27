#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current.

Portfolio analysis event handler for event-driven architecture.

Processes SignalGenerated events to analyze portfolio allocation and emit
RebalancePlanned events. This handler is stateless and focuses on portfolio
analysis logic without orchestration concerns.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.portfolio_v2 import PortfolioServiceV2
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    WorkflowFailed,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolioDTO,
)
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlanDTO,
    RebalancePlanItem,
)


def _to_float_safe(value: object) -> float:
    """Convert a value to float safely, returning 0.0 for invalid values."""
    try:
        if hasattr(value, "value"):
            return float(value.value)
        if isinstance(value, (int, float, str)):
            return float(value)
        return 0.0
    except (ValueError, TypeError, AttributeError):
        return 0.0


def _normalize_account_info(account_info: dict[str, Any] | object) -> dict[str, float]:
    """Normalize account info to a consistent dict format."""
    if isinstance(account_info, dict):
        return {
            "cash": _to_float_safe(account_info.get("cash", 0)),
            "buying_power": _to_float_safe(account_info.get("buying_power", 0)),
            "portfolio_value": _to_float_safe(account_info.get("portfolio_value", 0)),
        }
    # Assume it's an SDK object with attributes
    return {
        "cash": _to_float_safe(getattr(account_info, "cash", 0)),
        "buying_power": _to_float_safe(getattr(account_info, "buying_power", 0)),
        "portfolio_value": _to_float_safe(getattr(account_info, "portfolio_value", 0)),
    }


def _build_positions_dict(current_positions: list[Any]) -> dict[str, float]:
    """Build positions dictionary from position list."""
    positions_dict = {}
    for position in current_positions:
        if hasattr(position, "symbol") and hasattr(position, "market_value"):
            symbol = str(position.symbol)
            market_value = _to_float_safe(position.market_value)
            positions_dict[symbol] = market_value
    return positions_dict


class PortfolioAnalysisHandler:
    """Event handler for portfolio analysis and rebalancing.

    Listens for SignalGenerated events and performs portfolio analysis,
    emitting RebalancePlanned events for downstream execution.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the portfolio analysis handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for portfolio analysis.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, SignalGenerated):
                self._handle_signal_generated(event)
            else:
                self.logger.debug(
                    f"PortfolioAnalysisHandler ignoring event type: {event.event_type}"
                )

        except Exception as e:
            self.logger.error(
                f"PortfolioAnalysisHandler event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

            # Emit workflow failure event
            self._emit_workflow_failure(event, str(e))

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in [
            "SignalGenerated",
        ]

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle SignalGenerated event by analyzing portfolio and generating rebalance plan.

        Args:
            event: The SignalGenerated event

        """
        self.logger.info("🔄 Starting portfolio analysis from SignalGenerated event")

        try:
            # Extract strategy names from the signals data
            strategy_names = self._extract_strategy_names_from_event(event)

            # Reconstruct ConsolidatedPortfolioDTO from event data
            consolidated_portfolio = ConsolidatedPortfolioDTO.model_validate(
                event.consolidated_portfolio
            )

            # Get current account and position data
            account_data = self._get_comprehensive_account_data()
            if not account_data or not account_data.get("account_info"):
                raise ValueError(
                    "Could not retrieve account data for portfolio analysis"
                )

            # Analyze allocation comparison
            allocation_comparison = self._analyze_allocation_comparison(
                consolidated_portfolio
            )
            if not allocation_comparison:
                raise ValueError("Failed to generate allocation comparison")

            # Create rebalance plan from allocation comparison
            account_info = account_data.get("account_info", {})
            if not isinstance(account_info, dict):
                account_info = _normalize_account_info(account_info)
            rebalance_plan = self._create_rebalance_plan_from_allocation(
                allocation_comparison, account_info, strategy_names
            )

            # Emit RebalancePlanned event (even if no trades needed)
            self._emit_rebalance_planned_event(
                rebalance_plan,
                allocation_comparison,
                event.correlation_id,
                account_info,
                strategy_names,
            )

            self.logger.info("✅ Portfolio analysis completed successfully")

        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            self._emit_workflow_failure(event, str(e))

    def _extract_strategy_names_from_event(self, event: SignalGenerated) -> list[str]:
        """Extract strategy names from SignalGenerated event.

        Args:
            event: The SignalGenerated event

        Returns:
            List of strategy names extracted from signals

        """
        strategy_names = []

        try:
            # Extract from signals_data if available
            signals_data = event.signals_data
            if isinstance(signals_data, dict) and "signals" in signals_data:
                signals = signals_data["signals"]
                if isinstance(signals, list):
                    for signal in signals:
                        if isinstance(signal, dict) and "strategy" in signal:
                            strategy_name = signal["strategy"]
                            if strategy_name not in strategy_names:
                                strategy_names.append(strategy_name)

            # Fallback to strategy_allocations if signals don't have strategy info
            if (
                not strategy_names
                and isinstance(signals_data, dict)
                and "strategy_allocations" in signals_data
            ):
                strategy_allocations = signals_data["strategy_allocations"]
                if isinstance(strategy_allocations, dict):
                    strategy_names.extend(strategy_allocations.keys())

        except Exception as e:
            self.logger.warning(f"Failed to extract strategy names from event: {e}")

        # Fallback to default if no strategy names found
        if not strategy_names:
            strategy_names = ["unknown"]

        self.logger.debug(f"Extracted strategy names: {strategy_names}")
        return strategy_names

    def _get_comprehensive_account_data(self) -> dict[str, Any] | None:
        """Get comprehensive account data including positions and orders.

        Returns:
            Dictionary containing account_info, current_positions, and open_orders

        """
        try:
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                self.logger.warning("Could not retrieve account information")
                return None

            # Get current positions
            current_positions = alpaca_manager.get_positions()
            positions_dict = _build_positions_dict(current_positions)

            # Get open orders
            open_orders = alpaca_manager.get_orders()
            orders_list = [
                {
                    "id": str(order.id) if hasattr(order, "id") else "unknown",
                    "symbol": (
                        str(order.symbol) if hasattr(order, "symbol") else "unknown"
                    ),
                    "side": str(order.side) if hasattr(order, "side") else "unknown",
                    "qty": _to_float_safe(getattr(order, "qty", 0)),
                }
                for order in (open_orders or [])
            ]

            return {
                "account_info": _normalize_account_info(account_info),
                "current_positions": positions_dict,
                "open_orders": orders_list,
            }

        except Exception as e:
            self.logger.error(f"Failed to get account data: {e}")
            return None

    def _analyze_allocation_comparison(
        self, consolidated_portfolio: ConsolidatedPortfolioDTO
    ) -> AllocationComparisonDTO | None:
        """Analyze target vs current allocations.

        Args:
            consolidated_portfolio: Consolidated portfolio allocation DTO

        Returns:
            AllocationComparisonDTO or None if analysis failed

        """
        try:
            # Get current account info and positions
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                self.logger.warning("Could not retrieve account information")
                return None

            # Get current positions and normalize account info
            current_positions = alpaca_manager.get_positions()
            positions_dict = _build_positions_dict(current_positions)
            account_dict = _normalize_account_info(account_info)

            # Build allocation comparison data
            allocation_comparison_data = self._build_allocation_comparison_data(
                consolidated_portfolio, account_dict, positions_dict
            )

            # Create and return AllocationComparisonDTO
            return AllocationComparisonDTO(**allocation_comparison_data)

        except Exception as e:
            self.logger.error(f"Allocation comparison analysis failed: {e}")
            return None

    def _build_allocation_comparison_data(
        self,
        consolidated_portfolio: ConsolidatedPortfolioDTO,
        account_dict: dict[str, float],
        positions_dict: dict[str, float],
    ) -> dict[str, Any]:
        """Build allocation comparison data structure."""
        portfolio_value = account_dict.get("portfolio_value", 0.0)

        # Calculate current allocations as percentages
        current_allocations = {}
        if portfolio_value > 0:
            for symbol, market_value in positions_dict.items():
                current_allocations[symbol] = (market_value / portfolio_value) * 100

        # Get target allocations from consolidated portfolio
        target_allocations = consolidated_portfolio.target_allocations

        # Get all symbols from both target and current allocations
        all_symbols = set(target_allocations.keys()) | set(current_allocations.keys())

        # Convert to Decimal values for AllocationComparisonDTO
        target_values = {}
        current_values = {}
        deltas = {}

        for symbol in all_symbols:
            target_decimal = Decimal(str(target_allocations.get(symbol, 0.0)))
            current_decimal = Decimal(str(current_allocations.get(symbol, 0.0)))

            target_values[symbol] = target_decimal
            current_values[symbol] = current_decimal
            deltas[symbol] = target_decimal - current_decimal

        return {
            "target_values": target_values,
            "current_values": current_values,
            "deltas": deltas,
        }

    def _create_rebalance_plan_from_allocation(
        self,
        allocation_comparison: AllocationComparisonDTO,
        account_info: dict[str, Any],
        strategy_names: list[str] | None = None,
    ) -> RebalancePlanDTO | None:
        """Create rebalance plan from allocation comparison.

        Args:
            allocation_comparison: Allocation comparison data
            account_info: Account information
            strategy_names: List of strategy names that generated the signals

        Returns:
            RebalancePlanDTO or None if no rebalancing needed

        """
        try:
            # Use PortfolioServiceV2 for rebalance plan generation
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            portfolio_service = PortfolioServiceV2(alpaca_manager)

            # Generate correlation_id for this analysis
            correlation_id = (
                f"portfolio_analysis_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            )

            # Create StrategyAllocationDTO from allocation comparison
            from the_alchemiser.shared.schemas.strategy_allocation import (
                StrategyAllocationDTO,
            )

            portfolio_value = Decimal(str(account_info.get("portfolio_value", 0)))

            # target_values are already percentages (0.0-1.0), so use them directly as weights
            target_weights = {}
            for symbol, value in allocation_comparison.target_values.items():
                target_weights[symbol] = value

            strategy_allocation = StrategyAllocationDTO(
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                correlation_id=correlation_id,
            )

            # Generate rebalance plan using portfolio service
            rebalance_plan = portfolio_service.create_rebalance_plan_dto(
                strategy=strategy_allocation,
                correlation_id=correlation_id,
            )

            # Add strategy attribution to metadata if plan was created
            # Use the actual strategy names instead of hardcoded "DSL"
            strategy_name = self._format_strategy_names(strategy_names or ["DSL"])

            if rebalance_plan and rebalance_plan.metadata is None:
                # Create new metadata dict with strategy attribution
                plan_dict = rebalance_plan.model_dump()
                plan_dict["metadata"] = {"strategy_name": strategy_name}
                # Recreate the plan with updated metadata
                rebalance_plan = RebalancePlanDTO.model_validate(plan_dict)
            elif rebalance_plan and rebalance_plan.metadata:
                # Update existing metadata with strategy attribution
                plan_dict = rebalance_plan.model_dump()
                plan_dict["metadata"]["strategy_name"] = strategy_name
                # Recreate the plan with updated metadata
                rebalance_plan = RebalancePlanDTO.model_validate(plan_dict)

            return rebalance_plan

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            return None

    def _format_strategy_names(self, strategy_names: list[str]) -> str:
        """Format strategy names for metadata.

        Args:
            strategy_names: List of strategy names

        Returns:
            Formatted string for strategy attribution

        """
        if not strategy_names:
            return "DSL"

        if len(strategy_names) == 1:
            return strategy_names[0]

        # For multiple strategies, use the first one as primary with count
        return f"{strategy_names[0]} (+{len(strategy_names)-1} others)"

    def _emit_rebalance_planned_event(
        self,
        rebalance_plan: RebalancePlanDTO | None,
        allocation_comparison: AllocationComparisonDTO,
        correlation_id: str,
        account_info: dict[str, Any],
        strategy_names: list[str] | None = None,
    ) -> None:
        """Emit RebalancePlanned event.

        Args:
            rebalance_plan: Generated rebalance plan (may be None for no-op)
            allocation_comparison: Allocation comparison data
            correlation_id: Correlation ID from the triggering event
            account_info: Account information with portfolio value
            strategy_names: List of strategy names that generated the signals

        """
        try:
            # Create a plan even if None - represent as no-trade plan
            if rebalance_plan is None:
                from the_alchemiser.shared.schemas.rebalance_plan import (
                    RebalancePlanDTO,
                )

                # Format strategy names for metadata
                strategy_name = self._format_strategy_names(strategy_names or ["DSL"])

                rebalance_plan = RebalancePlanDTO(
                    plan_id=f"no-trade-{uuid.uuid4()}",
                    correlation_id=correlation_id,
                    causation_id=correlation_id,
                    timestamp=datetime.now(UTC),
                    items=[],
                    total_portfolio_value=Decimal(
                        str(account_info.get("portfolio_value", 0))
                    ),
                    total_trade_value=Decimal("0"),
                    metadata={
                        "scenario": "no_trades_needed",
                        "strategy_name": strategy_name,
                    },
                )
            self._log_final_rebalance_plan_summary(rebalance_plan)

            event = RebalancePlanned(
                correlation_id=correlation_id,
                causation_id=correlation_id,  # This event is caused by the signal generation
                event_id=f"rebalance-planned-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="portfolio_v2.handlers",
                source_component="PortfolioAnalysisHandler",
                rebalance_plan=rebalance_plan,
                allocation_comparison=allocation_comparison,
                trades_required=(
                    rebalance_plan is not None and len(rebalance_plan.items) > 0
                    if rebalance_plan
                    else False
                ),
                metadata={
                    "analysis_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                },
            )

            self.event_bus.publish(event)

            trades_count = len(rebalance_plan.items) if rebalance_plan else 0
            self.logger.info(
                f"📡 Emitted RebalancePlanned event with {trades_count} trades"
            )

        except Exception as e:
            self.logger.error(f"Failed to emit RebalancePlanned event: {e}")
            raise

    def _extract_trade_values(self, item: RebalancePlanItem) -> tuple[str, str, float]:
        """Extract action, symbol, and trade amount from a rebalance item.

        Args:
            item: Rebalance plan item

        Returns:
            Tuple of (action, symbol, trade_amount)

        """
        # With a typed DTO we can access fields directly; keep defensive conversion
        action = item.action.upper()
        symbol = item.symbol
        try:
            trade_amount = abs(float(item.trade_amount))
        except (TypeError, ValueError):
            trade_amount = 0.0

        return action, symbol, trade_amount

    def _calculate_weight_percentages(
        self,
        item: RebalancePlanItem,
        total_portfolio_value: Decimal,
        *,
        has_portfolio_value: bool,
    ) -> tuple[float, float]:
        """Calculate target and current weight percentages for a rebalance item.

        Args:
            item: Rebalance plan item
            total_portfolio_value: Total portfolio value
            has_portfolio_value: Whether portfolio has valid value

        Returns:
            Tuple of (target_weight, current_weight) as percentages

        """
        if not has_portfolio_value:
            return 0.0, 0.0

        try:
            target_weight = float(
                item.target_value / total_portfolio_value * Decimal("100")
            )
        except (TypeError, ValueError, ArithmeticError):
            target_weight = 0.0

        try:
            current_weight = float(
                item.current_value / total_portfolio_value * Decimal("100")
            )
        except (TypeError, ValueError, ArithmeticError):
            current_weight = 0.0

        return target_weight, current_weight

    def _extract_plan_totals(
        self, rebalance_plan: RebalancePlanDTO
    ) -> tuple[float, Decimal, bool]:
        """Extract total trade value, portfolio value, and validity flag from rebalance plan.

        Args:
            rebalance_plan: The rebalance plan DTO

        Returns:
            Tuple of (total_trade_value, total_portfolio_value, has_portfolio_value)

        """
        try:
            total_trade_value = float(rebalance_plan.total_trade_value)
        except (TypeError, ValueError):
            total_trade_value = 0.0

        try:
            total_portfolio_value = rebalance_plan.total_portfolio_value
            if not isinstance(total_portfolio_value, Decimal):
                total_portfolio_value = Decimal(str(total_portfolio_value))
        except (TypeError, ValueError, ArithmeticError):
            total_portfolio_value = Decimal("0")

        has_portfolio_value = total_portfolio_value > Decimal("0")
        return total_trade_value, total_portfolio_value, has_portfolio_value

    def _log_final_rebalance_plan_summary(
        self, rebalance_plan: RebalancePlanDTO
    ) -> None:
        """Log final rebalance plan trades for visibility."""
        try:
            if not rebalance_plan.items:
                self.logger.info("⚖️ Final rebalance plan: no trades required")
                return

            trade_count = len(rebalance_plan.items)
            total_trade_value, total_portfolio_value, has_portfolio_value = (
                self._extract_plan_totals(rebalance_plan)
            )

            self.logger.info(
                "⚖️ Final rebalance plan: %s trades | total value $%.2f",
                trade_count,
                total_trade_value,
            )

            for item in rebalance_plan.items:
                action, symbol, trade_amount = self._extract_trade_values(item)
                target_weight, current_weight = self._calculate_weight_percentages(
                    item, total_portfolio_value, has_portfolio_value=has_portfolio_value
                )

                self.logger.debug(
                    "  • %s %s | $%.2f | target %.2f%% vs current %.2f%%",
                    action,
                    symbol,
                    trade_amount,
                    target_weight,
                    current_weight,
                )

        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.warning("Failed to log final rebalance plan summary: %s", exc)

    def _emit_workflow_failure(
        self, original_event: BaseEvent, error_message: str
    ) -> None:
        """Emit WorkflowFailed event when portfolio analysis fails.

        Args:
            original_event: The event that triggered the failed operation
            error_message: Error message describing the failure

        """
        try:
            failure_event = WorkflowFailed(
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="portfolio_v2.handlers",
                source_component="PortfolioAnalysisHandler",
                workflow_type="portfolio_analysis",
                failure_reason=error_message,
                failure_step="portfolio_analysis",
                error_details={
                    "original_event_type": original_event.event_type,
                    "original_event_id": original_event.event_id,
                },
            )

            self.event_bus.publish(failure_event)
            self.logger.error(f"📡 Emitted WorkflowFailed event: {error_message}")

        except Exception as e:
            self.logger.error(f"Failed to emit WorkflowFailed event: {e}")
