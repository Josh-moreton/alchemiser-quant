"""Business Unit: shared/types; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.constants import PERCENTAGE_RANGE
from the_alchemiser.shared.utils.validation_utils import validate_decimal_range


@dataclass(frozen=True)
class Percentage:
    """Immutable percentage value object with validation.

    Represents a percentage value stored internally as a Decimal in range [0, 1]
    where 0 = 0%, 0.5 = 50%, and 1.0 = 100%. Uses Decimal for exact precision
    per financial-grade guardrails.

    Attributes:
        value: Percentage as Decimal in range [0, 1] (inclusive)

    Examples:
        >>> # Create from internal value (0.0 - 1.0)
        >>> p = Percentage(Decimal("0.5"))  # 50%
        >>> p.to_percent()
        Decimal('50')

        >>> # Create from percentage notation (0.0 - 100.0)
        >>> p = Percentage.from_percent(75.0)  # 75%
        >>> p.value
        Decimal('0.75')

        >>> # Invalid values raise ValueError
        >>> Percentage(Decimal("-0.1"))  # Raises ValueError
        >>> Percentage.from_percent(150.0)  # Raises ValueError

    Raises:
        ValueError: If value is outside range [0, 1]

    Note:
        This is a frozen dataclass - immutable after construction.
        All arithmetic must be done on the .value attribute or via helper methods.

    """

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate that the percentage value is within acceptable bounds."""
        validate_decimal_range(
            self.value,
            PERCENTAGE_RANGE[0],
            PERCENTAGE_RANGE[1],
            "Percentage",
        )

    @classmethod
    def from_percent(cls, percent: float) -> Percentage:
        """Create a Percentage from a percentage value (e.g. 50.0 for 50%).

        Args:
            percent: Percentage value in range [0.0, 100.0] (e.g., 50.0 = 50%)

        Returns:
            Percentage object with value normalized to [0, 1] range

        Raises:
            ValueError: If percent is outside [0.0, 100.0] range

        Examples:
            >>> Percentage.from_percent(0.0)    # 0%
            Percentage(value=Decimal('0'))
            >>> Percentage.from_percent(50.0)   # 50%
            Percentage(value=Decimal('0.5'))
            >>> Percentage.from_percent(100.0)  # 100%
            Percentage(value=Decimal('1'))

        Note:
            Float is converted to Decimal via str() to avoid precision issues.
            E.g., from_percent(33.33) becomes Decimal('0.3333'), not 0.33330000...

        """
        return cls(Decimal(str(percent)) / Decimal("100"))

    def to_percent(self) -> Decimal:
        """Convert to percentage representation (e.g. 0.5 -> 50.0).

        Returns:
            Decimal in range [0, 100] representing percentage notation

        Examples:
            >>> Percentage(Decimal("0")).to_percent()
            Decimal('0')
            >>> Percentage(Decimal("0.5")).to_percent()
            Decimal('50')
            >>> Percentage(Decimal("1")).to_percent()
            Decimal('100')

        Note:
            Result is exact Decimal multiplication, no rounding applied.
            E.g., Decimal("0.3333") * 100 = Decimal("33.33")

        """
        return self.value * Decimal("100")
