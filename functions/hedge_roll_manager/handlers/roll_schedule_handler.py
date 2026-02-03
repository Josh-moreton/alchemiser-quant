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
from the_alchemiser.shared.options.adapters import (
    HedgeHistoryRepository,
    HedgePositionsRepository,
)
from the_alchemiser.shared.options.constants import (
    CRITICAL_DTE_THRESHOLD,
    SMOOTHING_HEDGE_TEMPLATE,
    TAIL_HEDGE_TEMPLATE,
)
from the_alchemiser.shared.options.schemas.hedge_history_record import HedgeAction

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.events import EventBus

logger = get_logger(__name__)

# Account ID for hedge history audit trail records
# In production, set HEDGE_ACCOUNT_ID environment variable to actual account identifier
HEDGE_ACCOUNT_ID = os.environ.get("HEDGE_ACCOUNT_ID", "default")


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

        # Initialize DynamoDB repository for hedge history
        history_table_name = os.environ.get("HEDGE_HISTORY_TABLE_NAME", "")
        self._history_repo = (
            HedgeHistoryRepository(history_table_name) if history_table_name else None
        )

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

    def handle_scheduled_event(  # noqa: C901
        self, correlation_id: str | None = None
    ) -> dict[str, Any]:
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
                    assignment_risk = self._check_assignment_risk(position, correlation_id)
                    if assignment_risk:
                        assignment_risks += 1

                # Initialize roll decision variables
                should_roll = False
                roll_reason = None

                # Determine roll threshold based on template
                if template == "smoothing":
                    # Fixed cadence: check days since entry
                    should_roll = self._should_roll_smoothing(position, today)
                    if should_roll:
                        roll_reason = "cadence_due"

                    # Check enhanced spread roll triggers (FR-8)
                    if not should_roll:
                        should_roll, roll_reason = self._check_spread_width_value(position)
                    if not should_roll:
                        should_roll, roll_reason = self._check_spread_delta_drift(position)

                else:
                    # DTE-based: check if below roll trigger
                    if dte < self._tail_template.roll_trigger_dte:
                        should_roll = True
                        if dte < CRITICAL_DTE_THRESHOLD:
                            roll_reason = "dte_critical"
                        else:
                            roll_reason = "dte_threshold"

                    # Check enhanced tail roll triggers (FR-8)
                    if not should_roll:
                        should_roll, roll_reason = self._check_delta_drift(position)
                    if not should_roll:
                        should_roll, roll_reason = self._check_extrinsic_decay(position)

                # Trigger roll if any condition met
                if should_roll and roll_reason:
                    self._trigger_roll(position, dte, correlation_id, roll_reason)
                    rolls_triggered += 1
                elif should_roll:
                    # Fallback for legacy path
                    self._trigger_roll(position, dte, correlation_id)
                    rolls_triggered += 1

            logger.info(
                "Hedge roll check completed",
                correlation_id=correlation_id,
                positions_checked=len(positions),
                rolls_triggered=rolls_triggered,
                assignment_risks=assignment_risks,
            )

            # Record EVALUATION_COMPLETED to audit trail
            self._record_evaluation_completed(correlation_id, len(positions), rolls_triggered)

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

        # Cast to expected type for mypy
        return list(positions) if positions else []

    def _trigger_roll(
        self,
        position: dict[str, Any],
        current_dte: int,
        correlation_id: str,
        roll_reason: str | None = None,
    ) -> None:
        """Trigger a roll for an expiring position.

        Args:
            position: Hedge position data
            current_dte: Current days to expiry
            correlation_id: Correlation ID for tracing
            roll_reason: Optional explicit roll reason (FR-8 enhancement)

        """
        hedge_id = position.get("hedge_id", f"hedge-{uuid.uuid4()}")
        option_symbol = position.get("option_symbol", "")
        underlying = position.get("underlying_symbol", "QQQ")
        contracts = position.get("contracts", 1)
        template = position.get("hedge_template", "tail_first")

        # Determine roll reason (use provided reason or infer from DTE/template)
        if roll_reason is None:
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

            days_held: int = (today - entry_date).days

            # Roll if held >= 21 days
            should_roll: bool = days_held >= self._smoothing_template.roll_cadence_days
            return should_roll

        except (ValueError, AttributeError) as e:
            logger.warning(
                "Failed to parse entry date for smoothing roll check",
                position_id=position.get("hedge_id"),
                entry_date=entry_date_str,
                error=str(e),
            )
            return False

    def _check_assignment_risk(
        self, position: dict[str, Any], correlation_id: str | None = None
    ) -> bool:
        """Check for assignment risk on short leg of spread (FR-5.3).

        Args:
            position: Hedge position data (must be a spread)
            correlation_id: Correlation ID for tracing (propagated to audit trail)

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

                # Record assignment detection to audit trail (FR-8 enhancement)
                self._record_assignment_detected(
                    hedge_id=hedge_id,
                    short_leg_symbol=short_symbol,
                    short_delta=str(short_delta),
                    correlation_id=correlation_id or f"assignment-risk-{hedge_id}",
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

        try:
            self._history_repo.record_action(
                account_id=HEDGE_ACCOUNT_ID,
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

        try:
            self._history_repo.record_action(
                account_id=HEDGE_ACCOUNT_ID,
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

    def _check_delta_drift(self, position: dict[str, Any]) -> tuple[bool, str | None]:
        """Check for delta drift beyond threshold (FR-8 enhancement).

        Args:
            position: Hedge position data

        Returns:
            Tuple of (should_roll, roll_reason)

        """
        from decimal import Decimal

        current_delta_str = position.get("current_delta")
        entry_delta_str = position.get("entry_delta")

        if not current_delta_str or not entry_delta_str:
            return False, None

        try:
            current_delta = Decimal(str(current_delta_str))
            entry_delta = Decimal(str(entry_delta_str))
            delta_drift = abs(current_delta - entry_delta)

            # Import threshold from constants
            from the_alchemiser.shared.options.constants import TAIL_DELTA_DRIFT_THRESHOLD

            if delta_drift > TAIL_DELTA_DRIFT_THRESHOLD:
                if abs(current_delta) > abs(entry_delta):
                    # Position moved ITM - delta increased
                    roll_reason = "delta_drift_itm"
                else:
                    # Position moved further OTM - delta decreased
                    roll_reason = "delta_drift_otm"

                logger.info(
                    "Delta drift detected - roll recommended",
                    hedge_id=position.get("hedge_id"),
                    entry_delta=str(entry_delta),
                    current_delta=str(current_delta),
                    drift=str(delta_drift),
                    threshold=str(TAIL_DELTA_DRIFT_THRESHOLD),
                )
                return True, roll_reason

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to check delta drift",
                position_id=position.get("hedge_id"),
                error=str(e),
            )

        return False, None

    def _check_extrinsic_decay(self, position: dict[str, Any]) -> tuple[bool, str | None]:
        """Check for extrinsic value decay below threshold (FR-8 enhancement).

        Args:
            position: Hedge position data

        Returns:
            Tuple of (should_roll, roll_reason)

        """
        from decimal import Decimal

        current_price_str = position.get("current_price")
        entry_price_str = position.get("entry_price")
        strike_price_str = position.get("strike_price")
        underlying_symbol = position.get("underlying_symbol", "")

        if not all([current_price_str, entry_price_str, strike_price_str]):
            return False, None

        try:
            from the_alchemiser.shared.options.constants import (
                DEFAULT_ETF_PRICE_FALLBACK,
                DEFAULT_ETF_PRICES,
                TAIL_EXTRINSIC_DECAY_THRESHOLD,
            )

            current_price = Decimal(str(current_price_str))
            entry_price = Decimal(str(entry_price_str))
            strike_price = Decimal(str(strike_price_str))

            # Get underlying price (use fallback if not available)
            underlying_price = DEFAULT_ETF_PRICES.get(underlying_symbol, DEFAULT_ETF_PRICE_FALLBACK)

            # Calculate intrinsic value for put option
            intrinsic_value = max(strike_price - underlying_price, Decimal("0"))

            # Calculate extrinsic value
            extrinsic_value = current_price - intrinsic_value

            # Check if extrinsic value fell below threshold
            if extrinsic_value < (entry_price * TAIL_EXTRINSIC_DECAY_THRESHOLD):
                logger.info(
                    "Extrinsic value decay detected - roll recommended",
                    hedge_id=position.get("hedge_id"),
                    entry_price=str(entry_price),
                    current_price=str(current_price),
                    extrinsic_value=str(extrinsic_value),
                    threshold=str(entry_price * TAIL_EXTRINSIC_DECAY_THRESHOLD),
                )
                return True, "extrinsic_decay"

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to check extrinsic value decay",
                position_id=position.get("hedge_id"),
                error=str(e),
            )

        return False, None

    def _check_spread_width_value(self, position: dict[str, Any]) -> tuple[bool, str | None]:
        """Check for spread width value decay (FR-8 enhancement).

        Args:
            position: Hedge position data (must be a spread)

        Returns:
            Tuple of (should_roll, roll_reason)

        """
        from decimal import Decimal

        if not position.get("is_spread", False):
            return False, None

        long_price_str = position.get("current_price")
        short_price_str = position.get("short_leg_current_price")
        long_strike_str = position.get("strike_price")
        short_strike_str = position.get("short_leg_strike")

        if not all([long_price_str, short_price_str, long_strike_str, short_strike_str]):
            return False, None

        try:
            from the_alchemiser.shared.options.constants import (
                SPREAD_WIDTH_VALUE_THRESHOLD,
            )

            long_price = Decimal(str(long_price_str))
            short_price = Decimal(str(short_price_str))
            long_strike = Decimal(str(long_strike_str))
            short_strike = Decimal(str(short_strike_str))

            # Calculate spread metrics
            max_width = long_strike - short_strike
            current_spread_value = long_price - short_price

            # Check if spread value decayed significantly
            if current_spread_value < (max_width * SPREAD_WIDTH_VALUE_THRESHOLD):
                logger.info(
                    "Spread width value decay detected - roll recommended",
                    hedge_id=position.get("hedge_id"),
                    max_width=str(max_width),
                    current_spread_value=str(current_spread_value),
                    threshold=str(max_width * SPREAD_WIDTH_VALUE_THRESHOLD),
                )
                return True, "width_value_decay"

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to check spread width value",
                position_id=position.get("hedge_id"),
                error=str(e),
            )

        return False, None

    def _check_spread_delta_drift(self, position: dict[str, Any]) -> tuple[bool, str | None]:
        """Check for delta drift on spread legs (FR-8 enhancement).

        Args:
            position: Hedge position data (must be a spread)

        Returns:
            Tuple of (should_roll, roll_reason)

        """
        from decimal import Decimal

        if not position.get("is_spread", False):
            return False, None

        long_delta_str = position.get("current_delta")
        short_delta_str = position.get("short_leg_current_delta")

        if not long_delta_str or not short_delta_str:
            return False, None

        try:
            from the_alchemiser.shared.options.constants import (
                SPREAD_LONG_DELTA_THRESHOLD,
                SPREAD_SHORT_DELTA_THRESHOLD,
            )

            long_delta = Decimal(str(long_delta_str))
            short_delta = Decimal(str(short_delta_str))

            # Check long leg delta drift (deep ITM warning)
            if abs(long_delta) > SPREAD_LONG_DELTA_THRESHOLD:
                logger.info(
                    "Long leg delta drift detected - roll recommended",
                    hedge_id=position.get("hedge_id"),
                    long_delta=str(long_delta),
                    threshold=str(SPREAD_LONG_DELTA_THRESHOLD),
                )
                return True, "long_leg_delta_drift"

            # Check short leg delta drift (assignment risk warning)
            # Note: Critical assignment risk (>0.80) is handled separately
            if abs(short_delta) > SPREAD_SHORT_DELTA_THRESHOLD:
                logger.info(
                    "Short leg delta drift detected - roll recommended",
                    hedge_id=position.get("hedge_id"),
                    short_delta=str(short_delta),
                    threshold=str(SPREAD_SHORT_DELTA_THRESHOLD),
                )
                return True, "short_leg_delta_drift"

        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to check spread delta drift",
                position_id=position.get("hedge_id"),
                error=str(e),
            )

        return False, None

    def _record_assignment_detected(
        self,
        hedge_id: str,
        short_leg_symbol: str,
        short_delta: str,
        correlation_id: str,
    ) -> None:
        """Record ASSIGNMENT_DETECTED action to audit trail (FR-8 enhancement).

        Args:
            hedge_id: Hedge identifier
            short_leg_symbol: Short leg OCC symbol
            short_delta: Short leg delta value
            correlation_id: Correlation ID for tracing

        """
        if not self._history_repo:
            return

        try:
            self._history_repo.record_action(
                account_id=HEDGE_ACCOUNT_ID,
                action=HedgeAction.ASSIGNMENT_DETECTED,
                hedge_id=hedge_id,
                correlation_id=correlation_id,
                underlying_symbol="",  # Not critical for this action
                option_symbol=short_leg_symbol,
                details={
                    "short_delta": short_delta,
                    "threshold": str(self._smoothing_template.assignment_risk_delta_threshold),
                    "detection_method": "automated_roll_check",
                },
            )
            logger.info(
                "Assignment detection recorded to audit trail",
                hedge_id=hedge_id,
                action="ASSIGNMENT_DETECTED",
            )
        except Exception as e:
            # Don't fail the check if audit trail write fails
            logger.error(
                "Failed to record assignment detection to audit trail",
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )
