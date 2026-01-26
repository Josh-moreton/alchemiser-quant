"""Business Unit: hedge_roll_manager | Status: current.

Handler for scheduled hedge roll management.

Scans existing hedge positions and triggers rolls for expiring hedges.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.events.schemas import HedgeRollTriggered
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import (
    HedgeHistoryRepository,
    HedgePositionsRepository,
)
from the_alchemiser.shared.options.constants import CRITICAL_DTE_THRESHOLD, TAIL_HEDGE_TEMPLATE
from the_alchemiser.shared.options.schemas.hedge_history_record import HedgeAction

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
        self._template = TAIL_HEDGE_TEMPLATE

        # Initialize DynamoDB repository for hedge positions
        table_name = os.environ.get("HEDGE_POSITIONS_TABLE_NAME", "")
        self._positions_repo = HedgePositionsRepository(table_name) if table_name else None

        # Initialize DynamoDB repository for hedge history
        history_table_name = os.environ.get("HEDGE_HISTORY_TABLE_NAME", "")
        self._history_repo = HedgeHistoryRepository(history_table_name) if history_table_name else None

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
                }

            # Check each position for roll eligibility
            rolls_triggered = 0
            today = datetime.now(UTC).date()

            for position in positions:
                expiry_str = position.get("expiration_date", "")
                if not expiry_str:
                    continue

                expiry = date.fromisoformat(expiry_str)
                dte = (expiry - today).days

                # Check if DTE below threshold
                if dte < self._template.roll_trigger_dte:
                    self._trigger_roll(position, dte, correlation_id)
                    rolls_triggered += 1

            logger.info(
                "Hedge roll check completed",
                correlation_id=correlation_id,
                positions_checked=len(positions),
                rolls_triggered=rolls_triggered,
            )

            # Record EVALUATION_COMPLETED to audit trail
            self._record_evaluation_completed(correlation_id, len(positions), rolls_triggered)

            return {
                "status": "success",
                "positions_checked": len(positions),
                "rolls_triggered": rolls_triggered,
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

        # Determine roll reason
        if current_dte < CRITICAL_DTE_THRESHOLD:
            roll_reason = "dte_critical"
        elif current_dte < self._template.roll_trigger_dte:
            roll_reason = "dte_threshold"
        else:
            roll_reason = "scheduled"

        logger.info(
            "Triggering hedge roll",
            hedge_id=hedge_id,
            option_symbol=option_symbol,
            current_dte=current_dte,
            roll_reason=roll_reason,
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

        # Record ROLL_TRIGGERED to audit trail
        self._record_roll_triggered(
            hedge_id=hedge_id,
            option_symbol=option_symbol,
            underlying=underlying,
            contracts=contracts,
            correlation_id=correlation_id,
            current_dte=current_dte,
            roll_reason=roll_reason,
        )

    def _record_roll_triggered(
        self,
        hedge_id: str,
        option_symbol: str,
        underlying: str,
        contracts: int,
        correlation_id: str,
        current_dte: int,
        roll_reason: str,
    ) -> None:
        """Record ROLL_TRIGGERED action to audit trail.

        Args:
            hedge_id: Hedge identifier
            option_symbol: OCC option symbol
            underlying: Underlying symbol
            contracts: Number of contracts
            correlation_id: Correlation ID for tracing
            current_dte: Current days to expiry
            roll_reason: Reason for roll trigger

        """
        if not self._history_repo:
            return

        # Use a placeholder account ID - in production this should come from config
        account_id = "default"

        try:
            self._history_repo.record_action(
                account_id=account_id,
                action=HedgeAction.ROLL_TRIGGERED,
                hedge_id=hedge_id,
                correlation_id=correlation_id,
                underlying_symbol=underlying,
                option_symbol=option_symbol,
                contracts=contracts,
                details={
                    "current_dte": current_dte,
                    "roll_reason": roll_reason,
                },
            )
            logger.info(
                "Roll trigger recorded to audit trail",
                hedge_id=hedge_id,
                action="ROLL_TRIGGERED",
            )
        except Exception as e:
            # Don't fail the roll trigger if audit trail write fails
            logger.error(
                "Failed to record roll trigger to audit trail",
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )

    def _record_evaluation_completed(
        self,
        correlation_id: str,
        positions_checked: int,
        rolls_triggered: int,
    ) -> None:
        """Record EVALUATION_COMPLETED action to audit trail.

        Args:
            correlation_id: Correlation ID for tracing
            positions_checked: Number of positions checked
            rolls_triggered: Number of rolls triggered

        """
        if not self._history_repo:
            return

        # Use a placeholder account ID - in production this should come from config
        account_id = "default"

        try:
            self._history_repo.record_action(
                account_id=account_id,
                action=HedgeAction.EVALUATION_COMPLETED,
                hedge_id=f"eval-{correlation_id}",
                correlation_id=correlation_id,
                underlying_symbol="N/A",
                details={
                    "positions_checked": positions_checked,
                    "rolls_triggered": rolls_triggered,
                },
            )
            logger.info(
                "Evaluation completed recorded to audit trail",
                action="EVALUATION_COMPLETED",
                positions_checked=positions_checked,
                rolls_triggered=rolls_triggered,
            )
        except Exception as e:
            # Don't fail the evaluation if audit trail write fails
            logger.error(
                "Failed to record evaluation completed to audit trail",
                error=str(e),
                exc_info=True,
            )
