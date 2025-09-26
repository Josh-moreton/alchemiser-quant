"""Business Unit: execution | Status: current.

Execution idempotency utilities for execution_v2 module.

Provides utilities for ensuring idempotent execution through persistent tracking
of execution attempts and deterministic hash generation for execution plans.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging.logging_utils import log_with_context
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO

if TYPE_CHECKING:
    from the_alchemiser.shared.persistence import LocalFileHandler

logger = logging.getLogger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "execution_v2.utils.execution_idempotency"


class ExecutionIdempotencyStore:
    """Store for tracking execution attempts to ensure idempotent behavior.

    Persists execution attempts keyed by correlation_id and execution_plan_hash
    to prevent duplicate executions when events are replayed.
    """

    def __init__(self, persistence_handler: LocalFileHandler) -> None:
        """Initialize the idempotency store.

        Args:
            persistence_handler: Handler for persistent storage

        """
        self._persistence = persistence_handler
        self._store_key = "execution_attempts"

    def has_been_executed(self, correlation_id: str, execution_plan_hash: str) -> bool:
        """Check if an execution has already been attempted.

        Args:
            correlation_id: Correlation ID from the event
            execution_plan_hash: Hash of the execution plan

        Returns:
            True if execution has been attempted, False otherwise

        """
        try:
            attempts = self._load_attempts()
            key = self._make_key(correlation_id, execution_plan_hash)

            has_executed = key in attempts

            log_with_context(
                logger,
                logging.DEBUG,
                f"Idempotency check: {'found' if has_executed else 'not found'}",
                module=MODULE_NAME,
                action="has_been_executed",
                correlation_id=correlation_id,
                execution_plan_hash=execution_plan_hash,
                result=has_executed,
            )

            return has_executed

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to check execution idempotency: {e}",
                module=MODULE_NAME,
                action="has_been_executed",
                error=str(e),
            )
            # On error, assume not executed to be safe
            return False

    def record_execution_attempt(
        self,
        correlation_id: str,
        execution_plan_hash: str,
        *,
        success: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an execution attempt.

        Args:
            correlation_id: Correlation ID from the event
            execution_plan_hash: Hash of the execution plan
            success: Whether the execution was successful
            metadata: Optional metadata about the execution

        """
        try:
            attempts = self._load_attempts()
            key = self._make_key(correlation_id, execution_plan_hash)

            attempt_record = {
                "correlation_id": correlation_id,
                "execution_plan_hash": execution_plan_hash,
                "success": success,
                "timestamp": str(self._get_current_timestamp()),
                "metadata": metadata or {},
            }

            attempts[key] = attempt_record
            self._save_attempts(attempts)

            log_with_context(
                logger,
                logging.INFO,
                f"Recorded execution attempt: {success=}",
                module=MODULE_NAME,
                action="record_execution_attempt",
                correlation_id=correlation_id,
                execution_plan_hash=execution_plan_hash,
                success=success,
            )

        except Exception as e:
            log_with_context(
                logger,
                logging.ERROR,
                f"Failed to record execution attempt: {e}",
                module=MODULE_NAME,
                action="record_execution_attempt",
                error=str(e),
            )
            # Don't re-raise to avoid breaking execution flow

    def _make_key(self, correlation_id: str, execution_plan_hash: str) -> str:
        """Create a storage key from correlation ID and plan hash."""
        return f"{correlation_id}_{execution_plan_hash}"

    def _load_attempts(self) -> dict[str, Any]:
        """Load execution attempts from persistence."""
        try:
            data = self._persistence.read_text(self._store_key)
            return json.loads(data) if data else {}
        except Exception:
            # Return empty dict if load fails
            return {}

    def _save_attempts(self, attempts: dict[str, Any]) -> None:
        """Save execution attempts to persistence."""
        data = json.dumps(attempts, indent=2)
        self._persistence.write_text(self._store_key, data)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()


def generate_execution_plan_hash(rebalance_plan: RebalancePlanDTO, correlation_id: str) -> str:
    """Generate a deterministic hash for an execution plan.

    Args:
        rebalance_plan: The rebalance plan to hash
        correlation_id: Correlation ID to include in hash

    Returns:
        Hex string hash of the execution plan

    """
    # Create deterministic representation of the plan
    plan_data = {
        "plan_id": rebalance_plan.plan_id,
        "correlation_id": correlation_id,
        "items": [
            {
                "symbol": item.symbol,
                "action": item.action,
                "trade_amount": str(
                    item.trade_amount
                ),  # Convert Decimal to string for deterministic hashing
                "target_weight": str(item.target_weight),
                "current_weight": str(item.current_weight),
            }
            for item in sorted(rebalance_plan.items, key=lambda x: (x.symbol, x.action))
        ],
    }

    # Generate hash
    plan_json = json.dumps(plan_data, sort_keys=True, separators=(",", ":"))
    plan_hash = hashlib.sha256(plan_json.encode("utf-8")).hexdigest()

    log_with_context(
        logger,
        logging.DEBUG,
        f"Generated execution plan hash: {plan_hash[:8]}...",
        module=MODULE_NAME,
        action="generate_execution_plan_hash",
        plan_id=rebalance_plan.plan_id,
        correlation_id=correlation_id,
        hash=plan_hash,
    )

    return plan_hash
