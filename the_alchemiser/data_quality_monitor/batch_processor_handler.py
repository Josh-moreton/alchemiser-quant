"""Business Unit: data_quality_monitor | Status: current.

Batch processor Lambda handler for data quality validation.

Processes a single batch of symbols (max 8) to respect API rate limits.
After completion, triggers next batch if any remain.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3

from the_alchemiser.shared.events import WorkflowCompleted, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .quality_checker import DataQualityChecker, DataQualityError
from .schemas import BatchStatus, SymbolValidationResult, ValidationSession
from .session_manager import SessionManagerError, ValidationSessionManager

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)

# Constants
NEXT_BATCH_DELAY_SECONDS = 60  # 1 minute delay to respect rate limits


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Process a batch of symbols for data quality validation.

    Triggered by SQS message containing batch details.

    Args:
        event: SQS event with batch details
        context: Lambda context

    Returns:
        Processing result

    """
    # Extract message from SQS event
    try:
        records = event.get("Records", [])
        if not records:
            logger.warning("No SQS records in event")
            return {"statusCode": 400, "body": {"error": "No SQS records"}}

        # Process first record (SQS batch size is 1 in our config)
        message_body = json.loads(records[0]["body"])

        session_id = message_body["session_id"]
        correlation_id = message_body["correlation_id"]
        batch_number = message_body["batch_number"]
        symbols = message_body["symbols"]
        lookback_days = message_body["lookback_days"]

    except (KeyError, json.JSONDecodeError) as e:
        logger.error("Invalid SQS message format", error=str(e), exc_info=True)
        return {"statusCode": 400, "body": {"error": "Invalid message format"}}

    logger.info(
        "Batch processor invoked",
        correlation_id=correlation_id,
        session_id=session_id,
        batch_number=batch_number,
        symbols_count=len(symbols),
    )

    session_manager = ValidationSessionManager()

    try:
        # Mark batch as processing
        session_manager.update_batch_status(
            session_id=session_id,
            batch_number=batch_number,
            status=BatchStatus.PROCESSING,
        )

        # Process batch
        results = _process_batch(
            symbols=symbols,
            lookback_days=lookback_days,
            session_id=session_id,
            correlation_id=correlation_id,
        )

        # Store results in DynamoDB
        for symbol, result in results.items():
            symbol_result = SymbolValidationResult(
                session_id=session_id,
                symbol=symbol,
                passed=result.passed,
                issues=result.issues,
                rows_checked=result.rows_checked,
                external_source=result.external_source,
                validated_at=datetime.now(UTC),
            )
            session_manager.store_symbol_result(symbol_result)

        # Mark batch as completed
        session = session_manager.update_batch_status(
            session_id=session_id,
            batch_number=batch_number,
            status=BatchStatus.COMPLETED,
        )

        logger.info(
            "Batch processing completed",
            correlation_id=correlation_id,
            session_id=session_id,
            batch_number=batch_number,
            symbols_processed=len(results),
        )

        # Check if more batches remain
        if not session.is_complete:
            _enqueue_next_batch(session, correlation_id)
        else:
            _finalize_session(session, correlation_id, session_manager)

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "session_id": session_id,
                "batch_number": batch_number,
                "symbols_processed": len(results),
                "session_complete": session.is_complete,
            },
        }

    except (DataQualityError, SessionManagerError, Exception) as e:
        return _handle_batch_failure(
            error=e,
            session_id=session_id,
            batch_number=batch_number,
            correlation_id=correlation_id,
            session_manager=session_manager,
        )


def _process_batch(
    symbols: list[str],
    lookback_days: int,
    session_id: str,
    correlation_id: str,
) -> dict[str, Any]:
    """Process a batch of symbols.

    Args:
        symbols: Symbols to validate
        lookback_days: Days to look back
        session_id: Session ID
        correlation_id: Correlation ID

    Returns:
        Dict mapping symbol to validation result

    """
    checker = DataQualityChecker()

    logger.info(
        "Processing batch",
        correlation_id=correlation_id,
        session_id=session_id,
        symbols=symbols,
        lookback_days=lookback_days,
    )

    return checker.validate_symbols(symbols=symbols, lookback_days=lookback_days)


