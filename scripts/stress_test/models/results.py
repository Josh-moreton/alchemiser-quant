"""Business Unit: utilities | Status: current.

Result models for stress testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StressTestResult:
    """Result from a single stress test scenario."""

    scenario_id: str
    timestamp: datetime
    success: bool
    trades_executed: int
    error_message: str | None = None
    error_type: str | None = None
    portfolio_value: float | None = None
    execution_time_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
