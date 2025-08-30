"""Business Unit: portfolio assessment & management | Status: current.

AWS Lambda handler for consuming strategy signals from SQS.

This handler is triggered by SQS events containing SignalContractV1 JSON payloads
and invokes the GeneratePlanUseCase to create rebalance plans for cross-context
publication.

Trigger: SQS event carrying SignalContractV1 JSON
Action: parse -> GeneratePlanUseCase -> publish RebalancePlanContractV1
"""

from __future__ import annotations

import json
import logging
from typing import Any

from the_alchemiser.shared_kernel.exceptions.base_exceptions import (
    ConfigurationError,
)
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1

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


def _parse_sqs_signal_record(record: dict[str, Any]) -> SignalContractV1:
    """Parse SQS record containing SignalContractV1 JSON.
    
    Args:
        record: SQS record from event
        
    Returns:
        Parsed SignalContractV1 instance
        
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
            signal_data = json.loads(message_data["Message"])
        else:
            # Direct SQS message
            signal_data = message_data
            
        # Parse signal contract
        return SignalContractV1.model_validate(signal_data)
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse SQS signal record: {e}") from e


def handler(event: dict, context: Any) -> dict[str, Any]:
    """AWS Lambda handler for portfolio signal consumption.
    
    Expected event format (SQS):
    {
        "Records": [
            {
                "body": "{...SignalContractV1 JSON...}",
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
    
    logger.info("Portfolio signal consumer invoked", extra={
        "correlation_id": correlation_id,
        "record_count": len(records)
    })
    
    processed = 0
    skipped = 0
    plans_generated = 0
    processed_message_ids = []
    
    try:
        # Get dependencies
        bootstrap_ctx = _get_bootstrap_context()
        
        for record in records:
            message_id = record.get("messageId", "unknown")
            
            try:
                # Parse signal from SQS record
                signal = _parse_sqs_signal_record(record)
                
                logger.debug("Processing signal", extra={
                    "message_id": message_id,
                    "signal_id": str(signal.message_id),
                    "symbol": str(signal.symbol),
                    "action": signal.action.value
                })
                
                # TODO: Implement idempotency check here if needed
                # For now, assume SQS deduplication handles this
                
                # Execute use case
                bootstrap_ctx.generate_plan_use_case.handle_signal(signal)
                
                processed += 1
                plans_generated += 1  # Assuming each signal generates one plan
                processed_message_ids.append(str(signal.message_id))
                
            except ValueError as e:
                # Parsing error - skip this record and continue
                logger.warning(
                    "Skipped unparseable signal record: %s", 
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "component": "signal_consumer_handler"
                    }
                )
                skipped += 1
                continue
                
            except Exception as e:
                # Use case execution error - log and re-raise to ensure retry
                logger.error(
                    "Failed to process signal %s: %s",
                    message_id,
                    str(e),
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "error_type": type(e).__name__,
                        "component": "signal_consumer_handler"
                    },
                    exc_info=True
                )
                raise
        
        # Build response
        result = {
            "status": "success",
            "processed": processed,
            "skipped": skipped,
            "plans_generated": plans_generated,
            "correlation_id": correlation_id,
            "processed_signal_ids": processed_message_ids
        }
        
        logger.info("Portfolio signal consumption completed", extra={
            "correlation_id": correlation_id,
            "processed": processed,
            "skipped": skipped,
            "plans_generated": plans_generated
        })
        
        return result
        
    except ConfigurationError as e:
        # Configuration issues - log and re-raise (likely permanent failure)
        logger.error(
            "Portfolio context configuration error: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "signal_consumer_handler"
            },
            exc_info=True
        )
        raise
        
    except Exception as e:
        # Unexpected error - log and re-raise
        logger.error(
            "Unexpected error in portfolio signal consumer: %s",
            str(e),
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "component": "signal_consumer_handler"
            },
            exc_info=True
        )
        raise