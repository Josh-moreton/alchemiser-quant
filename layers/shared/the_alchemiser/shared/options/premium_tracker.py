"""Business Unit: shared | Status: current.

Rolling premium spend tracker for options hedging.

Tracks premium spend over a rolling 12-month window and enforces
annual spend caps to prevent excessive hedging costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ..logging import get_logger
from .constants import MAX_ANNUAL_PREMIUM_SPEND_PCT

logger = get_logger(__name__)


@dataclass(frozen=True)
class PremiumSpendRecord:
    """Record of a single premium spend transaction."""

    timestamp: datetime  # When premium was paid
    amount: Decimal  # Premium amount in dollars
    hedge_id: str  # Hedge identifier
    description: str  # Human-readable description


@dataclass(frozen=True)
class SpendCheckResult:
    """Result of checking if proposed spend is within cap.

    Provides detailed information about current spend and capacity.
    """

    is_within_cap: bool  # Whether proposed spend would be within annual cap
    current_spend_12mo: Decimal  # Current rolling 12-month spend
    proposed_spend: Decimal  # Proposed additional spend
    total_spend_after: Decimal  # Total spend if proposal approved
    annual_cap_dollars: Decimal  # Annual cap in dollars
    remaining_capacity: Decimal  # Remaining spend capacity
    current_spend_pct: Decimal  # Current spend as % of NAV
    total_spend_pct: Decimal  # Total spend (after) as % of NAV
    nav: Decimal  # Current portfolio NAV


class PremiumTracker:
    """Tracker for rolling 12-month premium spend.

    Maintains a history of premium payments and enforces annual spend caps.
    Implements fail-closed behavior: refuses hedges when cap would be exceeded.
    """

    def __init__(self) -> None:
        """Initialize tracker with empty history."""
        self._spend_history: list[PremiumSpendRecord] = []

    def add_spend(
        self,
        amount: Decimal,
        hedge_id: str,
        description: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Record a premium spend transaction.

        Args:
            amount: Premium amount in dollars
            hedge_id: Hedge identifier
            description: Human-readable description
            timestamp: Transaction timestamp (defaults to now)

        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        record = PremiumSpendRecord(
            timestamp=timestamp,
            amount=amount,
            hedge_id=hedge_id,
            description=description,
        )

        self._spend_history.append(record)

        logger.info(
            "Recorded premium spend",
            amount=str(amount),
            hedge_id=hedge_id,
            description=description,
            timestamp=timestamp.isoformat(),
        )

    def get_rolling_12mo_spend(
        self,
        as_of: datetime | None = None,
    ) -> Decimal:
        """Calculate rolling 12-month premium spend.

        Args:
            as_of: Calculate as of this timestamp (defaults to now)

        Returns:
            Total premium spend in the 12 months ending at as_of

        """
        if as_of is None:
            as_of = datetime.now(UTC)

        # Calculate 12 months ago
        twelve_months_ago = as_of - timedelta(days=365)

        # Sum all spend in the rolling window
        total_spend = Decimal("0")
        for record in self._spend_history:
            if twelve_months_ago <= record.timestamp <= as_of:
                total_spend += record.amount

        logger.debug(
            "Calculated rolling 12-month spend",
            total_spend=str(total_spend),
            as_of=as_of.isoformat(),
            twelve_months_ago=twelve_months_ago.isoformat(),
            records_counted=sum(
                1 for r in self._spend_history if twelve_months_ago <= r.timestamp <= as_of
            ),
        )

        return total_spend

    def check_spend_within_cap(
        self,
        proposed_spend: Decimal,
        nav: Decimal,
        as_of: datetime | None = None,
    ) -> SpendCheckResult:
        """Check if proposed spend would exceed annual cap.

        Args:
            proposed_spend: Proposed additional premium spend
            nav: Current portfolio NAV
            as_of: Check as of this timestamp (defaults to now)

        Returns:
            SpendCheckResult with detailed breakdown

        """
        if as_of is None:
            as_of = datetime.now(UTC)

        # Get current rolling 12-month spend
        current_spend = self.get_rolling_12mo_spend(as_of)

        # Calculate total spend after proposal
        total_spend_after = current_spend + proposed_spend

        # Calculate annual cap in dollars
        annual_cap_dollars = nav * MAX_ANNUAL_PREMIUM_SPEND_PCT

        # Check if within cap
        is_within_cap = total_spend_after <= annual_cap_dollars

        # Calculate remaining capacity
        remaining_capacity = max(Decimal("0"), annual_cap_dollars - current_spend)

        # Calculate percentages
        current_spend_pct = (current_spend / nav) if nav > 0 else Decimal("0")
        total_spend_pct = (total_spend_after / nav) if nav > 0 else Decimal("0")

        result = SpendCheckResult(
            is_within_cap=is_within_cap,
            current_spend_12mo=current_spend,
            proposed_spend=proposed_spend,
            total_spend_after=total_spend_after,
            annual_cap_dollars=annual_cap_dollars,
            remaining_capacity=remaining_capacity,
            current_spend_pct=current_spend_pct,
            total_spend_pct=total_spend_pct,
            nav=nav,
        )

        logger.info(
            "Checked spend against annual cap",
            is_within_cap=is_within_cap,
            current_spend=str(current_spend),
            proposed_spend=str(proposed_spend),
            total_spend_after=str(total_spend_after),
            annual_cap_dollars=str(annual_cap_dollars),
            remaining_capacity=str(remaining_capacity),
            current_spend_pct=f"{current_spend_pct * 100:.2f}%",
            total_spend_pct=f"{total_spend_pct * 100:.2f}%",
            annual_cap_pct=f"{MAX_ANNUAL_PREMIUM_SPEND_PCT * 100:.1f}%",
        )

        return result

    def load_history_from_records(
        self,
        records: list[PremiumSpendRecord],
    ) -> None:
        """Load spend history from a list of records.

        Useful for restoring state from persistence.

        Args:
            records: List of PremiumSpendRecord to load

        """
        self._spend_history = sorted(records, key=lambda r: r.timestamp)

        logger.info(
            "Loaded premium spend history",
            record_count=len(records),
            oldest_record=(
                self._spend_history[0].timestamp.isoformat() if self._spend_history else None
            ),
            newest_record=(
                self._spend_history[-1].timestamp.isoformat() if self._spend_history else None
            ),
        )

    def get_spend_history(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[PremiumSpendRecord]:
        """Get spend history within a date range.

        Args:
            start_date: Start of range (inclusive, defaults to earliest record)
            end_date: End of range (inclusive, defaults to latest record)

        Returns:
            List of PremiumSpendRecord within the date range

        """
        filtered = self._spend_history

        if start_date is not None:
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if end_date is not None:
            filtered = [r for r in filtered if r.timestamp <= end_date]

        return filtered
