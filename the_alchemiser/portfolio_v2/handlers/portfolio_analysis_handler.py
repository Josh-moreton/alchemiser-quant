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
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    NegativeCashBalanceError,
    PortfolioError,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    WorkflowFailed,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolio,
)
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation

from ..core.portfolio_service import PortfolioServiceV2

# Module name constant for consistent logging and error reporting
MODULE_NAME = "portfolio_v2.handlers.portfolio_analysis_handler"


def _to_decimal_safe(value: object) -> Decimal:
    """Convert a value to Decimal safely, returning 0 for invalid values.

    Args:
        value: Value to convert (can be int, float, str, or object with .value attribute)

    Returns:
        Decimal representation of the value, or Decimal("0") if conversion fails

    """
    try:
        if hasattr(value, "value"):
            return Decimal(str(value.value))
        if isinstance(value, (int, float, str)):
            return Decimal(str(value))
        return Decimal("0")
    except (ValueError, TypeError, AttributeError, InvalidOperation):
        return Decimal("0")


def _normalize_account_info(account_info: dict[str, Any] | object) -> dict[str, Decimal]:
    """Normalize account info to a consistent dict format with Decimal values.

    Args:
        account_info: Account information as dict or SDK object

    Returns:
        Dictionary with cash, buying_power, and portfolio_value as Decimal

    Raises:
        NegativeCashBalanceError: If cash balance is negative or zero

    """
    if isinstance(account_info, dict):
        result = {
            "cash": _to_decimal_safe(account_info.get("cash", 0)),
            "buying_power": _to_decimal_safe(account_info.get("buying_power", 0)),
            "portfolio_value": _to_decimal_safe(account_info.get("portfolio_value", 0)),
        }
    else:
        # Assume it's an SDK object with attributes
        result = {
            "cash": _to_decimal_safe(getattr(account_info, "cash", 0)),
            "buying_power": _to_decimal_safe(getattr(account_info, "buying_power", 0)),
            "portfolio_value": _to_decimal_safe(getattr(account_info, "portfolio_value", 0)),
        }

    # Validate cash balance is not negative
    if result["cash"] <= Decimal("0"):
        raise NegativeCashBalanceError(
            f"Invalid cash balance: {result['cash']}. Cannot proceed with portfolio analysis.",
            cash_balance=str(result["cash"]),
            module=MODULE_NAME,
        )

    return result


def _build_positions_dict(current_positions: list[Any]) -> dict[str, Decimal]:
    """Build positions dictionary from position list with Decimal values.

    Args:
        current_positions: List of position objects from broker

    Returns:
        Dictionary mapping symbol to market value as Decimal

    """
    positions_dict = {}
    for position in current_positions:
        if hasattr(position, "symbol") and hasattr(position, "market_value"):
            symbol = str(position.symbol)
            market_value = _to_decimal_safe(position.market_value)
            positions_dict[symbol] = market_value
    return positions_dict


