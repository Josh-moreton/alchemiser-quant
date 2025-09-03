"""Business Unit: shared | Status: current.

Utility functions and helpers.

This module provides cross-cutting utility functions including account data processing,
error handling, context management, and other helper functions that support
operations across all business units.
"""

from __future__ import annotations

__all__: list[str] = []

# Import from new locations where files were moved
from ..types.exceptions import *
from .account_utils import (
    calculate_position_target_deltas,
    extract_basic_account_metrics,
    extract_comprehensive_account_data,
    extract_current_position_values,
)

# Cross-cutting utilities and error handling
from .context import ErrorContextData, create_error_context
from .error_handling import *  # Legacy deprecated
from .error_reporter import *
