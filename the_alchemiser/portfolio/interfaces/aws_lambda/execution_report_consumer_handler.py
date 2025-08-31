"""Business Unit: portfolio assessment & management | Status: current.

AWS Lambda handler for consuming execution reports from SQS.

This handler is triggered by SQS events containing ExecutionReportContractV1 JSON
payloads and invokes the UpdatePortfolioUseCase to update portfolio state based
on execution fills.

Trigger: SQS event carrying ExecutionReportContractV1 JSON
Action: parse -> UpdatePortfolioUseCase -> persist updated positions
"""

from __future__ import annotations

import json
import logging
from typing import Any

from the_alchemiser.execution.application.contracts.execution_report_contract_v1 import (
    ExecutionReportContractV1,
)
from the_alchemiser.shared_kernel.exceptions.base_exceptions import (
    ConfigurationError,
)

from .bootstrap import bootstrap_portfolio_context

logger = logging.getLogger(__name__)

# Initialize bootstrap context once per Lambda container
_bootstrap_context = None


def _get_bootstrap_context():
    """Get or initialize bootstrap context (container-level caching)."""
    global _bootstrap_context
    if _bootstrap_context is None:
        _bootstrap_context = bootstrap_portfolio_context()
    return _bootstrap_context


def _parse_sqs_report_record(record: dict[str, Any]) -> ExecutionReportContractV1:
    """Parse SQS record containing ExecutionReportContractV1 JSON.

    Args:
        record: SQS record from event

    Returns:
        Parsed ExecutionReportContractV1 instance

    Raises:
        ValueError: If record cannot be parsed

    """
    try:
        # Get message body (might be JSON string)
        body = record.get("body", "")
        if isinstance(body, str):
            message_data = json.loads(body)
        else:
            message_data = body

        # Handle potential SQS message wrapping
        if "Message" in message_data:
            # SNS -> SQS wrapping
            report_data = json.loads(message_data["Message"])
        else:
            # Direct SQS message
            report_data = message_data

        # Parse execution report contract
        return ExecutionReportContractV1.model_validate(report_data)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse SQS execution report record: {e}") from e


def handler(event: dict, context: Any) -> dict[str, Any]:
    """AWS Lambda handler for portfolio execution report consumption.

    Expected event format (SQS):
    {
        "Records": [
            {
                "body": "{...ExecutionReportContractV1 JSON...}",
                "messageId": "...",
                "receiptHandle": "..."
            }
        ]
    }

    Args:
        event: AWS Lambda event (SQS)
        context: AWS Lambda context object

    Returns:
        dict with processing status and metrics

    """
    correlation_id = getattr(context, "aws_request_id", "unknown")
    records = event.get("Records", [])

    logger.info(
        "Portfolio execution report consumer invoked",
        extra={"correlation_id": correlation_id, "record_count": len(records)},
    )

    processed = 0
    skipped = 0
    total_fills = 0
    processed_report_ids = []

    try:
        # Get dependencies
        bootstrap_ctx = _get_bootstrap_context()

        for record in records:
            message_id = record.get("messageId", "unknown")

            try:
                # Parse execution report from SQS record
                report = _parse_sqs_report_record(record)

                logger.debug(
                    "Processing execution report",
                    extra={
                        "message_id": message_id,
                        "report_id": str(report.report_id),
                        "fills_count": len(report.fills),
                        "correlation_id": str(report.correlation_id),
                    },
                )

                # TODO: Implement idempotency check here if needed
                # For now, assume SQS deduplication handles this

                # Execute use case
                bootstrap_ctx.update_portfolio_use_case.handle_execution_report(report)

                processed += 1
                total_fills += len(report.fills)
                processed_report_ids.append(str(report.report_id))

            except ValueError as e:
                # Parsing error - skip this record and continue
                logger.warning(
                    "Skipped unparseable execution report record: %s",
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "component": "execution_report_consumer_handler",
                    },
                )
                skipped += 1
                continue

            except Exception as e:
                # Use case execution error - log and re-raise to ensure retry
                logger.error(
                    "Failed to process execution report %s: %s",
                    message_id,
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "error_type": type(e).__name__,
                        "component": "execution_report_consumer_handler",
                    },
                    exc_info=True,
                )
                raise

        # Build response
        result = {
            "status": "success",
            "processed": processed,
            "skipped": skipped,
            "total_fills": total_fills,
            "correlation_id": correlation_id,
            "processed_report_ids": processed_report_ids,
        }

        logger.info(
            "Portfolio execution report consumption completed",
            extra={
                "correlation_id": correlation_id,
                "processed": processed,
                "skipped": skipped,
                "total_fills": total_fills,
            },
        )

        return result

    except ConfigurationError as e:
        # Configuration issues - log and re-raise (likely permanent failure)
        logger.error(
            "Portfolio context configuration error: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "execution_report_consumer_handler",
            },
            exc_info=True,
        )
        raise

    except Exception as e:
        # Unexpected error - log and re-raise
        logger.error(
            "Unexpected error in portfolio execution report consumer: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "execution_report_consumer_handler",
            },
            exc_info=True,
        )
        raise
