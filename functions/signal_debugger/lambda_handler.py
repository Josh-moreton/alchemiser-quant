"""Business Unit: shared | Status: current.

Lambda handler for Signal Debugger microservice.

This Lambda tracks signal changes over time during the debugging window
(3:00-3:55 PM ET, every 5 minutes) to help debug partial bar behavior.

It captures each signal generation, compares it to the previous snapshot,
and records when tickers or weights change.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from the_alchemiser.shared.events import SignalGenerated
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)

# Environment variables
SIGNAL_HISTORY_TABLE = os.environ.get("SIGNAL_HISTORY_TABLE", "")
APP_STAGE = os.environ.get("APP__STAGE", "dev")


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle SignalGenerated events and track changes over time.

    Args:
        event: EventBridge event containing SignalGenerated data
        context: Lambda context

    Returns:
        Response with tracking status.

    """
    correlation_id = event.get("detail", {}).get("correlation_id", f"debug-{uuid.uuid4()}")

    logger.info(
        "Signal Debugger Lambda invoked",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Validate required environment variables
        if not SIGNAL_HISTORY_TABLE:
            raise ValueError("SIGNAL_HISTORY_TABLE environment variable is required")

        # Extract SignalGenerated event from EventBridge wrapper
        detail = event.get("detail", {})
        if not detail:
            raise ValueError("No detail found in event")

        # Extract signals data
        signals_data = detail.get("signals_data", {})
        timestamp = detail.get("timestamp", datetime.now(UTC).isoformat())

        # Get current date for partitioning
        current_date = datetime.now(UTC).date().isoformat()

        # Store signal snapshot
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(SIGNAL_HISTORY_TABLE)

        # Calculate signal hash for change detection
        signal_hash = _calculate_signal_hash(signals_data)

        # Check if signal changed from previous snapshot
        changes_detected = _detect_changes(
            table,
            current_date,
            timestamp,
            signals_data,
            signal_hash,
        )

        # Store snapshot
        table.put_item(
            Item={
                "PK": f"DATE#{current_date}",
                "SK": f"SNAPSHOT#{timestamp}",
                "correlation_id": correlation_id,
                "timestamp": timestamp,
                "signals_data": json.loads(json.dumps(signals_data), parse_float=Decimal),
                "signal_hash": signal_hash,
                "changes_detected": changes_detected,
                "stage": APP_STAGE,
                "ttl": int(datetime.now(UTC).timestamp()) + (90 * 24 * 60 * 60),  # 90 days
            }
        )

        logger.info(
            "Signal snapshot stored",
            extra={
                "correlation_id": correlation_id,
                "date": current_date,
                "timestamp": timestamp,
                "changes_detected": changes_detected,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "tracked",
                "correlation_id": correlation_id,
                "date": current_date,
                "timestamp": timestamp,
                "changes_detected": changes_detected,
            },
        }

    except Exception as e:
        logger.error(
            "Signal Debugger Lambda failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }


def _calculate_signal_hash(signals_data: dict[str, Any]) -> str:
    """Calculate a hash of the signals for change detection.

    Args:
        signals_data: Signal data dictionary

    Returns:
        Hash string representing the signal state.

    """
    # Create a deterministic representation of the signals
    # Sort keys to ensure consistent hashing
    signal_items = []
    for symbol, weight in sorted(signals_data.items()):
        # Round weight to 4 decimal places to avoid float precision issues
        rounded_weight = f"{float(weight):.4f}"
        signal_items.append(f"{symbol}:{rounded_weight}")

    return "|".join(signal_items)


def _detect_changes(
    table: Any,
    date: str,
    current_timestamp: str,
    current_signals: dict[str, Any],
    current_hash: str,
) -> dict[str, Any]:
    """Detect changes from the previous snapshot.

    Args:
        table: DynamoDB table resource
        date: Current date (for partition key)
        current_timestamp: Current timestamp
        current_signals: Current signal data
        current_hash: Hash of current signals

    Returns:
        Dictionary describing detected changes.

    """
    try:
        # Query for previous snapshot
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"DATE#{date}") & Key("SK").lt(f"SNAPSHOT#{current_timestamp}"),
            ScanIndexForward=False,  # Descending order (most recent first)
            Limit=1,
        )

        if not response.get("Items"):
            return {
                "is_first_snapshot": True,
                "ticker_changes": [],
                "weight_changes": [],
            }

        prev_snapshot = response["Items"][0]
        prev_signals = prev_snapshot.get("signals_data", {})
        prev_hash = prev_snapshot.get("signal_hash", "")

        # Quick check: if hashes match, no changes
        if current_hash == prev_hash:
            return {
                "is_first_snapshot": False,
                "has_changes": False,
            }

        # Detailed change detection
        current_tickers = set(current_signals.keys())
        prev_tickers = set(prev_signals.keys())

        added_tickers = list(current_tickers - prev_tickers)
        removed_tickers = list(prev_tickers - current_tickers)
        common_tickers = current_tickers & prev_tickers

        # Check weight changes for common tickers
        weight_changes = []
        for ticker in common_tickers:
            prev_weight = float(prev_signals.get(ticker, 0))
            curr_weight = float(current_signals.get(ticker, 0))

            # Consider a change if difference > 0.0001 (0.01%)
            if abs(curr_weight - prev_weight) > 0.0001:
                weight_changes.append(
                    {
                        "ticker": ticker,
                        "prev_weight": f"{prev_weight:.4f}",
                        "curr_weight": f"{curr_weight:.4f}",
                        "change": f"{curr_weight - prev_weight:+.4f}",
                    }
                )

        return {
            "is_first_snapshot": False,
            "has_changes": True,
            "added_tickers": added_tickers,
            "removed_tickers": removed_tickers,
            "weight_changes": weight_changes,
            "prev_timestamp": prev_snapshot.get("timestamp"),
        }

    except Exception as e:
        logger.warning(
            "Failed to detect changes",
            extra={"error": str(e)},
        )
        return {
            "error": str(e),
        }
