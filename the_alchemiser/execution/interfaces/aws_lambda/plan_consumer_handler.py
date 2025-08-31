"""Business Unit: order execution/placement | Status: current.

AWS Lambda handler for consuming rebalance plans from SQS.

This handler is triggered by SQS events containing RebalancePlanContractV1 JSON
payloads and invokes the ExecutePlanUseCase to execute orders and publish
execution reports.

Trigger: SQS event carrying RebalancePlanContractV1 JSON
Action: parse -> ExecutePlanUseCase -> publish ExecutionReportContractV1
"""

from __future__ import annotations

import json
import logging
from typing import Any

from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import (
    RebalancePlanContractV1,
)
from the_alchemiser.shared_kernel.exceptions.base_exceptions import (
    ConfigurationError,
)

from .bootstrap import bootstrap_execution_context

logger = logging.getLogger(__name__)

# Initialize bootstrap context once per Lambda container
_bootstrap_context = None


def _get_bootstrap_context():
    """Get or initialize bootstrap context (container-level caching)."""
    global _bootstrap_context
    if _bootstrap_context is None:
        _bootstrap_context = bootstrap_execution_context()
    return _bootstrap_context


def _parse_sqs_plan_record(record: dict[str, Any]) -> RebalancePlanContractV1:
    """Parse SQS record containing RebalancePlanContractV1 JSON.

    Args:
        record: SQS record from event

    Returns:
        Parsed RebalancePlanContractV1 instance

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
            plan_data = json.loads(message_data["Message"])
        else:
            # Direct SQS message
            plan_data = message_data

        # Parse plan contract
        return RebalancePlanContractV1.model_validate(plan_data)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse SQS plan record: {e}") from e


def handler(event: dict, context: Any) -> dict[str, Any]:
    """AWS Lambda handler for execution plan consumption.

    Expected event format (SQS):
    {
        "Records": [
            {
                "body": "{...RebalancePlanContractV1 JSON...}",
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
        "Execution plan consumer invoked",
        extra={"correlation_id": correlation_id, "record_count": len(records)},
    )

    processed = 0
    skipped = 0
    total_orders = 0
    total_fills = 0
    processed_plan_ids = []

    try:
        # Get dependencies
        bootstrap_ctx = _get_bootstrap_context()

        for record in records:
            message_id = record.get("messageId", "unknown")

            try:
                # Parse plan from SQS record
                plan = _parse_sqs_plan_record(record)

                logger.debug(
                    "Processing plan",
                    extra={
                        "message_id": message_id,
                        "plan_id": str(plan.plan_id),
                        "orders_count": len(plan.planned_orders),
                        "correlation_id": str(plan.correlation_id),
                    },
                )

                # TODO: Implement idempotency check here if needed
                # For now, assume SQS deduplication handles this

                # Execute use case
                bootstrap_ctx.execute_plan_use_case.handle_plan(plan)

                processed += 1
                total_orders += len(plan.planned_orders)
                total_fills += len(plan.planned_orders)  # Assuming 1:1 for simulation
                processed_plan_ids.append(str(plan.plan_id))

            except ValueError as e:
                # Parsing error - skip this record and continue
                logger.warning(
                    "Skipped unparseable plan record: %s",
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "component": "plan_consumer_handler",
                    },
                )
                skipped += 1
                continue

            except Exception as e:
                # Use case execution error - log and re-raise to ensure retry
                logger.error(
                    "Failed to execute plan %s: %s",
                    message_id,
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "error_type": type(e).__name__,
                        "component": "plan_consumer_handler",
                    },
                    exc_info=True,
                )
                raise

        # Build response
        result = {
            "status": "success",
            "processed": processed,
            "skipped": skipped,
            "total_orders": total_orders,
            "total_fills": total_fills,
            "correlation_id": correlation_id,
            "processed_plan_ids": processed_plan_ids,
        }

        logger.info(
            "Execution plan consumption completed",
            extra={
                "correlation_id": correlation_id,
                "processed": processed,
                "skipped": skipped,
                "total_orders": total_orders,
                "total_fills": total_fills,
            },
        )

        return result

    except ConfigurationError as e:
        # Configuration issues - log and re-raise (likely permanent failure)
        logger.error(
            "Execution context configuration error: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "plan_consumer_handler",
            },
            exc_info=True,
        )
        raise

    except Exception as e:
        # Unexpected error - log and re-raise
        logger.error(
            "Unexpected error in execution plan consumer: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "plan_consumer_handler",
            },
            exc_info=True,
        )
        raise
