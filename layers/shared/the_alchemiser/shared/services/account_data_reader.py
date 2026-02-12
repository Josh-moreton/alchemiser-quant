"""Business Unit: shared | Status: current.

Read-only service for account data stored in DynamoDB.

The account_data Lambda writes account snapshots, positions, and PnL history
to a single-table DynamoDB design. This service provides typed read access
for consumers (primarily the Streamlit dashboard) so they never need to
call Alpaca directly.

Table key schema (single-table design):
    PK=ACCOUNT#<account_id>   SK=SNAPSHOT#<iso_ts>   -> account snapshot
    PK=POSITIONS#<account_id> SK=SNAPSHOT#<iso_ts>   -> positions snapshot
    PK=PNL#<account_id>       SK=DATE#<YYYY-MM-DD>   -> daily PnL record
    PK=LATEST#<account_id>    SK=ACCOUNT              -> latest pointer
    PK=LATEST#<account_id>    SK=POSITIONS             -> latest pointer
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.accounts import PositionSnapshot
from the_alchemiser.shared.schemas.pnl import DailyPnLEntry

logger = get_logger(__name__)


class AccountDataReader:
    """Read-only service for account data persisted in DynamoDB.

    All methods accept a boto3 DynamoDB Table resource and the account_id
    to query. The caller is responsible for constructing the Table object
    (with appropriate credentials/region).

    Invariants:
        - Never writes to DynamoDB.
        - Account snapshots are returned as raw dicts (same shape as AlpacaAccountService.get_account_dict)
          or None when no snapshot exists.
        - Position and PnL reads return typed DTOs (PositionSnapshot, DailyPnLEntry) and use empty
          collections (not None) when no data is found.
    """

    # ------------------------------------------------------------------
    # Account ID discovery
    # ------------------------------------------------------------------

    @staticmethod
    def discover_account_id(
        table: Any,  # noqa: ANN401
    ) -> str:
        """Discover the account ID from the registry entry in DynamoDB.

        The account_data Lambda writes a well-known item at
        ``PK=REGISTRY``, ``SK=ACCOUNT_ID`` containing the Alpaca account
        identifier.  This allows consumers to discover the account ID
        with a single GetItem (no Scan required).

        Args:
            table: boto3 DynamoDB Table resource.

        Returns:
            Account ID string, or empty string if no registry entry exists.

        """
        try:
            item = table.get_item(
                Key={"PK": "REGISTRY", "SK": "ACCOUNT_ID"},
            ).get("Item")
        except Exception:
            logger.warning(
                "Failed to read account registry from DynamoDB",
                exc_info=True,
            )
            return ""

        if not item:
            logger.info("No account registry entry found in DynamoDB table")
            return ""

        account_id: str = str(item.get("account_id", ""))
        if account_id:
            logger.info(
                "Discovered account_id from DynamoDB registry",
                extra={"account_id": account_id},
            )
        return account_id

    # ------------------------------------------------------------------
    # Account snapshot
    # ------------------------------------------------------------------

    @staticmethod
    def get_latest_account_snapshot(
        table: Any,  # noqa: ANN401
        account_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve the most recent account snapshot.

        Args:
            table: boto3 DynamoDB Table resource.
            account_id: Alpaca account identifier.

        Returns:
            Raw account dict (same shape as AlpacaAccountService.get_account_dict)
            or None if no snapshot exists.

        """
        # Read the LATEST pointer to find the most recent snapshot timestamp
        pointer = table.get_item(
            Key={"PK": f"LATEST#{account_id}", "SK": "ACCOUNT"},
        ).get("Item")

        if not pointer:
            logger.warning(
                "No latest account pointer found",
                extra={"account_id": account_id},
            )
            return None

        snapshot_sk = pointer.get("snapshot_sk", "")
        if not snapshot_sk:
            return None

        # Fetch the actual snapshot
        item = table.get_item(
            Key={"PK": f"ACCOUNT#{account_id}", "SK": snapshot_sk},
        ).get("Item")

        if not item:
            return None

        return _deserialize_account_item(item)

    # ------------------------------------------------------------------
    # Positions snapshot
    # ------------------------------------------------------------------

    @staticmethod
    def get_latest_positions(
        table: Any,  # noqa: ANN401
        account_id: str,
    ) -> list[PositionSnapshot]:
        """Retrieve the most recent positions snapshot.

        Args:
            table: boto3 DynamoDB Table resource.
            account_id: Alpaca account identifier.

        Returns:
            List of PositionSnapshot DTOs (empty if no data).

        """
        pointer = table.get_item(
            Key={"PK": f"LATEST#{account_id}", "SK": "POSITIONS"},
        ).get("Item")

        if not pointer:
            logger.warning(
                "No latest positions pointer found",
                extra={"account_id": account_id},
            )
            return []

        snapshot_sk = pointer.get("snapshot_sk", "")
        if not snapshot_sk:
            return []

        item = table.get_item(
            Key={"PK": f"POSITIONS#{account_id}", "SK": snapshot_sk},
        ).get("Item")

        if not item:
            return []

        return _deserialize_positions_item(item)

    # ------------------------------------------------------------------
    # PnL history
    # ------------------------------------------------------------------

    @staticmethod
    def get_pnl_history(
        table: Any,  # noqa: ANN401
        account_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[DailyPnLEntry]:
        """Query daily PnL records for a date range.

        Args:
            table: boto3 DynamoDB Table resource.
            account_id: Alpaca account identifier.
            start_date: Inclusive start date (YYYY-MM-DD). If None, reads all.
            end_date: Inclusive end date (YYYY-MM-DD). If None, reads up to today.

        Returns:
            Chronologically sorted list of DailyPnLEntry DTOs.

        """
        from boto3.dynamodb.conditions import Key

        pk = f"PNL#{account_id}"

        if start_date and end_date:
            response = table.query(
                KeyConditionExpression=(
                    Key("PK").eq(pk) & Key("SK").between(f"DATE#{start_date}", f"DATE#{end_date}")
                ),
            )
        elif start_date:
            response = table.query(
                KeyConditionExpression=(Key("PK").eq(pk) & Key("SK").gte(f"DATE#{start_date}")),
            )
        else:
            response = table.query(
                KeyConditionExpression=Key("PK").eq(pk),
            )

        items = response.get("Items", [])

        # Handle pagination
        while response.get("LastEvaluatedKey"):
            kwargs: dict[str, Any] = {
                "KeyConditionExpression": Key("PK").eq(pk),
                "ExclusiveStartKey": response["LastEvaluatedKey"],
            }
            if start_date and end_date:
                kwargs["KeyConditionExpression"] = Key("PK").eq(pk) & Key("SK").between(
                    f"DATE#{start_date}", f"DATE#{end_date}"
                )
            elif start_date:
                kwargs["KeyConditionExpression"] = Key("PK").eq(pk) & Key("SK").gte(
                    f"DATE#{start_date}"
                )
            response = table.query(**kwargs)
            items.extend(response.get("Items", []))

        records = [_deserialize_pnl_item(item) for item in items]
        records.sort(key=lambda r: r.date)
        return records

    @staticmethod
    def get_all_pnl_records(
        table: Any,  # noqa: ANN401
        account_id: str,
    ) -> list[DailyPnLEntry]:
        """Return all PnL records for an account.

        Args:
            table: boto3 DynamoDB Table resource.
            account_id: Alpaca account identifier.

        Returns:
            Chronologically sorted list of DailyPnLEntry DTOs.

        """
        return AccountDataReader.get_pnl_history(table, account_id)

    @staticmethod
    def get_snapshot_timestamp(
        table: Any,  # noqa: ANN401
        account_id: str,
    ) -> str | None:
        """Get the timestamp of the latest account snapshot.

        Useful for displaying "data last updated" in the dashboard.

        Args:
            table: boto3 DynamoDB Table resource.
            account_id: Alpaca account identifier.

        Returns:
            ISO timestamp string or None.

        """
        pointer = table.get_item(
            Key={"PK": f"LATEST#{account_id}", "SK": "ACCOUNT"},
        ).get("Item")

        if not pointer:
            return None

        result: str | None = pointer.get("updated_at")
        return result


# ======================================================================
# Private deserialization helpers
# ======================================================================


def _deserialize_account_item(item: dict[str, Any]) -> dict[str, Any]:
    """Convert a DynamoDB account snapshot item back to an account dict.

    The dict shape matches what AlpacaAccountService.get_account_dict() returns
    so dashboard code can switch between sources transparently.
    """
    data = item.get("account_data")
    if isinstance(data, str):
        data = json.loads(data)
    if not data:
        data = {}

    # Convert any Decimal values back to strings (DynamoDB stores numbers as Decimal)
    result: dict[str, Any] = _convert_decimals(data)
    return result


def _deserialize_positions_item(item: dict[str, Any]) -> list[PositionSnapshot]:
    """Convert a DynamoDB positions snapshot item to a list of PositionSnapshot."""
    raw = item.get("positions_data")
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not raw or not isinstance(raw, list):
        return []

    results: list[PositionSnapshot] = []
    for pos in raw:
        try:
            results.append(
                PositionSnapshot(
                    symbol=str(pos.get("symbol", "")),
                    qty=Decimal(str(pos.get("qty", "0"))),
                    avg_entry_price=Decimal(str(pos.get("avg_entry_price", "0"))),
                    current_price=Decimal(str(pos.get("current_price", "0"))),
                    market_value=Decimal(str(pos.get("market_value", "0"))),
                    cost_basis=Decimal(str(pos.get("cost_basis", "0"))),
                    unrealized_pl=Decimal(str(pos.get("unrealized_pl", "0"))),
                    unrealized_plpc=Decimal(str(pos.get("unrealized_plpc", "0"))),
                    side=str(pos.get("side", "long")),
                    asset_class=str(pos.get("asset_class", "us_equity")),
                )
            )
        except Exception:
            logger.warning(
                "Failed to parse position snapshot",
                extra={"symbol": pos.get("symbol", "unknown")},
                exc_info=True,
            )
    return results


def _deserialize_pnl_item(item: dict[str, Any]) -> DailyPnLEntry:
    """Convert a DynamoDB PnL item to a DailyPnLEntry DTO."""
    # SK is DATE#YYYY-MM-DD
    sk = str(item.get("SK", ""))
    date_str = sk.replace("DATE#", "") if sk.startswith("DATE#") else sk

    deposit_val = item.get("deposit")
    withdrawal_val = item.get("withdrawal")

    return DailyPnLEntry(
        date=date_str,
        equity=Decimal(str(item.get("equity", "0"))),
        profit_loss=Decimal(str(item.get("profit_loss", "0"))),
        profit_loss_pct=Decimal(str(item.get("profit_loss_pct", "0"))),
        deposit=Decimal(str(deposit_val)) if deposit_val is not None else None,
        withdrawal=Decimal(str(withdrawal_val)) if withdrawal_val is not None else None,
    )


def _convert_decimals(obj: Any) -> Any:  # noqa: ANN401
    """Recursively convert Decimal values to strings in a dict/list.

    DynamoDB returns numbers as Decimal. The dashboard code expects strings
    for financial values (matching the Alpaca API response format).
    """
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_decimals(v) for v in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    return obj
