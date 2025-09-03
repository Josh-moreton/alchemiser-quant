from __future__ import annotations

"""Business Unit: shared | Status: current..
"""

#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    summary: dict[str, Any]  # Position summary


class EnrichedPositionsView(Result):
    """DTO for enriched positions list response."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    positions: list[EnrichedPositionView]


# Backward compatibility aliases - will be removed in future version
EnrichedOrderDTO = EnrichedOrderView
OpenOrdersDTO = OpenOrdersView
EnrichedPositionDTO = EnrichedPositionView
EnrichedPositionsDTO = EnrichedPositionsView
