#!/usr/bin/env python3
"""
Error context data structures for The Alchemiser Trading System.

This module provides standardized error context data structures
for consistent error reporting and tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ErrorContextData:
    """
    Standardized error context data for all error reporting.
    
    This frozen dataclass provides immutable error context information
    that can be safely passed around and serialized.
    """
    
    operation: str
    component: str
    function_name: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    additional_data: dict[str, Any] | None = None
    
    def __post_init__(self) -> None:
        """Post-initialization to handle mutable defaults."""
        if self.additional_data is None:
            # Use object.__setattr__ since the dataclass is frozen
            object.__setattr__(self, 'additional_data', {})
    
    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "operation": self.operation,
            "component": self.component,
            "function_name": self.function_name,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "additional_data": self.additional_data or {},
            "timestamp": datetime.now().isoformat(),
        }


def create_error_context(
    operation: str,
    component: str,
    function_name: str | None = None,
    **kwargs: Any,
) -> ErrorContextData:
    """Factory function to create standardized error context."""
    return ErrorContextData(
        operation=operation,
        component=component,
        function_name=function_name,
        **kwargs,
    )