def _enqueue_next_batch(session: ValidationSession, correlation_id: str) -> None:
    """Enqueue the next pending batch with delay.

    Args:
        session: Validation session
        correlation_id: Correlation ID

    """
    next_batch = session.pending_batches[0] if session.pending_batches else None

    if not next_batch:
        logger.warning(
            "No pending batches found but session not complete",
            correlation_id=correlation_id,
            session_id=session.session_id,
        )
        return

    queue_url = os.environ["VALIDATION_QUEUE_URL"]
    sqs = boto3.client("sqs")

    message = {
        "session_id": session.session_id,
        "correlation_id": correlation_id,
        "batch_number": next_batch.batch_number,
        "symbols": next_batch.symbols,
        "lookback_days": session.lookback_days,
    }

    # Send with 60-second delay to respect API rate limits
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message),
        DelaySeconds=NEXT_BATCH_DELAY_SECONDS,
    )

    logger.info(
        "Next batch enqueued with delay",
        correlation_id=correlation_id,
        session_id=session.session_id,
        batch_number=next_batch.batch_number,
        delay_seconds=NEXT_BATCH_DELAY_SECONDS,
    )


def _finalize_session(
    session: ValidationSession,
    correlation_id: str,
    session_manager: ValidationSessionManager,
) -> None:
    """Finalize session and publish completion event.

    Args:
        session: Validation session
        correlation_id: Correlation ID
        session_manager: Session manager

    """
    # Get all results
    all_results = session_manager.get_all_results(session.session_id)

    # Calculate statistics
    total = len(all_results)
    passed_count = sum(1 for r in all_results.values() if r.passed)
    failed_count = total - passed_count
    failed_symbols = [s for s, r in all_results.items() if not r.passed]

    # Calculate duration
    if session.created_at and session.updated_at:
        duration_ms = int((session.updated_at - session.created_at).total_seconds() * 1000)
    else:
        duration_ms = 0

    logger.info(
        "Session finalized",
        correlation_id=correlation_id,
        session_id=session.session_id,
        total_symbols=total,
        passed=passed_count,
        failed=failed_count,
    )

    # Publish WorkflowCompleted event
    try:
        completion_event = WorkflowCompleted(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"quality-session-complete-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="data_quality_monitor",
            source_component="batch_processor_handler",
            workflow_type="data_quality_batch_validation",
            workflow_duration_ms=duration_ms,
            success=True,  # Session completed (even if some quality issues found)
            summary={
                "session_id": session.session_id,
                "total_symbols": total,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "failed_symbols": failed_symbols,
            },
        )
        publish_to_eventbridge(completion_event)
    except Exception as pub_error:
        logger.error(
            "Failed to publish WorkflowCompleted event",
            error=str(pub_error),
        )


def _handle_batch_failure(
    error: Exception,
    session_id: str,
    batch_number: int,
    correlation_id: str,
    session_manager: ValidationSessionManager,
) -> dict[str, Any]:
    """Handle batch processing failure.

    Args:
        error: Exception that occurred
        session_id: Session ID
        batch_number: Batch number
        correlation_id: Correlation ID
        session_manager: Session manager

    Returns:
        Error response

    """
    logger.error(
        "Batch processing failed",
        correlation_id=correlation_id,
        session_id=session_id,
        batch_number=batch_number,
        error=str(error),
        exc_info=True,
    )

    # Mark batch as failed
    try:
        session_manager.update_batch_status(
            session_id=session_id,
            batch_number=batch_number,
            status=BatchStatus.FAILED,
            error_message=str(error),
        )
    except Exception as update_error:
        logger.error(
            "Failed to update batch status to FAILED",
            error=str(update_error),
        )

    # Publish WorkflowFailed event
    try:
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"quality-batch-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="data_quality_monitor",
            source_component="batch_processor_handler",
            workflow_type="data_quality_batch_validation",
            failure_reason=str(error),
            failure_step=f"batch_{batch_number}",
            error_details={
                "exception_type": type(error).__name__,
                "session_id": session_id,
                "batch_number": batch_number,
            },
        )
        publish_to_eventbridge(failure_event)
    except Exception as pub_error:
        logger.error(
            "Failed to publish WorkflowFailed event",
            error=str(pub_error),
        )

    return {
        "statusCode": 500,
        "body": {
            "status": "error",
            "correlation_id": correlation_id,
            "session_id": session_id,
            "batch_number": batch_number,
            "error": str(error),
        },
    }
