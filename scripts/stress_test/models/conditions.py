"""Business Unit: utilities | Status: current.

Market condition model for stress testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MarketCondition:
    """Represents a specific market condition scenario.

    Each scenario has a unique identifier and specific RSI/price ranges
    for all symbols used in the strategies.
    """

    scenario_id: str
    description: str
    rsi_range: tuple[float, float]  # (min, max) for RSI values
    price_multiplier: float  # Multiplier for base prices (e.g., 0.8 = -20%, 1.2 = +20%)
    volatility_regime: str  # "low", "medium", "high"
    metadata: dict[str, Any] = field(default_factory=dict)
