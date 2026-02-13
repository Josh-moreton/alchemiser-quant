"""Business Unit: hedge_evaluator | Status: current.

Event handler for hedge evaluation.

Processes AllTradesCompleted events and generates HedgeEvaluationCompleted
events with hedge sizing recommendations based on actual portfolio positions.
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
)
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.schemas import (
    HedgeEvaluationCompleted,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    VIX_PROXY_SCALE_FACTOR,
    VIX_PROXY_SYMBOL,
)
from the_alchemiser.shared.options.iv_signal import IVSignalCalculator, classify_iv_regime
from the_alchemiser.shared.options.kill_switch_service import KillSwitchService
from the_alchemiser.shared.options.utils import get_underlying_price

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import EventBus

logger = get_logger(__name__)


class HedgeEvaluationHandler:
    """Handler for hedge evaluation events.

    Processes AllTradesCompleted events and produces HedgeEvaluationCompleted
    events with recommendations for protective options hedges based on
    actual portfolio positions after trades complete.
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
        # Note: HedgeSizer template is now chosen dynamically by TemplateChooser
        self._hedge_sizer: HedgeSizer | None = None

        # Create ExposureCalculator with container for historical data access
        self._exposure_calculator = ExposureCalculator(container=container)

        # Initialize IV signal calculator
        self._iv_calculator = IVSignalCalculator(container=container)

        # Initialize kill switch service
        self._kill_switch = KillSwitchService()

        # Initialize template chooser for regime-based template selection
        from the_alchemiser.shared.options import TemplateChooser

        self._template_chooser = TemplateChooser()

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

    def _get_vix_proxy_sanity_check(self, correlation_id: str | None = None) -> Decimal:
        """Get VIX proxy value for sanity checking only (NOT for hedge decisions).

        This method fetches VIXY x 10 as a VIX approximation for comparison
        with the IV signal. It is NOT used for hedge sizing decisions.

        Args:
            correlation_id: Correlation ID for tracing

        Returns:
            Estimated VIX value from VIXY proxy

        Raises:
            Exception: If VIX proxy data is unavailable (non-critical)

        """
        # Fetch VIX proxy ETF price using configurable symbol
        proxy_price: Decimal = get_underlying_price(self._container, VIX_PROXY_SYMBOL)

        # Scale proxy price to approximate VIX index value
        estimated_vix: Decimal = proxy_price * VIX_PROXY_SCALE_FACTOR

        return estimated_vix

    # ========== AllTradesCompleted Handler (Primary) ==========

    def handle_all_trades_completed(
        self,
        correlation_id: str,
        causation_id: str,
        plan_id: str,
        run_id: str,
        portfolio_nav: Decimal,
        portfolio_snapshot: dict[str, object],
        timestamp: datetime,
    ) -> None:
        """Handle AllTradesCompleted event for hedge evaluation.

        Evaluates actual portfolio positions after trades complete and
        generates hedge recommendations.

        Args:
            correlation_id: Correlation ID for tracing
            causation_id: Event ID of the triggering AllTradesCompleted event
            plan_id: Source RebalancePlan identifier
            run_id: Execution run identifier
            portfolio_nav: Portfolio NAV (equity) from portfolio_snapshot
            portfolio_snapshot: Portfolio snapshot with positions from TradeAggregator
            timestamp: Event timestamp

        """
        logger.info(
            "Processing AllTradesCompleted for hedge evaluation",
            correlation_id=correlation_id,
            plan_id=plan_id,
            run_id=run_id,
            nav=str(portfolio_nav),
        )

        try:
            # FAIL-CLOSED CHECK: Emergency kill switch
            try:
                self._kill_switch.check_kill_switch(correlation_id=correlation_id)
            except HedgeFailClosedError as e:
                logger.warning(
                    "Hedge evaluation skipped - kill switch active",
                    correlation_id=correlation_id,
                    plan_id=plan_id,
                    trigger_reason=getattr(e, "trigger_reason", None),
                )
                self._publish_skip_event_from_snapshot(
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    plan_id=plan_id,
                    portfolio_nav=portfolio_nav,
                    skip_reason=f"Kill switch active: {getattr(e, 'trigger_reason', 'unknown')}",
                )
                return

            # Extract positions from portfolio_snapshot
            positions = self._extract_positions_from_snapshot(portfolio_snapshot)

            if not positions:
                logger.info(
                    "No positions in portfolio snapshot - skipping hedge evaluation",
                    correlation_id=correlation_id,
                )
                self._publish_skip_event_from_snapshot(
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    plan_id=plan_id,
                    portfolio_nav=portfolio_nav,
                    skip_reason="No equity positions in portfolio",
                )
                return

            # Map positions to sector ETFs
            sector_exposures = self._sector_mapper.map_positions_to_sectors(positions)

            # Determine primary hedge underlying
            primary_underlying, _ = self._sector_mapper.aggregate_for_single_hedge(sector_exposures)

            # Get current price of primary underlying (from Alpaca)
            underlying_price = get_underlying_price(self._container, primary_underlying)

            # Calculate portfolio exposure
            exposure = self._exposure_calculator.calculate_exposure(
                nav=portfolio_nav,
                sector_exposures=sector_exposures,
                primary_underlying=primary_underlying,
                underlying_price=underlying_price,
            )

            # Note: existing_hedge_count not available from AllTradesCompleted
            # Future: could query HedgePositionsTable for active hedges
            existing_hedge_count: int = 0

            # FAIL-CLOSED CHECK: IV data
            iv_signal = self._iv_calculator.calculate_iv_signal(
                underlying_symbol=primary_underlying,
                underlying_price=underlying_price,
                correlation_id=correlation_id,
            )

            # Classify IV regime
            iv_regime = classify_iv_regime(iv_signal)

            logger.info(
                "IV signal calculated and regime classified",
                underlying=primary_underlying,
                atm_iv=str(iv_signal.atm_iv),
                iv_percentile=str(iv_signal.iv_percentile),
                iv_skew=str(iv_signal.iv_skew),
                regime=iv_regime.regime,
                skew_rich=iv_regime.skew_rich,
                correlation_id=correlation_id,
            )

            # Fetch VIX proxy for dynamic tenor selection
            current_vix: Decimal | None = None
            try:
                vix_proxy = self._get_vix_proxy_sanity_check(correlation_id)
                current_vix = vix_proxy
                logger.info(
                    "VIX proxy fetched for dynamic tenor selection",
                    vix_proxy=str(vix_proxy),
                    iv_signal_atm=str(iv_signal.atm_iv),
                    correlation_id=correlation_id,
                )
            except Exception as e:
                logger.warning(
                    "VIX proxy fetch failed - executor will use default tenor",
                    error=str(e),
                    correlation_id=correlation_id,
                )
                current_vix = iv_signal.atm_iv * Decimal("100")

            # Choose template based on market regime
            template_rationale = self._template_chooser.choose_template(
                vix=current_vix if current_vix is not None else Decimal("20"),
                vix_percentile=iv_signal.iv_percentile,
                skew=iv_signal.iv_skew,
            )

            logger.info(
                "Template selection rationale",
                correlation_id=correlation_id,
                plan_id=plan_id,
                selected_template=template_rationale.selected_template,
                regime=template_rationale.regime,
                vix=str(template_rationale.vix),
                reason=template_rationale.reason,
                hysteresis_applied=template_rationale.hysteresis_applied,
            )

            # Create HedgeSizer with selected template
            hedge_sizer = HedgeSizer(template=template_rationale.selected_template)
            self._hedge_sizer = hedge_sizer

            # Check if hedging is needed
            should_hedge, skip_reason = hedge_sizer.should_hedge(
                exposure=exposure,
                existing_hedge_count=existing_hedge_count,
            )

            if not should_hedge:
                logger.info(
                    "Hedge evaluation skipped - conditions not met",
                    correlation_id=correlation_id,
                    skip_reason=skip_reason,
                    status="success_skip",
                )
                self._publish_skip_event_from_snapshot(
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    plan_id=plan_id,
                    portfolio_nav=portfolio_nav,
                    skip_reason=skip_reason,
                )
                return

            # Calculate hedge recommendation
            recommendation = hedge_sizer.calculate_hedge_recommendation(
                exposure=exposure,
                iv_signal=iv_signal,
                iv_regime=iv_regime,
                underlying_price=underlying_price,
            )

            # Build recommendation dict for event
            recommendation_dict: dict[str, str | int | None] = {
                "underlying_symbol": recommendation.underlying_symbol,
                "target_delta": str(recommendation.target_delta),
                "target_dte": recommendation.target_dte,
                "premium_budget": str(recommendation.premium_budget),
                "contracts_estimated": recommendation.contracts_estimated,
                "hedge_template": recommendation.hedge_template,
                "current_vix": str(current_vix) if current_vix is not None else None,
            }

            # Publish HedgeEvaluationCompleted event
            completed_event = HedgeEvaluationCompleted(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=f"hedge-eval-completed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="hedge_evaluator",
                source_component="HedgeEvaluationHandler",
                plan_id=plan_id,
                portfolio_nav=portfolio_nav,
                recommendations=[recommendation_dict],
                total_premium_budget=recommendation.premium_budget,
                budget_nav_pct=recommendation.nav_pct,
                vix_tier=recommendation.vix_tier,
                current_vix=current_vix,
                exposure_multiplier=recommendation.exposure_multiplier,
                template_selected=template_rationale.selected_template,
                template_regime=template_rationale.regime,
                template_selection_reason=template_rationale.reason,
            )

            self._event_bus.publish(completed_event)

            logger.info(
                "Hedge evaluation completed from AllTradesCompleted",
                correlation_id=correlation_id,
                plan_id=plan_id,
                run_id=run_id,
                premium_budget=str(recommendation.premium_budget),
                underlying=recommendation.underlying_symbol,
                iv_atm=str(iv_signal.atm_iv),
                iv_percentile=str(iv_signal.iv_percentile),
                iv_regime=iv_regime.regime,
                vix_tier=recommendation.vix_tier,
                template_selected=template_rationale.selected_template,
            )

        except HedgeFailClosedError as e:
            logger.error(
                "Hedge evaluation FAILED CLOSED",
                correlation_id=correlation_id,
                plan_id=plan_id,
                fail_closed_condition=e.condition,
                error=str(e),
                exc_info=True,
                alert_required=True,
            )
            self._kill_switch.record_failure(f"Fail-closed: {e.condition} - {e.message}")
            self._publish_failure_event_from_snapshot(
                correlation_id=correlation_id,
                causation_id=causation_id,
                plan_id=plan_id,
                portfolio_nav=portfolio_nav,
                error_message=str(e),
            )
            raise

        except Exception as e:
            logger.error(
                "Hedge evaluation failed with unexpected error",
                correlation_id=correlation_id,
                plan_id=plan_id,
                error=str(e),
                exc_info=True,
                alert_required=True,
            )
            self._kill_switch.record_failure(f"Unexpected error: {e!s}")
            self._publish_failure_event_from_snapshot(
                correlation_id=correlation_id,
                causation_id=causation_id,
                plan_id=plan_id,
                portfolio_nav=portfolio_nav,
                error_message=str(e),
            )
            raise

    def _extract_positions_from_snapshot(
        self,
        portfolio_snapshot: dict[str, object],
    ) -> dict[str, Decimal]:
        """Extract position values from portfolio snapshot.

        The portfolio_snapshot from AllTradesCompleted contains:
        {
            "equity": 100000.0,
            "cash": 5000.0,
            "gross_exposure": 0.95,
            "net_exposure": 0.95,
            "top_positions": [
                {"symbol": "AAPL", "weight": 25.5, "market_value": 25500.0, "qty": 150},
                {"symbol": "MSFT", "weight": 20.3, "market_value": 20300.0, "qty": 50},
                ...
            ]
        }

        Args:
            portfolio_snapshot: Portfolio snapshot dict from AllTradesCompleted

        Returns:
            Dict of symbol -> position value in dollars

        """
        positions: dict[str, Decimal] = {}

        # Note: Despite the name 'top_positions', this field now contains ALL positions (not just top 5).
        # The original top-5 throttling was removed as part of a feature to allow full position visibility
        # in notifications. The key name is retained for backward compatibility with existing snapshots.
        all_positions = portfolio_snapshot.get("top_positions", [])
        if not isinstance(all_positions, list):
            logger.warning(
                "Invalid top_positions type in portfolio_snapshot",
                actual_type=type(all_positions).__name__,
            )
            return positions

        for pos in all_positions:
            if not isinstance(pos, dict):
                continue

            symbol = pos.get("symbol")
            market_value = pos.get("market_value", 0)

            if symbol and isinstance(symbol, str) and market_value > 0:
                positions[symbol] = Decimal(str(market_value))

        logger.info(
            "Extracted positions from portfolio snapshot",
            position_count=len(positions),
            total_value=str(sum(positions.values())) if positions else "0",
        )

        return positions

    def _publish_skip_event_from_snapshot(
        self,
        correlation_id: str,
        causation_id: str,
        plan_id: str,
        portfolio_nav: Decimal,
        skip_reason: str | None,
    ) -> None:
        """Publish HedgeEvaluationCompleted with skip reason (from snapshot context).

        Args:
            correlation_id: Correlation ID for tracing
            causation_id: Causation ID (AllTradesCompleted event ID)
            plan_id: RebalancePlan identifier
            portfolio_nav: Portfolio NAV
            skip_reason: Reason for skipping hedging

        """
        completed_event = HedgeEvaluationCompleted(
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_id=f"hedge-eval-skipped-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_evaluator",
            source_component="HedgeEvaluationHandler",
            plan_id=plan_id,
            portfolio_nav=portfolio_nav,
            recommendations=[],
            total_premium_budget=Decimal("0"),
            budget_nav_pct=Decimal("0"),
            skip_reason=skip_reason,
        )
        self._event_bus.publish(completed_event)

    def _publish_failure_event_from_snapshot(
        self,
        correlation_id: str,
        causation_id: str,
        plan_id: str,
        portfolio_nav: Decimal,
        error_message: str,
    ) -> None:
        """Publish WorkflowFailed event (from snapshot context).

        Args:
            correlation_id: Correlation ID for tracing
            causation_id: Causation ID (AllTradesCompleted event ID)
            plan_id: RebalancePlan identifier
            portfolio_nav: Portfolio NAV
            error_message: Error description

        """
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=causation_id,
            event_id=f"hedge-eval-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_evaluator",
            source_component="HedgeEvaluationHandler",
            workflow_type="hedge_evaluation",
            failure_reason=error_message,
            failure_step="hedge_evaluation",
            error_details={"plan_id": plan_id, "portfolio_nav": str(portfolio_nav)},
        )
        self._event_bus.publish(failure_event)
