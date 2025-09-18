"""Business Unit: shared | Status: current.

Error context data for error handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ErrorContextData:
    """Context data for error reporting."""

    module: str | None = None
    function: str | None = None
    operation: str | None = None
    correlation_id: str | None = None
    additional_data: dict[str, str | int | bool | None] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "module": self.module,
            "function": self.function,
            "operation": self.operation,
            "correlation_id": self.correlation_id,
            "additional_data": self.additional_data or {},
        }
