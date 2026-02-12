"""Business Unit: notifications | Status: current.

Shared notification session lookup used by multiple handlers.
"""

from __future__ import annotations

import os
from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def get_notification_session(correlation_id: str) -> dict[str, Any] | None:
    """Check if a notification session exists for this correlation_id.

    Args:
        correlation_id: Shared workflow correlation ID.

    Returns:
        Session metadata dict, or None if no session exists.

    """
    table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME", "")
    if not table_name:
        return None

    try:
        from the_alchemiser.shared.services.notification_session_service import (
            NotificationSessionService,
        )

        session_service = NotificationSessionService(table_name=table_name)
        return session_service.get_session(correlation_id)
    except Exception as e:
        logger.warning(
            "Failed to check notification session",
            extra={"correlation_id": correlation_id, "error": str(e)},
        )
        return None
