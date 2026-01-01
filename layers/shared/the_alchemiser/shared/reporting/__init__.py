"""Business Unit: shared | Status: current.

Shared reporting module for QuantStats tearsheet generation.

Provides a unified interface for generating performance reports that can be
used by both local backtest runs and production Lambda functions.
"""

from the_alchemiser.shared.reporting.quantstats_report import (
    ExtendedMetrics,
    calculate_extended_metrics,
    generate_tearsheet,
    generate_tearsheet_from_trades,
)

__all__ = [
    "ExtendedMetrics",
    "calculate_extended_metrics",
    "generate_tearsheet",
    "generate_tearsheet_from_trades",
]
