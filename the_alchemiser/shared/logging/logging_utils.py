"""Business Unit: shared | Status: deprecated.

DEPRECATED: This module has been replaced by structlog-based logging.

This file is maintained for minimal backward compatibility only. New code should import from:
- the_alchemiser.shared.logging (preferred - public API)

For structlog usage, see docs/structlog_usage.md
"""

from __future__ import annotations

# Re-export core functions from new structlog-based API for backward compatibility
from . import get_logger
from .config import (
    configure_application_logging,
    configure_production_logging,
    configure_test_logging,
)
from .context import (
    generate_request_id,
    get_error_id,
    get_request_id,
    set_error_id,
    set_request_id,
)

__all__ = [
    "configure_application_logging",
    "configure_production_logging",
    "configure_test_logging",
    "generate_request_id",
    "get_error_id",
    "get_logger",
    "get_request_id",
    "set_error_id",
    "set_request_id",
]
