#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""
        if self.additional_data is None:
            # Use object.__setattr__ since the dataclass is frozen
            object.__setattr__(self, "additional_data", {})

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
            "timestamp": datetime.now(UTC).isoformat(),
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
