#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Portfolio event handler for event-driven portfolio workflows.

This demonstrates the migration from direct PortfolioOrchestrator method calls
to event-driven portfolio analysis and rebalancing workflows.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolioDTO
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    PortfolioAnalysisCompleted,
    PortfolioAnalysisRequested,
)
from the_alchemiser.shared.logging.logging_utils import get_logger


class PortfolioEventHandler:
    """Event-driven handler for portfolio analysis and rebalancing workflows.

    This handler demonstrates the migration from direct PortfolioOrchestrator calls
    to event-driven patterns, showing how to eliminate tight coupling between
    orchestrators while maintaining the same functionality.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize portfolio event handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)
        self.event_bus: EventBus = container.services.event_bus()

        # Track analysis state for correlation
        self.analysis_state: dict[str, Any] = {}

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers for portfolio workflows."""
        self.event_bus.subscribe("PortfolioAnalysisRequested", self)
        self.logger.info("Registered portfolio event handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle portfolio-related events.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, PortfolioAnalysisRequested):
                self._handle_portfolio_analysis_requested(event)
            else:
                self.logger.debug(f"Portfolio handler ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Portfolio event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type.

        Args:
            event_type: The type of event

        Returns:
            True if this handler can process the event type

        """
        return event_type in ["PortfolioAnalysisRequested"]

    def _handle_portfolio_analysis_requested(self, event: PortfolioAnalysisRequested) -> None:
        """Handle portfolio analysis request event.

        This replaces direct calls to PortfolioOrchestrator methods with
        event-driven execution, providing the same functionality with
        better decoupling and extensibility.

        Args:
            event: The portfolio analysis request event

        """
        self.logger.info(
            f"🏦 Portfolio analysis requested: {event.analysis_type}",
            extra={
                "correlation_id": event.correlation_id,
                "trigger_event_id": event.trigger_event_id,
            },
        )

        try:
            # Import here to avoid circular dependencies during migration
            from the_alchemiser.orchestration.portfolio_orchestrator import PortfolioOrchestrator

            # Create portfolio orchestrator (will be removed in Phase 5)
            portfolio_orchestrator = PortfolioOrchestrator(
                self.container.services.settings(), self.container
            )

            # Perform portfolio analysis based on type
            portfolio_state = None
            account_data = None
            allocation_comparison = None

            if event.analysis_type in ["state", "comprehensive"]:
                portfolio_state = portfolio_orchestrator.analyze_portfolio_state()
                if not portfolio_state:
                    raise RuntimeError("Failed to analyze portfolio state")

            if event.analysis_type in ["comprehensive"]:
                account_data = portfolio_orchestrator.get_comprehensive_account_data()
                if not account_data:
                    raise RuntimeError("Failed to get comprehensive account data")

                # If target allocations provided, calculate comparison
                if event.target_allocations and account_data:
                    try:
                        # Convert target allocations to ConsolidatedPortfolioDTO
                        consolidated_dto = ConsolidatedPortfolioDTO(
                            target_allocations=event.target_allocations,
                            correlation_id=event.correlation_id,
                            timestamp=datetime.now(UTC),
                            constraints={},
                        )

                        allocation_comparison_dto = (
                            portfolio_orchestrator.analyze_allocation_comparison(consolidated_dto)
                        )

                        if allocation_comparison_dto:
                            allocation_comparison = {
                                "target_values": allocation_comparison_dto.target_values,
                                "current_values": allocation_comparison_dto.current_values,
                                "deltas": allocation_comparison_dto.deltas,
                            }
                    except Exception as e:
                        self.logger.warning(f"Failed to calculate allocation comparison: {e}")

            # Emit portfolio analysis completed event
            completed_event = PortfolioAnalysisCompleted(
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                event_id=f"portfolio-analysis-{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="PortfolioEventHandler",
                portfolio_state=portfolio_state or {},
                account_data=account_data or {},
                allocation_comparison=allocation_comparison,
                analysis_timestamp=datetime.now(UTC).isoformat(),
            )

            self.event_bus.publish(completed_event)

            self.logger.info(
                "Portfolio analysis completed successfully",
                extra={
                    "correlation_id": event.correlation_id,
                    "analysis_type": event.analysis_type,
                    "completed_event_id": completed_event.event_id,
                },
            )

        except Exception as e:
            self.logger.error(
                f"Portfolio analysis failed: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "analysis_type": event.analysis_type,
                    "trigger_event_id": event.trigger_event_id,
                },
            )
            # Could emit a PortfolioAnalysisFailed event here for error handling

    def get_analysis_state(self) -> dict[str, Any]:
        """Get current portfolio analysis state for monitoring.

        Returns:
            Dictionary containing analysis state information

        """
        return {
            "handler_active": True,
            "registered_events": ["PortfolioAnalysisRequested"],
            "analysis_state": self.analysis_state,
        }