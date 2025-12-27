"""Business Unit: data_quality_monitor | Status: current.

DynamoDB session manager for validation workflow tracking.

Persists and retrieves validation sessions to coordinate batch processing
across multiple Lambda invocations.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, cast

import boto3

from the_alchemiser.shared.errors import AlchemiserError
from the_alchemiser.shared.logging import get_logger

from .schemas import (
    BatchStatus,
    SessionStatus,
    SymbolValidationResult,
    ValidationBatch,
    ValidationSession,
)

logger = get_logger(__name__)


class SessionManagerError(AlchemiserError):
    """Raised when session management operations fail."""


class ValidationSessionManager:
    """Manages validation session state in DynamoDB."""

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize session manager.

        Args:
            table_name: DynamoDB table name (defaults to env var)

        """
        self.table_name = table_name or os.environ.get(
            "VALIDATION_SESSIONS_TABLE",
            "alchemiser-data-quality-validation-sessions",
        )
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def create_session(
        self,
        session_id: str,
        correlation_id: str,
        symbols: list[str],
        lookback_days: int,
        batch_size: int = 8,
    ) -> ValidationSession:
        """Create a new validation session with batches.

        Args:
            session_id: Unique session identifier
            correlation_id: Correlation ID for tracking
            symbols: All symbols to validate
            lookback_days: Days to look back for validation
            batch_size: Number of symbols per batch (default 8 for API limit)

        Returns:
            Created validation session

        """
        # Split symbols into batches
        batches: list[ValidationBatch] = []
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i : i + batch_size]
            batch = ValidationBatch(
                batch_number=len(batches),
                symbols=batch_symbols,
                status=BatchStatus.PENDING,
            )
            batches.append(batch)

        now = datetime.now(UTC)
        session = ValidationSession(
            session_id=session_id,
            correlation_id=correlation_id,
            total_symbols=len(symbols),
            total_batches=len(batches),
            batches=batches,
            status=SessionStatus.PENDING,
            lookback_days=lookback_days,
            created_at=now,
            updated_at=now,
        )

        # Persist to DynamoDB
        self._put_session(session)

        logger.info(
            "Validation session created",
            session_id=session_id,
            total_symbols=len(symbols),
            total_batches=len(batches),
            batch_size=batch_size,
        )

        return session

    def get_session(self, session_id: str) -> ValidationSession:
        """Retrieve a validation session.

        Args:
            session_id: Session identifier

        Returns:
            Validation session

        Raises:
            SessionManagerError: If session not found

        """
        try:
            response = self.table.get_item(Key={"PK": f"SESSION#{session_id}", "SK": "METADATA"})

            if "Item" not in response:
                raise SessionManagerError(
                    f"Session not found: {session_id}",
                    context={"session_id": session_id},
                )

            return self._deserialize_session(cast(dict[str, Any], response["Item"]))

        except SessionManagerError:
            raise
        except Exception as e:
            raise SessionManagerError(
                f"Failed to get session {session_id}: {e}",
                context={"session_id": session_id},
            ) from e

    def update_batch_status(
        self,
        session_id: str,
        batch_number: int,
        status: BatchStatus,
        error_message: str | None = None,
    ) -> ValidationSession:
        """Update the status of a specific batch.

        Args:
            session_id: Session identifier
            batch_number: Batch number to update
            status: New status
            error_message: Error message if failed

        Returns:
            Updated validation session

        """
        session = self.get_session(session_id)

        # Update the specific batch
        updated_batches = []
        for batch in session.batches:
            if batch.batch_number == batch_number:
                now = datetime.now(UTC)
                updated_batch = ValidationBatch(
                    batch_number=batch.batch_number,
                    symbols=batch.symbols,
                    status=status,
                    started_at=batch.started_at
                    or (now if status == BatchStatus.PROCESSING else None),
                    completed_at=now
                    if status in (BatchStatus.COMPLETED, BatchStatus.FAILED)
                    else None,
                    error_message=error_message,
                )
                updated_batches.append(updated_batch)
            else:
                updated_batches.append(batch)

        # Determine overall session status
        session_status = self._calculate_session_status(updated_batches)
        now = datetime.now(UTC)

        updated_session = ValidationSession(
            session_id=session.session_id,
            correlation_id=session.correlation_id,
            total_symbols=session.total_symbols,
            total_batches=session.total_batches,
            batches=updated_batches,
            status=session_status,
            lookback_days=session.lookback_days,
            created_at=session.created_at,
            updated_at=now,
            completed_at=now
            if session_status in (SessionStatus.COMPLETED, SessionStatus.FAILED)
            else None,
        )

        self._put_session(updated_session)

        logger.info(
            "Batch status updated",
            session_id=session_id,
            batch_number=batch_number,
            status=status.value,
            session_status=session_status.value,
        )

        return updated_session

    def store_symbol_result(self, result: SymbolValidationResult) -> None:
        """Store validation result for a single symbol.

        Args:
            result: Symbol validation result

        """
        try:
            item = {
                "PK": f"SESSION#{result.session_id}",
                "SK": f"RESULT#{result.symbol}",
                "symbol": result.symbol,
                "passed": result.passed,
                "issues": result.issues,
                "rows_checked": result.rows_checked,
                "external_source": result.external_source,
                "validated_at": result.validated_at.isoformat(),
            }

            self.table.put_item(Item=item)  # type: ignore[arg-type]

        except Exception as e:
            logger.error(
                "Failed to store symbol result",
                session_id=result.session_id,
                symbol=result.symbol,
                error=str(e),
            )
            raise SessionManagerError(
                f"Failed to store result for {result.symbol}: {e}",
                context={"session_id": result.session_id, "symbol": result.symbol},
            ) from e

    def get_all_results(self, session_id: str) -> dict[str, SymbolValidationResult]:
        """Retrieve all symbol results for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict mapping symbol to validation result

        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"SESSION#{session_id}",
                    ":sk": "RESULT#",
                },
            )

            results: dict[str, SymbolValidationResult] = {}
            for raw_item in response.get("Items", []):
                item = cast(dict[str, Any], raw_item)
                result = SymbolValidationResult(
                    session_id=session_id,
                    symbol=str(item["symbol"]),
                    passed=bool(item["passed"]),
                    issues=cast(list[str], item["issues"]),
                    rows_checked=int(cast(int, item["rows_checked"])),
                    external_source=str(item["external_source"]),
                    validated_at=datetime.fromisoformat(str(item["validated_at"])),
                )
                results[result.symbol] = result

            return results

        except Exception as e:
            logger.error(
                "Failed to get session results",
                session_id=session_id,
                error=str(e),
            )
            raise SessionManagerError(
                f"Failed to get results for session {session_id}: {e}",
                context={"session_id": session_id},
            ) from e

    def _put_session(self, session: ValidationSession) -> None:
        """Persist session to DynamoDB.

        Args:
            session: Session to persist

        """
        try:
            item = {
                "PK": f"SESSION#{session.session_id}",
                "SK": "METADATA",
                "session_id": session.session_id,
                "correlation_id": session.correlation_id,
                "total_symbols": session.total_symbols,
                "total_batches": session.total_batches,
                "batches": self._serialize_batches(session.batches),
                "status": session.status.value,
                "lookback_days": session.lookback_days,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "ttl": int(session.created_at.timestamp()) + (86400 * 7),  # 7 days TTL
            }

            self.table.put_item(Item=item)  # type: ignore[arg-type]

        except Exception as e:
            raise SessionManagerError(
                f"Failed to put session {session.session_id}: {e}",
                context={"session_id": session.session_id},
            ) from e

    def _serialize_batches(self, batches: list[ValidationBatch]) -> list[dict[str, object]]:
        """Serialize batches for DynamoDB storage.

        Args:
            batches: Batches to serialize

        Returns:
            List of serialized batch dicts

        """
        serialized = []
        for batch in batches:
            batch_dict = {
                "batch_number": batch.batch_number,
                "symbols": batch.symbols,
                "status": batch.status.value,
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
                "error_message": batch.error_message,
            }
            serialized.append(batch_dict)
        return serialized

    def _deserialize_session(self, item: dict[str, Any]) -> ValidationSession:
        """Deserialize session from DynamoDB item.

        Args:
            item: DynamoDB item

        Returns:
            Validation session

        """
        # Deserialize batches
        batches: list[ValidationBatch] = []
        batch_list = cast(list[dict[str, Any]], item["batches"])
        for batch_data in batch_list:
            batch = ValidationBatch(
                batch_number=int(cast(int, batch_data["batch_number"])),
                symbols=cast(list[str], batch_data["symbols"]),
                status=BatchStatus(str(batch_data["status"])),
                started_at=datetime.fromisoformat(str(batch_data["started_at"]))
                if batch_data.get("started_at")
                else None,
                completed_at=datetime.fromisoformat(str(batch_data["completed_at"]))
                if batch_data.get("completed_at")
                else None,
                error_message=str(batch_data["error_message"])
                if batch_data.get("error_message")
                else None,
            )
            batches.append(batch)

        return ValidationSession(
            session_id=str(item["session_id"]),
            correlation_id=str(item["correlation_id"]),
            total_symbols=int(cast(int, item["total_symbols"])),
            total_batches=int(cast(int, item["total_batches"])),
            batches=batches,
            status=SessionStatus(str(item["status"])),
            lookback_days=int(cast(int, item["lookback_days"])),
            created_at=datetime.fromisoformat(str(item["created_at"])),
            updated_at=datetime.fromisoformat(str(item["updated_at"])),
            completed_at=datetime.fromisoformat(str(item["completed_at"]))
            if item.get("completed_at")
            else None,
        )

    def _calculate_session_status(self, batches: list[ValidationBatch]) -> SessionStatus:
        """Calculate overall session status from batch statuses.

        Args:
            batches: All batches in session

        Returns:
            Session status

        """
        if all(b.status == BatchStatus.PENDING for b in batches):
            return SessionStatus.PENDING

        if any(b.status == BatchStatus.PROCESSING for b in batches):
            return SessionStatus.PROCESSING

        completed = sum(1 for b in batches if b.status == BatchStatus.COMPLETED)
        failed = sum(1 for b in batches if b.status == BatchStatus.FAILED)

        if completed + failed == len(batches):
            # All batches done - session is complete (even if some failed)
            return SessionStatus.COMPLETED

        return SessionStatus.PROCESSING
