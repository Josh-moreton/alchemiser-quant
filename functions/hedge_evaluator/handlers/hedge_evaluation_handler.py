"""Business Unit: hedge_evaluator | Status: current.

Event handler for hedge evaluation.

Processes RebalancePlanned events and generates HedgeEvaluationCompleted
events with hedge sizing recommendations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from core.exposure_calculator import ExposureCalculator
from core.hedge_sizer import HedgeSizer
from core.sector_mapper import SectorMapper

from the_alchemiser.shared.errors.exceptions import (
    HedgeFailClosedError,
    VIXProxyUnavailableError,
)
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.schemas import (
    HedgeEvaluationCompleted,
    RebalancePlanned,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    VIX_PROXY_SCALE_FACTOR,
    VIX_PROXY_SYMBOL,
)
from the_alchemiser.shared.options.kill_switch_service import KillSwitchService
from the_alchemiser.shared.options.utils import get_underlying_price

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
        self._hedge_sizer = HedgeSizer()

        # Create ExposureCalculator with container for historical data access
        self._exposure_calculator = ExposureCalculator(container=container)

        # Initialize kill switch service
        self._kill_switch = KillSwitchService()

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
            # FAIL-CLOSED CHECK: Emergency kill switch
            # Do not proceed with hedging if kill switch is active
            try:
                self._kill_switch.check_kill_switch(correlation_id=correlation_id)
            except HedgeFailClosedError as e:
                # Kill switch is active - this is an expected skip (system halted)
                logger.warning(
                    "Hedge evaluation skipped - kill switch active",
                    correlation_id=correlation_id,
                    plan_id=plan_id,
                    trigger_reason=getattr(e, "trigger_reason", None),
                )
                self._publish_skip_event(
                    event,
                    f"Kill switch active: {getattr(e, 'trigger_reason', 'unknown reason')}",
                )
                return

            # Extract position values from rebalance plan
            positions = self._extract_positions_from_plan(event)

            # Get portfolio NAV
            nav = event.rebalance_plan.total_portfolio_value

            # Map positions to sector ETFs
            sector_exposures = self._sector_mapper.map_positions_to_sectors(positions)

            # Determine primary hedge underlying
            primary_underlying, _ = self._sector_mapper.aggregate_for_single_hedge(sector_exposures)

            # Get current price of primary underlying (from Alpaca)
            underlying_price = get_underlying_price(self._container, primary_underlying)

            # Calculate portfolio exposure
            exposure = self._exposure_calculator.calculate_exposure(
                nav=nav,
                sector_exposures=sector_exposures,
                primary_underlying=primary_underlying,
                underlying_price=underlying_price,
            )

            # Derive existing hedge count from event metadata when available.
            # Falls back to 0 to preserve current behavior if metadata is absent.
            existing_hedge_count: int = 0
            metadata = getattr(event, "metadata", None)
            if isinstance(metadata, dict):
                raw_existing_hedge_count = metadata.get("existing_hedge_count")
                if isinstance(raw_existing_hedge_count, int) and raw_existing_hedge_count >= 0:
                    existing_hedge_count = raw_existing_hedge_count

            # Check if hedging is needed
            should_hedge, skip_reason = self._hedge_sizer.should_hedge(
                exposure=exposure,
                existing_hedge_count=existing_hedge_count,
            )

            if not should_hedge:
                # This is an EXPECTED skip - conditions not met for hedging
                # This is a success state, not a failure
                logger.info(
                    "Hedge evaluation skipped - conditions not met",
                    correlation_id=correlation_id,
                    skip_reason=skip_reason,
                    status="success_skip",
                )
                self._publish_skip_event(event, skip_reason)
                return

            # FAIL-CLOSED CHECK: VIX proxy data
            # Get VIX for adaptive budgeting - MUST succeed or fail closed
            current_vix = self._get_current_vix_fail_closed(correlation_id)

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
                vix_value=str(current_vix),
                vix_tier=recommendation.vix_tier,
            )

        except HedgeFailClosedError as e:
            # Fail-closed condition hit - this is an unexpected failure that needs alerting
            logger.error(
                "Hedge evaluation FAILED CLOSED",
                correlation_id=correlation_id,
                plan_id=plan_id,
                fail_closed_condition=e.condition,
                error=str(e),
                exc_info=True,
                alert_required=True,
            )
            # Record failure in kill switch service for automatic activation tracking
            self._kill_switch.record_failure(f"Fail-closed: {e.condition} - {e.message}")
            self._publish_failure_event(event, str(e))
            raise

        except Exception as e:
            # Unexpected error - needs alerting
            logger.error(
                "Hedge evaluation failed with unexpected error",
                correlation_id=correlation_id,
                plan_id=plan_id,
                error=str(e),
                exc_info=True,
                alert_required=True,
            )
            # Record failure for kill switch tracking
            self._kill_switch.record_failure(f"Unexpected error: {e!s}")
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

    def _get_current_vix_fail_closed(self, correlation_id: str | None = None) -> Decimal:
        """Get current VIX value from VIXY ETF proxy - FAIL CLOSED on unavailable data.

        Uses VIXY (ProShares VIX Short-Term Futures ETF) as a proxy for VIX
        since Alpaca does not provide direct VIX index quotes.

        This is a fail-closed check. If VIX proxy data is unavailable or stale,
        this method raises VIXProxyUnavailableError rather than defaulting to
        a mid-tier assumption. The system requires real volatility data to make
        safe hedging decisions.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Estimated VIX value from VIXY proxy

        Raises:
            VIXProxyUnavailableError: If VIX proxy data is unavailable or stale

        """
        try:
            # Fetch VIX proxy ETF price using configurable symbol
            proxy_price: Decimal = get_underlying_price(self._container, VIX_PROXY_SYMBOL)

            # Scale proxy price to approximate VIX index value
            estimated_vix: Decimal = proxy_price * VIX_PROXY_SCALE_FACTOR

            # Log for drift monitoring - VIXY/VIX relationship can drift over time
            # Monitor this in CloudWatch to detect when scaling factor needs recalibration
            logger.info(
                "Fetched VIX estimate from ETF proxy",
                proxy_symbol=VIX_PROXY_SYMBOL,
                proxy_price=str(proxy_price),
                scale_factor=str(VIX_PROXY_SCALE_FACTOR),
                estimated_vix=str(estimated_vix),
                data_source="ETF_proxy",
                correlation_id=correlation_id,
            )
            logger.info(
                "VIX proxy drift monitoring",
                proxy_symbol=VIX_PROXY_SYMBOL,
                proxy_price=str(proxy_price),
                implied_vix_ratio=str(estimated_vix / proxy_price) if proxy_price > 0 else "N/A",
                expected_ratio=str(VIX_PROXY_SCALE_FACTOR),
                vix_estimate=str(estimated_vix),
                monitoring_note="Track proxy_price vs estimated_vix ratio for scaling factor drift",
                correlation_id=correlation_id,
            )

            return estimated_vix

        except Exception as e:
            # FAIL CLOSED: VIX proxy unavailable - cannot hedge safely
            logger.error(
                "VIX proxy data unavailable - FAILING CLOSED",
                proxy_symbol=VIX_PROXY_SYMBOL,
                error=str(e),
                exc_info=True,
                correlation_id=correlation_id,
                fail_closed_condition="vix_proxy_unavailable",
                alert_required=True,
            )
            raise VIXProxyUnavailableError(
                message=f"VIX proxy ({VIX_PROXY_SYMBOL}) data unavailable - cannot hedge without volatility data: {e!s}",
                proxy_symbol=VIX_PROXY_SYMBOL,
                correlation_id=correlation_id,
            ) from e

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
