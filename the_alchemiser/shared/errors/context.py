"""Business Unit: shared | Status: current.

Error context data for error handling.

This module re-exports the unified ErrorContextDTO for backward compatibility.
"""

from __future__ import annotations

from ..dto.error_context_dto import ErrorContextDTO

# Backward compatibility alias
ErrorContextData = ErrorContextDTO
