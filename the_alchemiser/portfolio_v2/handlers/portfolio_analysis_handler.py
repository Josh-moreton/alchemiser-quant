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
from the_alchemiser.portfolio_v2.adapters import (
    AccountInfoDTO,
    PositionDTO,
    adapt_account_info,
    adapt_positions,
    generate_account_snapshot_id,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    WorkflowFailed,
)
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.persistence.portfolio_idempotency_store import (
    get_portfolio_idempotency_store,
)
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolioDTO,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO, RebalancePlanItem
from the_alchemiser.shared.utils.plan_hashing import generate_plan_hash


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
        
        # Get idempotency store for plan deduplication
        self.idempotency_store = get_portfolio_idempotency_store()

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
        self.logger.info(
            "🔄 Starting portfolio analysis from SignalGenerated event",
            extra={
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "event_id": event.event_id,
                "module": "portfolio_v2",
            }
        )

        try:
            # Reconstruct ConsolidatedPortfolioDTO from event data
            consolidated_portfolio = ConsolidatedPortfolioDTO.model_validate(
                event.consolidated_portfolio
            )

            # Get current account and position data using DTO adapters
            account_data = self._get_account_data_with_adapters()
            if not account_data:
                raise ValueError("Could not retrieve account data for portfolio analysis")

            # Generate account snapshot ID for correlation
            account_snapshot_id = generate_account_snapshot_id(
                account_data["account_info"], account_data["positions"]
            )

            # Analyze allocation comparison
            allocation_comparison = self._analyze_allocation_comparison(consolidated_portfolio)
            if not allocation_comparison:
                raise ValueError("Failed to generate allocation comparison")

            # Create rebalance plan from allocation comparison  
            rebalance_plan = self._create_rebalance_plan_from_allocation_dto(
                allocation_comparison, account_data["account_info"]
            )

            # Generate plan hash for idempotency
            plan_hash = generate_plan_hash(
                rebalance_plan, allocation_comparison, account_snapshot_id
            )

            # Check if we've already processed this plan
            if self.idempotency_store.has_plan_hash(plan_hash, event.correlation_id):
                self.logger.info(
                    f"Skipping duplicate plan processing for hash {plan_hash}",
                    extra={
                        "correlation_id": event.correlation_id,
                        "plan_hash": plan_hash,
                        "module": "portfolio_v2",
                    }
                )
                return

            # Store plan hash for idempotency
            self.idempotency_store.store_plan_hash(
                plan_hash=plan_hash,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                account_snapshot_id=account_snapshot_id,
                metadata={
                    "event_id": event.event_id,
                    "schema_version": event.schema_version,
                    "signal_hash": event.signal_hash,
                }
            )

            # Emit RebalancePlanned event with enhanced metadata
            self._emit_enhanced_rebalance_planned_event(
                rebalance_plan=rebalance_plan,
                allocation_comparison=allocation_comparison,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
                plan_hash=plan_hash,
                account_snapshot_id=account_snapshot_id,
            )

            self.logger.info(
                "✅ Portfolio analysis completed successfully",
                extra={
                    "correlation_id": event.correlation_id,
                    "plan_hash": plan_hash,
                    "trades_required": len(rebalance_plan.items) > 0,
                    "module": "portfolio_v2",
                }
            )

        except Exception as e:
            self.logger.error(
                f"Portfolio analysis failed: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                    "module": "portfolio_v2",
                }
            )
            self._emit_workflow_failure(event, str(e))

    def _get_account_data_with_adapters(self) -> dict[str, Any] | None:
        """Get account data using DTO adapters (eliminates raw dict usage).

        Returns:
            Dictionary containing AccountInfoDTO and list of PositionDTOs

        """
        try:
            alpaca_manager = self.container.infrastructure.alpaca_manager()

            # Get raw account information
            raw_account_info = alpaca_manager.get_account()
            if not raw_account_info:
                self.logger.error("Failed to retrieve account information from Alpaca")
                return None

            # Get raw positions
            raw_positions = alpaca_manager.get_positions()

            # Adapt to DTOs
            account_info_dto = adapt_account_info(raw_account_info)
            positions_dto = adapt_positions(raw_positions or [])

            self.logger.debug(
                f"Retrieved account data: portfolio_value={account_info_dto.portfolio_value}, "
                f"positions={len(positions_dto)}"
            )

            return {
                "account_info": account_info_dto,
                "positions": positions_dto,
            }

        except Exception as e:
            self.logger.error(f"Failed to get account data with adapters: {e}")
            return None

    def _create_rebalance_plan_from_allocation_dto(
        self, 
        allocation_comparison: AllocationComparisonDTO,
        account_info: AccountInfoDTO,
    ) -> RebalancePlanDTO:
        """Create rebalance plan using DTO-based data (eliminates raw dict usage).

        Args:
            allocation_comparison: Allocation comparison analysis
            account_info: Account information DTO

        Returns:
            RebalancePlanDTO for the rebalance plan

        """
        try:
            from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocationDTO

            # Extract target weights from allocation comparison
            target_weights = allocation_comparison.target_values
            portfolio_value = account_info.portfolio_value
            correlation_id = "portfolio_analysis_" + str(uuid.uuid4())[:8]

            # Create strategy allocation DTO
            strategy_allocation = StrategyAllocationDTO(
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                correlation_id=correlation_id,
            )

            # Generate rebalance plan using portfolio service
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            portfolio_service = PortfolioServiceV2(alpaca_manager)
            return portfolio_service.create_rebalance_plan_dto(
                strategy=strategy_allocation,
                correlation_id=correlation_id,
            )

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            # Return minimal no-trade plan on failure with dummy item to satisfy constraints
            dummy_item = RebalancePlanItem(
                symbol="CASH",
                current_weight=Decimal("1.0"),
                target_weight=Decimal("1.0"),
                weight_diff=Decimal("0.0"),
                target_value=account_info.portfolio_value,
                current_value=account_info.portfolio_value,
                trade_amount=Decimal("0"),
                action="HOLD",
                priority=1,
            )
            return RebalancePlanDTO(
                plan_id=f"fallback-{uuid.uuid4()}",
                correlation_id=correlation_id,
                causation_id=correlation_id,
                timestamp=datetime.now(UTC),
                items=[dummy_item],
                total_portfolio_value=account_info.portfolio_value,
                total_trade_value=Decimal("0"),
                metadata={"scenario": "fallback_no_trades"},
            )
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
                    "symbol": (str(order.symbol) if hasattr(order, "symbol") else "unknown"),
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
    ) -> RebalancePlanDTO | None:
        """Create rebalance plan from allocation comparison.

        Args:
            allocation_comparison: Allocation comparison data
            account_info: Account information

        Returns:
            RebalancePlanDTO or None if no rebalancing needed

        """
        try:
            # Use PortfolioServiceV2 for rebalance plan generation
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            portfolio_service = PortfolioServiceV2(alpaca_manager)

            # Generate correlation_id for this analysis
            correlation_id = f"portfolio_analysis_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

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
            return portfolio_service.create_rebalance_plan_dto(
                strategy=strategy_allocation,
                correlation_id=correlation_id,
            )

        except Exception as e:
            self.logger.error(f"Failed to create rebalance plan: {e}")
            return None

    def _emit_enhanced_rebalance_planned_event(
        self,
        rebalance_plan: RebalancePlanDTO,
        allocation_comparison: AllocationComparisonDTO,
        correlation_id: str,
        causation_id: str,
        plan_hash: str,
        account_snapshot_id: str,
    ) -> None:
        """Emit enhanced RebalancePlanned event with deterministic metadata.

        Args:
            rebalance_plan: Generated rebalance plan
            allocation_comparison: Allocation comparison data
            correlation_id: Correlation ID from the triggering event
            causation_id: Causation ID from the triggering event
            plan_hash: Deterministic plan hash for idempotency
            account_snapshot_id: Account state snapshot identifier

        """
        try:
            event = RebalancePlanned(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"rebalance-planned-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="portfolio_v2.handlers",
                source_component="PortfolioAnalysisHandler",
                rebalance_plan=rebalance_plan,
                allocation_comparison=allocation_comparison,
                trades_required=len(rebalance_plan.items) > 0,
                metadata={
                    "analysis_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                    "trades_count": len(rebalance_plan.items),
                },
                # Enhanced fields for idempotency and traceability
                schema_version="1.0",
                plan_hash=plan_hash,
                account_snapshot_id=account_snapshot_id,
            )

            self.event_bus.publish(event)

            trades_count = len(rebalance_plan.items)
            self.logger.info(
                f"📡 Emitted RebalancePlanned event with {trades_count} trades",
                extra={
                    "correlation_id": correlation_id,
                    "plan_hash": plan_hash,
                    "account_snapshot_id": account_snapshot_id,
                    "trades_count": trades_count,
                    "module": "portfolio_v2",
                }
            )

        except Exception as e:
            self.logger.error(
                f"Failed to emit enhanced RebalancePlanned event: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "plan_hash": plan_hash,
                    "module": "portfolio_v2",
                }
            )
            raise

    def _emit_workflow_failure(self, original_event: BaseEvent, error_message: str) -> None:
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
            self.logger.error(
                f"📡 Emitted WorkflowFailed event: {error_message}",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "causation_id": original_event.event_id,
                    "workflow_type": "portfolio_analysis",
                    "module": "portfolio_v2",
                }
            )

        except Exception as e:
            self.logger.error(
                f"Failed to emit WorkflowFailed event: {e}",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "module": "portfolio_v2",
                }
            )
