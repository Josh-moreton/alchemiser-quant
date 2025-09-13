#!/usr/bin/env python3
"""Business Unit: shared | Status: legacy

Legacy mapping utilities for summary DTOs.

This module provides backward compatibility for existing imports. New code
should use the utilities in shared.mappers.execution_summary_mapping instead.
"""

from __future__ import annotations

from typing import Any

# Import the actual implementation from the proper location
from the_alchemiser.shared.mappers.execution_summary_mapping import allocation_comparison_to_dict

__all__ = ["allocation_comparison_to_dict"]