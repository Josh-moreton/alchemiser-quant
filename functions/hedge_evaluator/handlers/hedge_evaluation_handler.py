"""Business Unit: hedge_evaluator | Status: current.

Event handler for hedge evaluation.

Processes RebalancePlanned events and generates HedgeEvaluationCompleted
events with hedge sizing recommendations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from core.exposure_calculator import ExposureCalculator
from core.hedge_sizer import HedgeSizer
from core.sector_mapper import SectorMapper

from the_alchemiser.shared.events import BaseEvent, WorkflowFailed
from the_alchemiser.shared.events.schemas import (
    HedgeEvaluationCompleted,
    RebalancePlanned,
)
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import EventBus

logger = get_logger(__name__)


class HedgeEvaluationHandler:
    """Handler for hedge evaluation events.

    Processes RebalancePlanned events and produces HedgeEvaluationCompleted
    events with recommendations for protective options hedges.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize handler.

        Args:
            container: Application DI container
            event_bus: Optional event bus for publishing (created if None)

        """
        self._container = container
        self._sector_mapper = SectorMapper()
        self._exposure_calculator = ExposureCalculator()
        self._hedge_sizer = HedgeSizer()

        # Create event bus if not provided
        if event_bus is None:
            from the_alchemiser.shared.events import EventBus as EventBusClass

            self._event_bus = EventBusClass()
        else:
            self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus for subscribing to events."""
        return self._event_bus

    def handle_event(self, event: RebalancePlanned) -> None:
        """Handle RebalancePlanned event.

        Evaluates portfolio exposure and generates hedge recommendations.

        Args:
            event: RebalancePlanned event from portfolio module

        """
        correlation_id = event.correlation_id
        plan_id = event.rebalance_plan.plan_id

        logger.info(
            "Processing RebalancePlanned for hedge evaluation",
            correlation_id=correlation_id,
            plan_id=plan_id,
        )

        try:
            # Extract position values from rebalance plan
            positions = self._extract_positions_from_plan(event)

            # Get portfolio NAV
            nav = event.rebalance_plan.total_portfolio_value

            # Map positions to sector ETFs
            sector_exposures = self._sector_mapper.map_positions_to_sectors(positions)

            # Determine primary hedge underlying
            primary_underlying, _ = self._sector_mapper.aggregate_for_single_hedge(
                sector_exposures
            )

            # Get current price of primary underlying (from Alpaca)
            underlying_price = self._get_underlying_price(primary_underlying)

            # Calculate portfolio exposure
            exposure = self._exposure_calculator.calculate_exposure(
                nav=nav,
                sector_exposures=sector_exposures,
                primary_underlying=primary_underlying,
                underlying_price=underlying_price,
            )

            # Check if hedging is needed
            should_hedge, skip_reason = self._hedge_sizer.should_hedge(
                exposure=exposure,
                existing_hedge_count=0,  # TODO: Query existing hedges from DynamoDB
            )

            if not should_hedge:
                logger.info(
                    "Skipping hedge evaluation",
                    correlation_id=correlation_id,
                    skip_reason=skip_reason,
                )
                self._publish_skip_event(event, skip_reason)
                return

            # Get VIX for adaptive budgeting
            current_vix = self._get_current_vix()

            # Calculate hedge recommendation
            recommendation = self._hedge_sizer.calculate_hedge_recommendation(
                exposure=exposure,
                current_vix=current_vix,
                underlying_price=underlying_price,
            )

            # Build recommendation dict for event
            recommendation_dict = {
                "underlying_symbol": recommendation.underlying_symbol,
                "target_delta": str(recommendation.target_delta),
                "target_dte": recommendation.target_dte,
                "premium_budget": str(recommendation.premium_budget),
                "contracts_estimated": recommendation.contracts_estimated,
                "hedge_template": recommendation.hedge_template,
            }

            # Publish HedgeEvaluationCompleted event
            completed_event = HedgeEvaluationCompleted(
                correlation_id=correlation_id,
                causation_id=event.event_id,
                event_id=f"hedge-eval-completed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="hedge_evaluator",
                source_component="HedgeEvaluationHandler",
                plan_id=plan_id,
                portfolio_nav=nav,
                recommendations=[recommendation_dict],
                total_premium_budget=recommendation.premium_budget,
                budget_nav_pct=recommendation.nav_pct,
                vix_tier=recommendation.vix_tier,
                exposure_multiplier=recommendation.exposure_multiplier,
            )

            self._event_bus.publish(completed_event)

            logger.info(
                "Hedge evaluation completed",
                correlation_id=correlation_id,
                plan_id=plan_id,
                premium_budget=str(recommendation.premium_budget),
                underlying=recommendation.underlying_symbol,
            )

        except Exception as e:
            logger.error(
                "Hedge evaluation failed",
                correlation_id=correlation_id,
                error=str(e),
                exc_info=True,
            )
            self._publish_failure_event(event, str(e))
            raise

    def _extract_positions_from_plan(
        self,
        event: RebalancePlanned,
    ) -> dict[str, Decimal]:
        """Extract position values from rebalance plan.

        Uses current values from the rebalance plan items.

        Args:
            event: RebalancePlanned event

        Returns:
            Dict of ticker -> position value in dollars

        """
        positions: dict[str, Decimal] = {}

        for item in event.rebalance_plan.items:
            # Use current value (post-trade would use target_value)
            # We want to hedge current exposure
            if item.current_value > 0:
                positions[item.symbol] = item.current_value

        return positions

    def _get_underlying_price(self, symbol: str) -> Decimal:
        """Get current price of underlying.

        Args:
            symbol: ETF symbol (QQQ, SPY, etc.)

        Returns:
            Current price (defaults to reasonable estimate if unavailable)

        """
        # TODO: Integrate with AlpacaManager to get real price
        # For now, use reasonable defaults
        default_prices = {
            "QQQ": Decimal("485"),
            "SPY": Decimal("590"),
            "IWM": Decimal("225"),
        }
        return default_prices.get(symbol, Decimal("500"))

    def _get_current_vix(self) -> Decimal | None:
        """Get current VIX value.

        Returns:
            Current VIX value, or None if unavailable

        """
        # TODO: Integrate with market data service to get real VIX
        # For now, return None to use default
        return None

    def _publish_skip_event(
        self,
        source_event: RebalancePlanned,
        skip_reason: str | None,
    ) -> None:
        """Publish HedgeEvaluationCompleted with skip reason.

        Args:
            source_event: Original RebalancePlanned event
            skip_reason: Reason for skipping hedging

        """
        completed_event = HedgeEvaluationCompleted(
            correlation_id=source_event.correlation_id,
            causation_id=source_event.event_id,
            event_id=f"hedge-eval-skipped-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_evaluator",
            source_component="HedgeEvaluationHandler",
            plan_id=source_event.rebalance_plan.plan_id,
            portfolio_nav=source_event.rebalance_plan.total_portfolio_value,
            recommendations=[],
            total_premium_budget=Decimal("0"),
            budget_nav_pct=Decimal("0"),
            skip_reason=skip_reason,
        )
        self._event_bus.publish(completed_event)

    def _publish_failure_event(
        self,
        source_event: RebalancePlanned,
        error_message: str,
    ) -> None:
        """Publish WorkflowFailed event.

        Args:
            source_event: Original RebalancePlanned event
            error_message: Error description

        """
        failure_event = WorkflowFailed(
            correlation_id=source_event.correlation_id,
            causation_id=source_event.event_id,
            event_id=f"hedge-eval-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_evaluator",
            source_component="HedgeEvaluationHandler",
            workflow_type="hedge_evaluation",
            failure_reason=error_message,
            failure_step="hedge_evaluation",
            error_details={"plan_id": source_event.rebalance_plan.plan_id},
        )
        self._event_bus.publish(failure_event)
