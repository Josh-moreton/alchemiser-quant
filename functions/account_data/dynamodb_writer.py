"""Business Unit: account_data | Status: current.

DynamoDB writer for account data snapshots.

Serialises account summaries, position snapshots, and daily PnL records
into DynamoDB items following the single-table design documented in
the account_data_reader service.

All financial values are stored as strings (Decimal -> str) so DynamoDB
Number type preserves full precision.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.pnl import DailyPnLEntry

logger = get_logger(__name__)

# TTL durations
SNAPSHOT_TTL_DAYS = 90
PNL_TTL_DAYS = 400


def write_account_snapshot(
    table: Any,  # noqa: ANN401
    account_id: str,
    account_data: dict[str, Any],
    timestamp: str,
) -> None:
    """Write an account snapshot to DynamoDB.

    Args:
        table: boto3 DynamoDB Table resource.
        account_id: Alpaca account identifier.
        account_data: Account dict from AlpacaAccountService.get_account_dict().
        timestamp: ISO 8601 timestamp for this snapshot.

    """
    ttl = int((datetime.now(UTC) + timedelta(days=SNAPSHOT_TTL_DAYS)).timestamp())
    serialised = _sanitize_for_dynamodb(account_data)

    table.put_item(
        Item={
            "PK": f"ACCOUNT#{account_id}",
            "SK": f"SNAPSHOT#{timestamp}",
            "EntityType": "ACCOUNT_SNAPSHOT",
            "account_data": json.dumps(serialised, default=str),
            "updated_at": timestamp,
            "ExpiresAt": ttl,
        }
    )

    logger.info(
        "Wrote account snapshot",
        extra={"account_id": account_id, "timestamp": timestamp},
    )


def write_positions_snapshot(
    table: Any,  # noqa: ANN401
    account_id: str,
    positions: list[dict[str, Any]],
    timestamp: str,
) -> None:
    """Write a positions snapshot to DynamoDB.

    All positions for one snapshot are stored as a single JSON-serialised list
    in one DynamoDB item (they belong together and are always read together).

    Args:
        table: boto3 DynamoDB Table resource.
        account_id: Alpaca account identifier.
        positions: List of position dicts (symbol, qty, prices, P&L fields).
        timestamp: ISO 8601 timestamp for this snapshot.

    """
    ttl = int((datetime.now(UTC) + timedelta(days=SNAPSHOT_TTL_DAYS)).timestamp())
    serialised = [_sanitize_for_dynamodb(p) for p in positions]

    table.put_item(
        Item={
            "PK": f"POSITIONS#{account_id}",
            "SK": f"SNAPSHOT#{timestamp}",
            "EntityType": "POSITIONS_SNAPSHOT",
            "positions_data": json.dumps(serialised, default=str),
            "position_count": len(positions),
            "updated_at": timestamp,
            "ExpiresAt": ttl,
        }
    )

    logger.info(
        "Wrote positions snapshot",
        extra={
            "account_id": account_id,
            "position_count": len(positions),
            "timestamp": timestamp,
        },
    )


def write_pnl_records(
    table: Any,  # noqa: ANN401
    account_id: str,
    daily_records: list[DailyPnLEntry],
) -> None:
    """Batch-write daily PnL records to DynamoDB.

    Each record gets its own item keyed by PK=PNL#<id>, SK=DATE#<YYYY-MM-DD>.
    Uses batch_writer for efficient throughput (batches of 25).

    This is idempotent: re-writing the same date overwrites with the same values.

    Args:
        table: boto3 DynamoDB Table resource.
        account_id: Alpaca account identifier.
        daily_records: List of DailyPnLEntry DTOs from PnLService.

    """
    ttl = int((datetime.now(UTC) + timedelta(days=PNL_TTL_DAYS)).timestamp())
    written = 0

    with table.batch_writer() as batch:
        for record in daily_records:
            item: dict[str, Any] = {
                "PK": f"PNL#{account_id}",
                "SK": f"DATE#{record.date}",
                "EntityType": "DAILY_PNL",
                "equity": str(record.equity),
                "profit_loss": str(record.profit_loss),
                "profit_loss_pct": str(record.profit_loss_pct),
                "ExpiresAt": ttl,
            }

            if record.deposit is not None:
                item["deposit"] = str(record.deposit)
            if record.withdrawal is not None:
                item["withdrawal"] = str(record.withdrawal)

            batch.put_item(Item=item)
            written += 1

    logger.info(
        "Wrote PnL records",
        extra={"account_id": account_id, "records_written": written},
    )


def update_latest_pointer(
    table: Any,  # noqa: ANN401
    account_id: str,
    entity_type: str,
    timestamp: str,
) -> None:
    """Update the LATEST pointer for an entity type.

    The pointer stores the SK of the most recent snapshot so readers can
    find it with a single GetItem instead of a reverse-chronological Query.

    Args:
        table: boto3 DynamoDB Table resource.
        account_id: Alpaca account identifier.
        entity_type: One of "ACCOUNT" or "POSITIONS".
        timestamp: ISO 8601 timestamp matching the snapshot SK.

    """
    table.put_item(
        Item={
            "PK": f"LATEST#{account_id}",
            "SK": entity_type,
            "snapshot_sk": f"SNAPSHOT#{timestamp}",
            "updated_at": timestamp,
        }
    )


def _sanitize_for_dynamodb(obj: Any) -> Any:  # noqa: ANN401
    """Recursively convert Decimal and other non-JSON-serialisable types to strings.

    DynamoDB's batch_writer handles Decimal natively, but since we JSON-serialise
    the account/position dicts, we need plain Python types.
    """
    if isinstance(obj, dict):
        return {k: _sanitize_for_dynamodb(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_dynamodb(v) for v in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
