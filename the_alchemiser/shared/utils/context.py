#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Error context data structures for The Alchemiser Trading System.

This module provides standardized error context data structures
for consistent error reporting and tracking.
"""

from __future__ import annotations

from ..dto.error_context_dto import ErrorContextDTO


def create_error_context(
    operation: str,
    component: str,
    function_name: str | None = None,
    **kwargs: str | int | float | bool,
) -> ErrorContextDTO:
    """Create standardized error context."""
    return ErrorContextDTO.create(
        operation=operation,
        component=component,
        function_name=function_name,
        **kwargs,
    )
