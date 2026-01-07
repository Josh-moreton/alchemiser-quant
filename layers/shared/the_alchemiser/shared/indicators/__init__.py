"""Business Unit: shared | Status: current.

Indicator configuration and partial-bar support utilities.

This module provides configuration and metadata for technical indicators,
including partial-bar eligibility classification for intraday evaluation.
"""

from .partial_bar_config import (
    InputRequirement,
    PartialBarEligibility,
    PartialBarIndicatorConfig,
    get_all_indicator_configs,
    get_indicator_config,
    is_eligible_for_partial_bar,
)

__all__ = [
    "InputRequirement",
    "PartialBarEligibility",
    "PartialBarIndicatorConfig",
    "get_all_indicator_configs",
    "get_indicator_config",
    "is_eligible_for_partial_bar",
]