class PortfolioAnalysisHandler:
    """Event handler for portfolio analysis and rebalancing.

    Listens for SignalGenerated events and performs portfolio analysis,
    emitting RebalancePlanned events for downstream execution.

    This handler is idempotent - duplicate event_ids are skipped to prevent
    duplicate rebalance plan creation.
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

        # Track processed events for idempotency
        self._processed_events: set[str] = set()

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for portfolio analysis with idempotency.

        Args:
            event: The event to handle

        """
        # Check for duplicate events (idempotency control)
        if event.event_id in self._processed_events:
            self.logger.debug(
                "Skipping duplicate event",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "event_type": event.event_type,
                },
            )
            return

        try:
            if isinstance(event, SignalGenerated):
                self._handle_signal_generated(event)
                # Mark as processed after successful handling
                self._processed_events.add(event.event_id)
            else:
                self.logger.debug(
                    f"PortfolioAnalysisHandler ignoring event type: {event.event_type}"
                )

        except (PortfolioError, DataProviderError) as e:
            # Re-raise specific errors after logging
            self.logger.error(
                f"Portfolio analysis failed with known error for {event.event_type}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )
            self._emit_workflow_failure(event, str(e))
            raise
        except Exception as e:
            # Wrap unexpected errors in PortfolioError
            self.logger.error(
                f"PortfolioAnalysisHandler event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

            # Emit workflow failure event
            self._emit_workflow_failure(event, str(e))
            raise PortfolioError(
                f"Unexpected error in portfolio analysis: {e}",
                module=MODULE_NAME,
                operation="handle_event",
                correlation_id=event.correlation_id,
            ) from e

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

        Raises:
            PortfolioError: If portfolio analysis fails
            DataProviderError: If account data cannot be retrieved
            NegativeCashBalanceError: If cash balance is invalid

        """
        self.logger.info(
            "Starting portfolio analysis",
            extra={
                "correlation_id": event.correlation_id,
                "event_id": event.event_id,
            },
        )

        try:
            # Extract strategy names from the signals data
            strategy_names = self._extract_strategy_names_from_event(event)

            # Reconstruct ConsolidatedPortfolio from event data
            consolidated_portfolio = ConsolidatedPortfolio.model_validate(
                event.consolidated_portfolio
            )

            # Get current account and position data
            account_data = self._get_comprehensive_account_data()
            if not account_data or not account_data.get("account_info"):
                raise DataProviderError("Could not retrieve account data for portfolio analysis")

            # Analyze allocation comparison
            allocation_comparison = self._analyze_allocation_comparison(consolidated_portfolio)
            if not allocation_comparison:
                raise PortfolioError(
                    "Failed to generate allocation comparison",
                    module=MODULE_NAME,
                    operation="_handle_signal_generated",
                    correlation_id=event.correlation_id,
                )

            # Create rebalance plan from allocation comparison
            account_info = account_data.get("account_info", {})
            if not isinstance(account_info, dict):
                account_info = _normalize_account_info(account_info)
            rebalance_plan = self._create_rebalance_plan_from_allocation(
                allocation_comparison,
                account_info,
                event.correlation_id,
                strategy_names,
            )

            # If no rebalance plan could be created, treat as failure and stop
            if rebalance_plan is None:
                raise PortfolioError(
                    "Rebalance plan could not be created",
                    module=MODULE_NAME,
                    operation="_handle_signal_generated",
                    correlation_id=event.correlation_id,
                )

            # Emit RebalancePlanned event with proper causation
            self._emit_rebalance_planned_event(
                rebalance_plan,
                allocation_comparison,
                event,
            )

            self.logger.info(
                "Portfolio analysis completed successfully",
                extra={"correlation_id": event.correlation_id},
            )

        except (PortfolioError, DataProviderError):
            # Re-raise specific errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            self.logger.error(
                f"Portfolio analysis failed with unexpected error: {e}",
                extra={"correlation_id": event.correlation_id},
            )
            self._emit_workflow_failure(event, str(e))
            raise PortfolioError(
                f"Unexpected error in portfolio analysis: {e}",
                module=MODULE_NAME,
                operation="_handle_signal_generated",
                correlation_id=event.correlation_id,
            ) from e

    def _extract_strategy_names_from_event(self, event: SignalGenerated) -> list[str]:
        """Extract strategy names from SignalGenerated event.

        Args:
            event: The SignalGenerated event

        Returns:
            List of strategy names extracted from signals

        """
        try:
            signals_data = event.signals_data
            strategy_names = self._extract_from_signals(signals_data)

            if not strategy_names:
                strategy_names = self._extract_from_strategy_allocations(signals_data)

        except Exception as e:
            self.logger.warning(f"Failed to extract strategy names from event: {e}")
            strategy_names = []

        # Fallback to default if no strategy names found
        if not strategy_names:
            strategy_names = ["unknown"]

        self.logger.debug(f"Extracted strategy names: {strategy_names}")
        return strategy_names

    def _extract_from_signals(self, signals_data: dict[str, Any] | None) -> list[str]:
        """Extract strategy names from signals data.

        Args:
            signals_data: Signals data from the event

        Returns:
            List of strategy names from signals

        """
        strategy_names: list[str] = []

        if not isinstance(signals_data, dict) or "signals" not in signals_data:
            return strategy_names

        signals = signals_data["signals"]
        if not isinstance(signals, list):
            return strategy_names

        for signal in signals:
            if isinstance(signal, dict) and "strategy" in signal:
                strategy_name = signal["strategy"]
                if strategy_name not in strategy_names:
                    strategy_names.append(strategy_name)

        return strategy_names

    def _extract_from_strategy_allocations(self, signals_data: dict[str, Any] | None) -> list[str]:
        """Extract strategy names from strategy allocations as fallback.

        Args:
            signals_data: Signals data from the event

        Returns:
            List of strategy names from allocations

        """
        if not isinstance(signals_data, dict) or "strategy_allocations" not in signals_data:
            return []

        strategy_allocations = signals_data["strategy_allocations"]
        if not isinstance(strategy_allocations, dict):
            return []

        return list(strategy_allocations.keys())

    def _get_comprehensive_account_data(self) -> dict[str, Any]:
        """Get comprehensive account data including positions and orders.

        Returns:
            Dictionary containing account_info, current_positions, and open_orders

        Raises:
            DataProviderError: If account data cannot be retrieved

        """
        try:
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                raise DataProviderError("Account information unavailable from Alpaca")

            # Get current positions
            current_positions = alpaca_manager.get_positions()
            positions_dict = _build_positions_dict(current_positions)

            # Get open orders
            open_orders = alpaca_manager.get_orders()
            orders_list = [
                {
                    "id": str(order.id) if hasattr(order, "id") else "unknown",
                    "symbol": (str(order.symbol) if hasattr(order, "symbol") else "unknown"),
                    "side": str(order.side) if hasattr(order, "side") else "unknown",
                    "qty": _to_decimal_safe(getattr(order, "qty", 0)),
                }
                for order in (open_orders or [])
            ]

            return {
                "account_info": _normalize_account_info(account_info),
                "current_positions": positions_dict,
                "open_orders": orders_list,
            }

        except DataProviderError:
            raise
        except NegativeCashBalanceError:
            raise
        except Exception as e:
            raise DataProviderError(f"Failed to retrieve account data: {e}") from e

    def _analyze_allocation_comparison(
        self, consolidated_portfolio: ConsolidatedPortfolio
    ) -> AllocationComparison:
        """Analyze target vs current allocations.

        Args:
            consolidated_portfolio: Consolidated portfolio allocation DTO

        Returns:
            AllocationComparison with target, current, and delta values

        Raises:
            DataProviderError: If account data cannot be retrieved
            PortfolioError: If allocation comparison cannot be built

        """
        try:
            # Get current account info and positions
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get account information
            account_info = alpaca_manager.get_account()
            if not account_info:
                raise DataProviderError("Account information unavailable for allocation comparison")

            # Get current positions and normalize account info
            current_positions = alpaca_manager.get_positions()
            positions_dict = _build_positions_dict(current_positions)
            account_dict = _normalize_account_info(account_info)

            # Build allocation comparison data
            allocation_comparison_data = self._build_allocation_comparison_data(
                consolidated_portfolio, account_dict, positions_dict
            )

            # Create and return AllocationComparison
            return AllocationComparison(**allocation_comparison_data)

        except (DataProviderError, NegativeCashBalanceError):
            raise
        except Exception as e:
            raise PortfolioError(
                f"Allocation comparison analysis failed: {e}",
                module=MODULE_NAME,
                operation="_analyze_allocation_comparison",
            ) from e

    def _build_allocation_comparison_data(
        self,
        consolidated_portfolio: ConsolidatedPortfolio,
        account_dict: dict[str, Decimal],
        positions_dict: dict[str, Decimal],
    ) -> dict[str, Any]:
        """Build allocation comparison data structure with Decimal precision.

        Args:
            consolidated_portfolio: Consolidated portfolio with target allocations
            account_dict: Account information with Decimal values
            positions_dict: Current positions with Decimal market values

        Returns:
            Dictionary with target_values, current_values, and deltas as Decimal

        """
        portfolio_value = account_dict.get("portfolio_value", Decimal("0"))

        # Calculate current allocations as percentages using Decimal
        current_allocations = {}
        if portfolio_value > Decimal("0"):
            for symbol, market_value in positions_dict.items():
                # Calculate percentage allocation with Decimal precision
                current_allocations[symbol] = (market_value / portfolio_value) * Decimal("100")

        # Get target allocations from consolidated portfolio
        target_allocations = consolidated_portfolio.target_allocations

        # Get all symbols from both target and current allocations
        all_symbols = set(target_allocations.keys()) | set(current_allocations.keys())

        # Convert to Decimal values for AllocationComparison
        target_values = {}
        current_values = {}
        deltas = {}

        for symbol in all_symbols:
            # Ensure target allocations are Decimal
            target_value = target_allocations.get(symbol, Decimal("0"))
            if not isinstance(target_value, Decimal):
                target_value = Decimal(str(target_value))

            current_value = current_allocations.get(symbol, Decimal("0"))

            target_values[symbol] = target_value
            current_values[symbol] = current_value
            deltas[symbol] = target_value - current_value

        return {
            "target_values": target_values,
            "current_values": current_values,
            "deltas": deltas,
        }

    def _create_rebalance_plan_from_allocation(
        self,
        allocation_comparison: AllocationComparison,
        account_info: dict[str, Any],
        correlation_id: str,
        strategy_names: list[str] | None = None,
    ) -> RebalancePlan:
        """Create rebalance plan from allocation comparison.

        Args:
            allocation_comparison: Allocation comparison data
            account_info: Account information with Decimal values
            correlation_id: Correlation ID from the triggering event
            strategy_names: List of strategy names that generated the signals

        Returns:
            RebalancePlan with trade items

        Raises:
            PortfolioError: If rebalance plan cannot be created

        """
        try:
            # Use PortfolioServiceV2 for rebalance plan generation
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            portfolio_service = PortfolioServiceV2(alpaca_manager)

            # Use provided correlation_id instead of generating new one
            portfolio_value = account_info.get("portfolio_value", Decimal("0"))
            if not isinstance(portfolio_value, Decimal):
                portfolio_value = Decimal(str(portfolio_value))

            # target_values are already percentages, use them directly as weights
            target_weights = {}
            for symbol, value in allocation_comparison.target_values.items():
                target_weights[symbol] = value

            strategy_allocation = StrategyAllocation(
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                correlation_id=correlation_id,
            )

            # Generate rebalance plan using portfolio service
            rebalance_plan = portfolio_service.create_rebalance_plan(
                strategy=strategy_allocation,
                correlation_id=correlation_id,
                causation_id=correlation_id,  # In handler context, caused by signal generation workflow
            )

            # Add strategy attribution to metadata using model_copy
            strategy_name = self._format_strategy_names(strategy_names or ["DSL"])

            if rebalance_plan.metadata is None:
                # Create new metadata with strategy attribution
                rebalance_plan = rebalance_plan.model_copy(
                    update={"metadata": {"strategy_name": strategy_name}}
                )
            else:
                # Update existing metadata with strategy attribution
                updated_metadata = {**rebalance_plan.metadata, "strategy_name": strategy_name}
                rebalance_plan = rebalance_plan.model_copy(update={"metadata": updated_metadata})

            return rebalance_plan

        except PortfolioError:
            raise
        except Exception as e:
            raise PortfolioError(
                f"Failed to create rebalance plan: {e}",
                module=MODULE_NAME,
                operation="_create_rebalance_plan_from_allocation",
                correlation_id=correlation_id,
            ) from e

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
        return f"{strategy_names[0]} (+{len(strategy_names) - 1} others)"

    def _emit_rebalance_planned_event(
        self,
        rebalance_plan: RebalancePlan,
        allocation_comparison: AllocationComparison,
        original_event: SignalGenerated,
    ) -> None:
        """Emit RebalancePlanned event with proper causation chain.

        Args:
            rebalance_plan: Generated rebalance plan
            allocation_comparison: Allocation comparison data
            original_event: The original SignalGenerated event that triggered this analysis

        """
        try:
            # Check if workflow has failed before emitting events
            is_failed = self.event_bus.is_workflow_failed(original_event.correlation_id)
            self.logger.debug(
                "Workflow state check before RebalancePlanned emission",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "is_failed": is_failed,
                },
            )

            if is_failed:
                self.logger.info(
                    "Skipping RebalancePlanned event emission - workflow already failed",
                    extra={"correlation_id": original_event.correlation_id},
                )
                return

            self._log_final_rebalance_plan_summary(rebalance_plan)

            # Determine if actual trades (BUY/SELL) are required, not just HOLDs
            trades_required = any(item.action in ["BUY", "SELL"] for item in rebalance_plan.items)

            event = RebalancePlanned(
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,  # Direct causation from SignalGenerated
                event_id=f"rebalance-planned-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="portfolio_v2.handlers",
                source_component="PortfolioAnalysisHandler",
                rebalance_plan=rebalance_plan,
                allocation_comparison=allocation_comparison,
                trades_required=trades_required,
                metadata={
                    "analysis_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                },
            )

            self.event_bus.publish(event)

            trades_count = len(rebalance_plan.items)
            self.logger.info(
                "Emitted RebalancePlanned event",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "trades_count": trades_count,
                    "trades_required": trades_required,
                },
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
            target_weight = float(item.target_value / total_portfolio_value * Decimal("100"))
        except (TypeError, ValueError, ArithmeticError):
            target_weight = 0.0

        try:
            current_weight = float(item.current_value / total_portfolio_value * Decimal("100"))
        except (TypeError, ValueError, ArithmeticError):
            current_weight = 0.0

        return target_weight, current_weight

    def _extract_plan_totals(self, rebalance_plan: RebalancePlan) -> tuple[float, Decimal, bool]:
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

    def _log_final_rebalance_plan_summary(self, rebalance_plan: RebalancePlan) -> None:
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
                f"⚖️ Final rebalance plan: {trade_count} trades | total value ${total_trade_value:.2f}"
            )

            for item in rebalance_plan.items:
                action, symbol, trade_amount = self._extract_trade_values(item)
                target_weight, current_weight = self._calculate_weight_percentages(
                    item, total_portfolio_value, has_portfolio_value=has_portfolio_value
                )

                self.logger.debug(
                    f"  • {action} {symbol} | ${trade_amount:.2f} | target {target_weight:.2f}% vs current {current_weight:.2f}%"
                )

        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.warning(f"Failed to log final rebalance plan summary: {exc}")

    def _emit_workflow_failure(self, original_event: BaseEvent, error_message: str) -> None:
        """Emit WorkflowFailed event when portfolio analysis fails.

        Args:
            original_event: The event that triggered the failed operation
            error_message: Error message describing the failure

        """
        try:
            # Check if workflow has already failed before emitting additional failure events
            is_failed = self.event_bus.is_workflow_failed(original_event.correlation_id)
            self.logger.debug(
                f"🔍 Workflow state check for failure: correlation_id={original_event.correlation_id}, is_failed={is_failed}"
            )

            if is_failed:
                self.logger.info(
                    f"🚫 Skipping WorkflowFailed event emission - workflow {original_event.correlation_id} already failed"
                )
                return

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
