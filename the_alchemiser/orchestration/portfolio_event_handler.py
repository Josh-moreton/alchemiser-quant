#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven portfolio analysis handler.

Handles portfolio analysis requests via events, eliminating direct
PortfolioOrchestrator method calls and enabling loose coupling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.dto.consolidated_portfolio_dto import ConsolidatedPortfolioDTO
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    EventHandler,
    PortfolioAnalysisCompleted,
    PortfolioAnalysisRequested,
)
from the_alchemiser.shared.logging.logging_utils import get_logger


class PortfolioEventHandler(EventHandler):
    """Event-driven portfolio analysis handler.
    
    Replaces direct PortfolioOrchestrator method calls with event-driven
    workflows for portfolio state analysis and allocation comparison.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize portfolio event handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)
        self.event_bus: EventBus = container.services.event_bus()

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers for portfolio workflows."""
        self.event_bus.subscribe("PortfolioAnalysisRequested", self)
        self.logger.info("Portfolio event handler registered")

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type."""
        return event_type == "PortfolioAnalysisRequested"

    def handle_event(self, event: BaseEvent) -> None:
        """Handle portfolio-related events."""
        try:
            if isinstance(event, PortfolioAnalysisRequested):
                self._handle_portfolio_analysis_requested(event)
            else:
                self.logger.debug(f"Portfolio handler ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Portfolio event handling failed: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def _handle_portfolio_analysis_requested(self, event: PortfolioAnalysisRequested) -> None:
        """Handle portfolio analysis request event.

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
            # Import here to avoid circular dependencies
            from the_alchemiser.orchestration.portfolio_orchestrator import PortfolioOrchestrator

            # Create portfolio orchestrator
            portfolio_orchestrator = PortfolioOrchestrator(
                self.container.services.settings(), self.container
            )

            # Perform analysis based on type
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

                # Calculate allocation comparison if target allocations provided
                if event.target_allocations and account_data:
                    try:
                        consolidated_dto = ConsolidatedPortfolioDTO(
                            target_allocations=event.target_allocations,
                            correlation_id=event.correlation_id,
                            timestamp=datetime.now(UTC),
                            strategy_count=1,  # Single analysis request
                            source_strategies=["portfolio_analysis"],
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
            raise