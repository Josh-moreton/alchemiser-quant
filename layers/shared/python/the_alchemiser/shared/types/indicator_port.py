"""Business Unit: shared | Status: current.

Indicator port interface for technical indicator providers.

This protocol defines the contract for indicator services, enabling
different implementations (in-process, Lambda-based) to be swapped
transparently by the Strategy module.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator


class IndicatorPort(Protocol):
    """Protocol for technical indicator providers.

    This interface abstracts the indicator computation mechanism,
    allowing Strategy to use either:
    - IndicatorLambdaClient (invokes Indicators Lambda)
    - Local IndicatorService (for testing)

    """

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Get technical indicator for a symbol.

        Args:
            request: IndicatorRequest containing symbol, indicator type,
                and computation parameters

        Returns:
            TechnicalIndicator with computed values

        Raises:
            IndicatorError: If indicator computation fails

        """
        ...
