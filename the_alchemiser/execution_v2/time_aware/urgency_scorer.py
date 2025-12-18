"""Business Unit: Execution | Status: current.

Urgency scorer for time-aware execution framework.

Computes a 0.0-1.0 urgency score based on:
- Time remaining until deadline
- Quantity remaining to fill
- Current execution phase
- Policy-specific urgency curves

The urgency score drives peg aggressiveness and order sizing decisions.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from the_alchemiser.execution_v2.time_aware.models import ExecutionPhase, PegType


@dataclass
class UrgencyFactors:
    """Breakdown of urgency score components for debugging/logging."""

    time_urgency: float  # 0-1 based on time remaining
    fill_urgency: float  # 0-1 based on unfilled quantity
    phase_urgency: float  # 0-1 based on current phase
    combined_score: float  # Final weighted score


class UrgencyScorer:
    """Computes urgency scores for execution decisions.

    The scorer implements a multi-factor urgency model:

    1. Time Urgency: Exponential ramp as deadline approaches
       - Linear from 0.0 to 0.5 during first 80% of session
       - Exponential ramp from 0.5 to 1.0 in final 20%

    2. Fill Urgency: Based on remaining quantity
       - Low urgency if on track
       - High urgency if behind schedule

    3. Phase Urgency: Inherent urgency of current phase
       - OPEN_AVOIDANCE: 0.0
       - PASSIVE_ACCUMULATION: 0.2
       - URGENCY_RAMP: 0.5
       - DEADLINE_CLOSE: 0.9

    Factors are combined with configurable weights.
    """

    def __init__(
        self,
        time_weight: float = 0.5,
        fill_weight: float = 0.3,
        phase_weight: float = 0.2,
        time_ramp_exponent: float = 2.5,  # Controls steepness of time ramp
    ) -> None:
        """Initialize urgency scorer.

        Args:
            time_weight: Weight for time-based urgency (0-1)
            fill_weight: Weight for fill-based urgency (0-1)
            phase_weight: Weight for phase-based urgency (0-1)
            time_ramp_exponent: Exponent for exponential time ramp

        """
        total = time_weight + fill_weight + phase_weight
        self.time_weight = time_weight / total
        self.fill_weight = fill_weight / total
        self.phase_weight = phase_weight / total
        self.time_ramp_exponent = time_ramp_exponent

    def compute_urgency(
        self,
        current_time: datetime,
        deadline: datetime,
        session_start: datetime,
        filled_ratio: float,
        current_phase: ExecutionPhase,
    ) -> UrgencyFactors:
        """Compute urgency score and component breakdown.

        Args:
            current_time: Current time (UTC)
            deadline: Execution deadline (UTC)
            session_start: Trading session start (UTC)
            filled_ratio: Fraction already filled (0.0 to 1.0)
            current_phase: Current execution phase

        Returns:
            UrgencyFactors with component breakdown and combined score

        """
        time_urgency = self._compute_time_urgency(current_time, deadline, session_start)
        fill_urgency = self._compute_fill_urgency(
            filled_ratio, current_time, deadline, session_start
        )
        phase_urgency = self._compute_phase_urgency(current_phase)

        combined = (
            self.time_weight * time_urgency
            + self.fill_weight * fill_urgency
            + self.phase_weight * phase_urgency
        )

        return UrgencyFactors(
            time_urgency=time_urgency,
            fill_urgency=fill_urgency,
            phase_urgency=phase_urgency,
            combined_score=min(1.0, max(0.0, combined)),
        )

    def _compute_time_urgency(
        self,
        current_time: datetime,
        deadline: datetime,
        session_start: datetime,
    ) -> float:
        """Compute time-based urgency.

        Uses a piecewise function:
        - Linear from 0.0 to 0.5 during first 80% of session
        - Exponential ramp from 0.5 to 1.0 in final 20%

        This reflects the reality that urgency should accelerate
        as the close approaches, but remain low during most of the day.
        """
        total_seconds = (deadline - session_start).total_seconds()
        if total_seconds <= 0:
            return 1.0

        elapsed_seconds = (current_time - session_start).total_seconds()
        if elapsed_seconds < 0:
            return 0.0

        progress = elapsed_seconds / total_seconds
        progress = min(1.0, max(0.0, progress))

        # Piecewise urgency curve
        LINEAR_PHASE_END = 0.8
        LINEAR_PHASE_URGENCY = 0.5

        if progress <= LINEAR_PHASE_END:
            # Linear phase: 0 to 0.5
            return (progress / LINEAR_PHASE_END) * LINEAR_PHASE_URGENCY
        # Exponential phase: 0.5 to 1.0
        remaining_progress = (progress - LINEAR_PHASE_END) / (1 - LINEAR_PHASE_END)
        exponential_factor = math.pow(remaining_progress, self.time_ramp_exponent)
        return LINEAR_PHASE_URGENCY + (1 - LINEAR_PHASE_URGENCY) * exponential_factor

    def _compute_fill_urgency(
        self,
        filled_ratio: float,
        current_time: datetime,
        deadline: datetime,
        session_start: datetime,
    ) -> float:
        """Compute fill-based urgency.

        Compares actual fill progress against expected progress.
        If behind schedule, urgency increases.
        If ahead of schedule, urgency decreases.
        """
        total_seconds = (deadline - session_start).total_seconds()
        if total_seconds <= 0:
            return 1.0 if filled_ratio < 1.0 else 0.0

        elapsed_seconds = (current_time - session_start).total_seconds()
        time_progress = min(1.0, max(0.0, elapsed_seconds / total_seconds))

        # Expected fill ratio should track time progress
        # (assumes linear fill rate as baseline)
        expected_fill = time_progress

        # Deviation from expected
        fill_deficit = expected_fill - filled_ratio

        if fill_deficit <= 0:
            # Ahead of schedule: low fill urgency
            return 0.0
        # Behind schedule: urgency proportional to deficit
        # Cap at 1.0 when completely unfilled at deadline
        return min(1.0, fill_deficit * 2)

    def _compute_phase_urgency(self, phase: ExecutionPhase) -> float:
        """Compute phase-based urgency."""
        phase_urgency_map = {
            ExecutionPhase.OPEN_AVOIDANCE: 0.0,
            ExecutionPhase.PASSIVE_ACCUMULATION: 0.2,
            ExecutionPhase.URGENCY_RAMP: 0.5,
            ExecutionPhase.DEADLINE_CLOSE: 0.9,
            ExecutionPhase.MARKET_CLOSED: 0.0,
        }
        return phase_urgency_map.get(phase, 0.0)

    def suggest_peg_type(
        self,
        urgency: float,
        allowed_pegs: frozenset[PegType],
        current_phase: ExecutionPhase,
    ) -> PegType:
        """Suggest appropriate peg type based on urgency.

        Maps urgency score to peg aggressiveness within allowed pegs.

        Args:
            urgency: Combined urgency score (0.0 to 1.0)
            allowed_pegs: Pegs permitted by current phase config
            current_phase: Current execution phase

        Returns:
            Recommended PegType

        """
        # Ordered from most passive to most aggressive
        peg_aggressiveness = [
            PegType.FAR_TOUCH,
            PegType.MID,
            PegType.NEAR_TOUCH,
            PegType.INSIDE_25,
            PegType.INSIDE_50,
            PegType.INSIDE_75,
            PegType.INSIDE_90,
            PegType.CROSS,
            PegType.MARKET,
        ]

        # Filter to allowed pegs, preserving order
        available = [p for p in peg_aggressiveness if p in allowed_pegs]
        if not available:
            return PegType.MID  # Fallback

        # Map urgency to index in available pegs
        index = int(urgency * (len(available) - 1))
        index = min(index, len(available) - 1)

        return available[index]

    def suggest_order_size_fraction(
        self,
        urgency: float,
        max_fraction: Decimal,
        remaining_quantity: Decimal,
        min_size: int = 1,
    ) -> Decimal:
        """Suggest child order size based on urgency.

        Higher urgency = larger child orders (to complete faster).
        Lower urgency = smaller child orders (reduce market impact).

        Args:
            urgency: Combined urgency score (0.0 to 1.0)
            max_fraction: Maximum allowed fraction of remaining qty
            remaining_quantity: Quantity still to fill
            min_size: Minimum order size

        Returns:
            Suggested order quantity as Decimal

        """
        # Base fraction scales with urgency
        # At urgency 0: use 10% of max_fraction
        # At urgency 1: use 100% of max_fraction
        min_fraction = Decimal("0.10")
        fraction_range = Decimal("1") - min_fraction

        effective_fraction = min_fraction + fraction_range * Decimal(str(urgency))
        suggested_fraction = min(effective_fraction, max_fraction)

        suggested_qty = remaining_quantity * suggested_fraction

        # Ensure minimum size
        return max(Decimal(str(min_size)), suggested_qty.quantize(Decimal("1")))
