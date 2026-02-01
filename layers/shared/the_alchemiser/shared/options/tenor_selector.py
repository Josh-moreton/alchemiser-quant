"""Business Unit: shared | Status: current.

Dynamic tenor selection for options hedging.

Selects optimal tenor (DTE) based on:
- Term structure analysis
- IV percentile
- Tenor ladder approach (60-90 DTE and 120-180 DTE)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class TenorRecommendation:
    """Tenor selection recommendation."""

    primary_dte: int  # Primary tenor target
    secondary_dte: int | None  # Optional secondary tenor for ladder
    strategy: Literal["single", "ladder"]  # Single tenor or ladder split
    rationale: str  # Explanation for selection


class TenorSelector:
    """Selects optimal tenor for options hedging based on market conditions."""

    def __init__(
        self,
        short_min_dte: int = 60,
        short_max_dte: int = 90,
        long_min_dte: int = 120,
        long_max_dte: int = 180,
        iv_percentile_threshold: Decimal = Decimal("0.7"),
    ) -> None:
        """Initialize tenor selector.

        Args:
            short_min_dte: Minimum DTE for short tenor range
            short_max_dte: Maximum DTE for short tenor range
            long_min_dte: Minimum DTE for long tenor range
            long_max_dte: Maximum DTE for long tenor range
            iv_percentile_threshold: IV percentile above which to prefer longer tenors

        """
        self._short_min_dte = short_min_dte
        self._short_max_dte = short_max_dte
        self._long_min_dte = long_min_dte
        self._long_max_dte = long_max_dte
        self._iv_percentile_threshold = iv_percentile_threshold

    def select_tenor(
        self,
        current_vix: Decimal,
        iv_percentile: Decimal | None = None,
        term_structure_slope: Decimal | None = None,
        *,
        use_ladder: bool = True,
    ) -> TenorRecommendation:
        """Select optimal tenor based on market conditions.

        Args:
            current_vix: Current VIX level
            iv_percentile: IV percentile (0-1), if available
            term_structure_slope: Term structure slope (positive = contango)
            use_ladder: Whether to use ladder strategy (split across tenors)

        Returns:
            TenorRecommendation with tenor targets and strategy

        """
        # Default: midpoint of short range
        primary_dte = (self._short_min_dte + self._short_max_dte) // 2
        secondary_dte = None
        strategy: Literal["single", "ladder"] = "single"
        rationale = f"Default single tenor at {primary_dte} DTE"

        # High IV scenario: prefer longer tenors for better theta efficiency
        if iv_percentile is not None and iv_percentile > self._iv_percentile_threshold:
            primary_dte = (self._long_min_dte + self._long_max_dte) // 2
            rationale = f"High IV percentile ({iv_percentile:.1%}), using longer tenor at {primary_dte} DTE for theta efficiency"
            logger.info(
                "High IV percentile detected, selecting longer tenor",
                iv_percentile=str(iv_percentile),
                primary_dte=primary_dte,
            )
        # Rich VIX: extend tenor to reduce cost
        elif current_vix > Decimal("35"):
            primary_dte = (self._long_min_dte + self._long_max_dte) // 2
            rationale = (
                f"Rich VIX ({current_vix}), using longer tenor at {primary_dte} DTE to reduce cost"
            )
            logger.info(
                "Rich VIX detected, selecting longer tenor",
                vix=str(current_vix),
                primary_dte=primary_dte,
            )
        # Tenor ladder: split between short and long for diversification
        elif use_ladder:
            primary_dte = (self._short_min_dte + self._short_max_dte) // 2
            secondary_dte = (self._long_min_dte + self._long_max_dte) // 2
            strategy = "ladder"
            rationale = f"Ladder strategy: split between {primary_dte} DTE (short) and {secondary_dte} DTE (long)"
            logger.info(
                "Using tenor ladder strategy",
                primary_dte=primary_dte,
                secondary_dte=secondary_dte,
            )

        # Term structure adjustment (if available)
        if term_structure_slope is not None:
            if term_structure_slope > Decimal("0.1") and strategy == "single":
                # Steep contango: favor shorter tenors (less theta decay)
                primary_dte = self._short_min_dte
                rationale += f" (steep contango {term_structure_slope:.1%}, favoring shorter tenor)"
            elif term_structure_slope < Decimal("-0.05") and strategy == "single":
                # Backwardation: favor longer tenors (capture term premium)
                primary_dte = self._long_max_dte
                rationale += f" (backwardation {term_structure_slope:.1%}, favoring longer tenor)"

        return TenorRecommendation(
            primary_dte=primary_dte,
            secondary_dte=secondary_dte,
            strategy=strategy,
            rationale=rationale,
        )

    def get_dte_range(self, dte_target: int) -> tuple[int, int]:
        """Get DTE range for filtering based on target.

        Args:
            dte_target: Target DTE

        Returns:
            Tuple of (min_dte, max_dte) for filtering

        """
        # Use appropriate range based on target
        if dte_target <= self._short_max_dte:
            return (self._short_min_dte, self._short_max_dte)
        return (self._long_min_dte, self._long_max_dte)
