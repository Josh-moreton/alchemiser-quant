"""Business Unit: hedge_roll_manager | Status: current.

Handler for scheduled hedge roll management.

Scans existing hedge positions and triggers rolls for expiring hedges.
Supports multiple templates:
- tail_first: DTE-based roll trigger (45 DTE)
- smoothing: Fixed 21-day cadence roll
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.events.schemas import HedgeRollTriggered
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import HedgePositionsRepository
from the_alchemiser.shared.options.constants import (
    CRITICAL_DTE_THRESHOLD,
    SMOOTHING_HEDGE_TEMPLATE,
    TAIL_HEDGE_TEMPLATE,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import EventBus

logger = get_logger(__name__)


class RollScheduleHandler:
    """Handler for scheduled hedge roll checks.

    Runs daily to:
    1. Scan DynamoDB for active hedge positions
    2. Check DTE against roll threshold
    3. Trigger HedgeRollTriggered events for positions needing roll
    """

    def __init__(
        self,
        container: ApplicationContainer,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize handler.

        Args:
            container: Application DI container
            event_bus: Optional event bus for publishing

        """
        self._container = container
        self._tail_template = TAIL_HEDGE_TEMPLATE
        self._smoothing_template = SMOOTHING_HEDGE_TEMPLATE

        # Initialize DynamoDB repository for hedge positions
        table_name = os.environ.get("HEDGE_POSITIONS_TABLE_NAME", "")
        self._positions_repo = HedgePositionsRepository(table_name) if table_name else None

        # Create event bus if not provided
        if event_bus is None:
            from the_alchemiser.shared.events import EventBus as EventBusClass

            self._event_bus = EventBusClass()
        else:
            self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._event_bus

    def handle_scheduled_event(self, correlation_id: str | None = None) -> dict[str, Any]:
        """Handle scheduled roll check event.

        Scans positions and triggers rolls as needed.

        Args:
            correlation_id: Optional correlation ID for tracing

        Returns:
            Summary of roll check results

        """
        if correlation_id is None:
            correlation_id = f"roll-check-{uuid.uuid4()}"

        logger.info(
            "Starting scheduled hedge roll check",
            correlation_id=correlation_id,
        )

        try:
            # Get active hedge positions from DynamoDB
            positions = self._get_active_hedge_positions()

            if not positions:
                logger.info(
                    "No active hedge positions found",
                    correlation_id=correlation_id,
                )
                return {
                    "status": "success",
                    "positions_checked": 0,
                    "rolls_triggered": 0,
                    "assignment_risks": 0,
                }

            # Check each position for roll eligibility
            rolls_triggered = 0
            assignment_risks = 0
            today = datetime.now(UTC).date()

            for position in positions:
                expiry_str = position.get("expiration_date", "")
                if not expiry_str:
                    continue

                expiry = date.fromisoformat(expiry_str)
                dte = (expiry - today).days

                # Get position template (default to tail_first if not set)
                template = position.get("hedge_template", "tail_first")

                # Check for assignment risk on short leg (for spreads)
                if position.get("is_spread", False):
                    assignment_risk = self._check_assignment_risk(position)
                    if assignment_risk:
                        assignment_risks += 1

                # Determine roll threshold based on template
                if template == "smoothing":
                    # Fixed cadence: check days since entry
                    should_roll = self._should_roll_smoothing(position, today)
                else:
                    # DTE-based: check if below roll trigger
                    should_roll = dte < self._tail_template.roll_trigger_dte

                # Check if DTE below threshold
                if should_roll:
                    self._trigger_roll(position, dte, correlation_id)
                    rolls_triggered += 1

            logger.info(
                "Hedge roll check completed",
                correlation_id=correlation_id,
                positions_checked=len(positions),
                rolls_triggered=rolls_triggered,
                assignment_risks=assignment_risks,
            )

            return {
                "status": "success",
                "positions_checked": len(positions),
                "rolls_triggered": rolls_triggered,
                "assignment_risks": assignment_risks,
            }

        except Exception as e:
            logger.error(
                "Hedge roll check failed",
                correlation_id=correlation_id,
                error=str(e),
                exc_info=True,
            )
            return {
                "status": "error",
                "error": str(e),
            }

    def _get_active_hedge_positions(self) -> list[dict[str, Any]]:
        """Get active hedge positions from DynamoDB.

        Returns:
            List of active hedge position records

        Note:
            Queries positions with status='active' and expiration_date > today.
            Uses scan for cross-underlying queries; could be optimized with
            GSI queries if performance becomes an issue.

        """
        if not self._positions_repo:
            logger.warning(
                "Hedge positions repository not initialized - check HEDGE_POSITIONS_TABLE_NAME env var"
            )
            return []

        # Query active positions without expiration filter
        # (we filter by DTE threshold in the caller)
        positions = self._positions_repo.query_active_positions()

        logger.info(
            "Queried active hedge positions from DynamoDB",
            count=len(positions),
        )

        return positions

    def _trigger_roll(
        self,
        position: dict[str, Any],
        current_dte: int,
        correlation_id: str,
    ) -> None:
        """Trigger a roll for an expiring position.

        Args:
            position: Hedge position data
            current_dte: Current days to expiry
            correlation_id: Correlation ID for tracing

        """
        hedge_id = position.get("hedge_id", f"hedge-{uuid.uuid4()}")
        option_symbol = position.get("option_symbol", "")
        underlying = position.get("underlying_symbol", "QQQ")
        contracts = position.get("contracts", 1)
        template = position.get("hedge_template", "tail_first")

        # Determine roll reason based on template
        if template == "smoothing":
            # Smoothing uses fixed cadence
            roll_reason = "cadence_due"
        elif current_dte < CRITICAL_DTE_THRESHOLD:
            roll_reason = "dte_critical"
        elif current_dte < self._tail_template.roll_trigger_dte:
            roll_reason = "dte_threshold"
        else:
            roll_reason = "scheduled"

        logger.info(
            "Triggering hedge roll",
            hedge_id=hedge_id,
            option_symbol=option_symbol,
            current_dte=current_dte,
            roll_reason=roll_reason,
            template=template,
        )

        roll_event = HedgeRollTriggered(
            correlation_id=correlation_id,
            causation_id=f"roll-check-{correlation_id}",
            event_id=f"roll-triggered-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="hedge_roll_manager",
            source_component="RollScheduleHandler",
            hedge_id=hedge_id,
            option_symbol=option_symbol,
            underlying_symbol=underlying,
            current_dte=current_dte,
            current_contracts=contracts,
            roll_reason=roll_reason,
        )

        self._event_bus.publish(roll_event)

    def _should_roll_smoothing(self, position: dict[str, Any], today: date) -> bool:
        """Check if smoothing template position should roll (fixed 21-day cadence).

        Args:
            position: Hedge position data
            today: Current date

        Returns:
            True if position should roll based on fixed cadence

        """
        entry_date_str = position.get("entry_date", "")
        if not entry_date_str:
            return False

        try:
            # Parse entry date (might be datetime string)
            if "T" in entry_date_str:
                entry_dt = datetime.fromisoformat(entry_date_str)
                entry_date = entry_dt.date()
            else:
                entry_date = date.fromisoformat(entry_date_str)

            days_held = (today - entry_date).days

            # Roll if held >= 21 days
            return days_held >= self._smoothing_template.roll_cadence_days

        except (ValueError, AttributeError) as e:
            logger.warning(
                "Failed to parse entry date for smoothing roll check",
                position_id=position.get("hedge_id"),
                entry_date=entry_date_str,
                error=str(e),
            )
            return False

    def _check_assignment_risk(self, position: dict[str, Any]) -> bool:
        """Check for assignment risk on short leg of spread (FR-5.3).

        Args:
            position: Hedge position data (must be a spread)

        Returns:
            True if assignment risk detected (delta > 0.80)

        """
        if not position.get("is_spread", False):
            return False

        short_delta_str = position.get("short_leg_current_delta")
        if not short_delta_str:
            return False

        try:
            from decimal import Decimal

            short_delta = Decimal(str(short_delta_str))
            abs_delta = abs(short_delta)

            # Check against threshold (0.80 by default)
            if abs_delta > self._smoothing_template.assignment_risk_delta_threshold:
                hedge_id = position.get("hedge_id", "unknown")
                short_symbol = position.get("short_leg_symbol", "unknown")

                logger.warning(
                    "Assignment risk detected on short leg",
                    hedge_id=hedge_id,
                    short_leg_symbol=short_symbol,
                    short_delta=str(short_delta),
                    threshold=str(self._smoothing_template.assignment_risk_delta_threshold),
                )
                return True

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse short leg delta for assignment risk check",
                position_id=position.get("hedge_id"),
                short_delta=short_delta_str,
                error=str(e),
            )

        return False
