"""Business Unit: data_quality_monitor | Status: current.

Coordinator Lambda handler for data quality batch validation.

Entry point that initiates batch processing workflow:
1. Determines symbols to validate
2. Creates validation session in DynamoDB
3. Splits symbols into batches of 8 (rate limit)
4. Enqueues first batch to SQS for immediate processing
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3

from the_alchemiser.data_v2.symbol_extractor import get_all_configured_symbols
from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .session_manager import SessionManagerError, ValidationSessionManager

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Coordinate data quality validation across multiple batches.

    Creates a validation session, splits symbols into batches of 8,
    and initiates batch processing via SQS.

    Args:
        event: Lambda event (schedule trigger or manual)
        context: Lambda context

    Returns:
        Response with session details

    """
    correlation_id = event.get("correlation_id") or f"quality-coord-{uuid.uuid4()}"
    session_id = f"session-{uuid.uuid4()}"

    logger.info(
        "Data Quality Coordinator invoked",
        correlation_id=correlation_id,
        session_id=session_id,
    )

    try:
        # Determine symbols to validate
        specific_symbols = event.get("symbols")
        symbols = specific_symbols or list(get_all_configured_symbols())

        lookback_days = event.get("lookback_days", 5)

        logger.info(
            "Symbols determined for validation",
            correlation_id=correlation_id,
            total_symbols=len(symbols),
            lookback_days=lookback_days,
        )

        # Create validation session
        session_manager = ValidationSessionManager()
        session = session_manager.create_session(
            session_id=session_id,
            correlation_id=correlation_id,
            symbols=symbols,
            lookback_days=lookback_days,
            batch_size=8,  # Twelve Data API limit
        )

        # Enqueue first batch to SQS for immediate processing
        queue_url = os.environ["VALIDATION_QUEUE_URL"]
        sqs = boto3.client("sqs")

        first_batch = session.batches[0]
        message = {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "batch_number": first_batch.batch_number,
            "symbols": first_batch.symbols,
            "lookback_days": lookback_days,
        }

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
        )

        logger.info(
            "First batch enqueued",
            correlation_id=correlation_id,
            session_id=session_id,
            batch_number=0,
            symbols_count=len(first_batch.symbols),
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "initiated",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "total_symbols": len(symbols),
                "total_batches": session.total_batches,
                "estimated_duration_minutes": session.total_batches,
            },
        }

    except (SessionManagerError, Exception) as e:
        return _handle_failure(e, correlation_id, session_id)


def _handle_failure(
    error: Exception,
    correlation_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Handle coordinator failure.

    Args:
        error: Exception that occurred
        correlation_id: Correlation ID for tracking
        session_id: Session ID for tracking

    Returns:
        Error response

    """
    logger.error(
        "Data Quality Coordinator failed",
        correlation_id=correlation_id,
        session_id=session_id,
        error=str(error),
        exc_info=True,
    )

    # Publish WorkflowFailed event
    try:
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"quality-coord-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="data_quality_monitor",
            source_component="coordinator_handler",
            workflow_type="data_quality_batch_validation",
            failure_reason=str(error),
            failure_step="coordination",
            error_details={"exception_type": type(error).__name__, "session_id": session_id},
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
            "error": str(error),
        },
    }
