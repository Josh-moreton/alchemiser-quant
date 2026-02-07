"""Business Unit: scripts | Status: current.

Data access layer for the Strategy Performance dashboard page.

Reads from two DynamoDB tables:
- StrategyPerformanceTable: pre-computed P&L snapshots (LATEST + time-series)
- TradeLedgerTable: strategy lots, trade links, and strategy metadata

All functions are cached via st.cache_data for efficient Streamlit re-renders.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import boto3
import streamlit as st
from boto3.dynamodb.conditions import Attr, Key
from dashboard_settings import get_dashboard_settings
from mypy_boto3_dynamodb.service_resource import Table as DynamoDBTable

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_decimal(value: str | int | float | Decimal | None, default: float = 0.0) -> float:
    """Safely convert a DynamoDB numeric string to float."""
    if value is None:
        return default
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return default


def _get_trade_ledger_table() -> DynamoDBTable:
    """Get a boto3 Table resource for the trade ledger."""
    settings = get_dashboard_settings()
    dynamodb = boto3.resource("dynamodb", **settings.get_boto3_client_kwargs())
    return dynamodb.Table(settings.trade_ledger_table)


def _get_strategy_performance_table() -> DynamoDBTable:
    """Get a boto3 Table resource for strategy performance snapshots."""
    settings = get_dashboard_settings()
    dynamodb = boto3.resource("dynamodb", **settings.get_boto3_client_kwargs())
    return dynamodb.Table(settings.strategy_performance_table)


def _has_credentials() -> bool:
    """Check if AWS credentials are configured."""
    settings = get_dashboard_settings()
    return settings.has_aws_credentials()


# ---------------------------------------------------------------------------
# Strategy Performance Table (pre-computed snapshots)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)
def get_all_strategy_snapshots() -> list[dict[str, Any]]:
    """Fetch the LATEST performance snapshot for every strategy.

    Queries PK=LATEST, SK begins_with STRATEGY# from the
    StrategyPerformanceTable. Returns one dict per strategy with
    realized_pnl, win_rate, completed_trades, etc.
    """
    if not _has_credentials():
        return []

    try:
        table = _get_strategy_performance_table()
        response = table.query(
            KeyConditionExpression=(Key("PK").eq("LATEST") & Key("SK").begins_with("STRATEGY#")),
        )
        items = response.get("Items", [])

        # Handle pagination (unlikely for LATEST but be safe)
        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=(
                    Key("PK").eq("LATEST") & Key("SK").begins_with("STRATEGY#")
                ),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [
            {
                "strategy_name": item.get("strategy_name", ""),
                "realized_pnl": _safe_decimal(item.get("realized_pnl")),
                "current_holdings_value": _safe_decimal(item.get("current_holdings_value")),
                "current_holdings": int(item.get("current_holdings", 0)),
                "completed_trades": int(item.get("completed_trades", 0)),
                "winning_trades": int(item.get("winning_trades", 0)),
                "losing_trades": int(item.get("losing_trades", 0)),
                "win_rate": _safe_decimal(item.get("win_rate")),
                "avg_profit_per_trade": _safe_decimal(item.get("avg_profit_per_trade")),
                "snapshot_timestamp": item.get("snapshot_timestamp", ""),
            }
            for item in items
            if item.get("strategy_name")
        ]

    except Exception as e:
        st.error(f"Error loading strategy snapshots: {e}")
        return []


@st.cache_data(ttl=60)
def get_strategy_time_series(strategy_name: str) -> list[dict[str, Any]]:
    """Fetch historical performance snapshots for a single strategy.

    Queries PK=STRATEGY#{name} from the StrategyPerformanceTable.
    Items have a 90-day TTL so this returns up to ~90 days of data.
    """
    if not _has_credentials():
        return []

    try:
        table = _get_strategy_performance_table()
        response = table.query(
            KeyConditionExpression=(
                Key("PK").eq(f"STRATEGY#{strategy_name}") & Key("SK").begins_with("SNAPSHOT#")
            ),
            ScanIndexForward=True,  # oldest first
        )
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=(
                    Key("PK").eq(f"STRATEGY#{strategy_name}") & Key("SK").begins_with("SNAPSHOT#")
                ),
                ScanIndexForward=True,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [
            {
                "snapshot_timestamp": item.get("snapshot_timestamp", ""),
                "realized_pnl": _safe_decimal(item.get("realized_pnl")),
                "current_holdings_value": _safe_decimal(item.get("current_holdings_value")),
                "current_holdings": int(item.get("current_holdings", 0)),
                "completed_trades": int(item.get("completed_trades", 0)),
                "winning_trades": int(item.get("winning_trades", 0)),
                "losing_trades": int(item.get("losing_trades", 0)),
                "win_rate": _safe_decimal(item.get("win_rate")),
                "avg_profit_per_trade": _safe_decimal(item.get("avg_profit_per_trade")),
            }
            for item in items
        ]

    except Exception as e:
        st.error(f"Error loading time series for {strategy_name}: {e}")
        return []


@st.cache_data(ttl=60)
def get_capital_deployed() -> float | None:
    """Fetch the latest capital deployed percentage."""
    if not _has_credentials():
        return None

    try:
        table = _get_strategy_performance_table()
        response = table.get_item(
            Key={"PK": "LATEST", "SK": "CAPITAL_DEPLOYED"},
        )
        item = response.get("Item")
        if item:
            return _safe_decimal(item.get("capital_deployed_pct"))
        return None

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Trade Ledger: Strategy Lots
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)
def get_strategy_lots(strategy_name: str) -> dict[str, list[dict[str, Any]]]:
    """Fetch open and closed lots for a strategy via GSI5.

    Returns dict with "open" and "closed" lists.
    """
    if not _has_credentials():
        return {"open": [], "closed": []}

    try:
        table = _get_trade_ledger_table()
        result: dict[str, list[dict[str, Any]]] = {"open": [], "closed": []}

        for status in ("OPEN", "CLOSED"):
            response = table.query(
                IndexName="GSI5-StrategyLotsIndex",
                KeyConditionExpression=(
                    Key("GSI5PK").eq(f"STRATEGY_LOTS#{strategy_name}")
                    & Key("GSI5SK").begins_with(f"{status}#")
                ),
                ScanIndexForward=False,  # newest first
            )
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response:
                response = table.query(
                    IndexName="GSI5-StrategyLotsIndex",
                    KeyConditionExpression=(
                        Key("GSI5PK").eq(f"STRATEGY_LOTS#{strategy_name}")
                        & Key("GSI5SK").begins_with(f"{status}#")
                    ),
                    ScanIndexForward=False,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            for item in items:
                lot = _parse_lot_item(item)
                result[status.lower()].append(lot)

        return result

    except Exception as e:
        st.error(f"Error loading lots for {strategy_name}: {e}")
        return {"open": [], "closed": []}


def _parse_lot_item(item: dict[str, Any]) -> dict[str, Any]:
    """Parse a raw DynamoDB lot item into a display-friendly dict."""
    exit_records = item.get("exit_records", [])
    if isinstance(exit_records, list):
        parsed_exits = []
        for ex in exit_records:
            parsed_exits.append(
                {
                    "exit_timestamp": ex.get("exit_timestamp", ""),
                    "exit_qty": _safe_decimal(ex.get("exit_qty")),
                    "exit_price": _safe_decimal(ex.get("exit_price")),
                    "realized_pnl": _safe_decimal(ex.get("realized_pnl")),
                }
            )
    else:
        parsed_exits = []

    total_realized_pnl = sum(e["realized_pnl"] for e in parsed_exits)

    entry_price = _safe_decimal(item.get("entry_price"))
    entry_qty = _safe_decimal(item.get("entry_qty"))
    remaining_qty = _safe_decimal(item.get("remaining_qty"))

    return {
        "lot_id": item.get("lot_id", ""),
        "symbol": item.get("symbol", ""),
        "entry_timestamp": item.get("entry_timestamp", ""),
        "entry_price": entry_price,
        "entry_qty": entry_qty,
        "remaining_qty": remaining_qty,
        "cost_basis": entry_price * entry_qty,
        "realized_pnl": total_realized_pnl,
        "exit_records": parsed_exits,
        "is_open": remaining_qty > 0,
        "fully_closed_at": item.get("fully_closed_at", ""),
        "correlation_id": item.get("correlation_id", ""),
    }


# ---------------------------------------------------------------------------
# Trade Ledger: Strategy Trades via GSI3
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)
def get_strategy_trades(strategy_name: str) -> list[dict[str, Any]]:
    """Fetch all trades attributed to a strategy via GSI3.

    Returns trade link items with weight, value, and direction.
    """
    if not _has_credentials():
        return []

    try:
        table = _get_trade_ledger_table()
        response = table.query(
            IndexName="GSI3-StrategyIndex",
            KeyConditionExpression=(
                Key("GSI3PK").eq(f"STRATEGY#{strategy_name}") & Key("GSI3SK").begins_with("TRADE#")
            ),
            ScanIndexForward=False,
        )
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.query(
                IndexName="GSI3-StrategyIndex",
                KeyConditionExpression=(
                    Key("GSI3PK").eq(f"STRATEGY#{strategy_name}")
                    & Key("GSI3SK").begins_with("TRADE#")
                ),
                ScanIndexForward=False,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        return [
            {
                "order_id": item.get("order_id", ""),
                "symbol": item.get("symbol", ""),
                "direction": item.get("direction", ""),
                "weight": _safe_decimal(item.get("weight")),
                "quantity": _safe_decimal(item.get("quantity")),
                "price": _safe_decimal(item.get("price")),
                "strategy_trade_value": _safe_decimal(item.get("strategy_trade_value")),
                "fill_timestamp": item.get("fill_timestamp", ""),
                "correlation_id": item.get("correlation_id", ""),
            }
            for item in items
            if item.get("EntityType") == "STRATEGY_TRADE"
        ]

    except Exception as e:
        st.error(f"Error loading trades for {strategy_name}: {e}")
        return []


# ---------------------------------------------------------------------------
# Trade Ledger: Strategy Metadata (from strategy_ledger.py sync)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def get_all_strategy_metadata() -> dict[str, dict[str, Any]]:
    """Fetch all strategy metadata from the trade ledger.

    Queries GSI3 PK=STRATEGIES, SK begins_with METADATA# to find
    all synced strategy ledger entries. Returns a dict keyed by
    strategy_name for easy lookup.
    """
    if not _has_credentials():
        return {}

    try:
        table = _get_trade_ledger_table()
        response = table.query(
            IndexName="GSI3-StrategyIndex",
            KeyConditionExpression=(
                Key("GSI3PK").eq("STRATEGIES") & Key("GSI3SK").begins_with("METADATA#")
            ),
        )
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.query(
                IndexName="GSI3-StrategyIndex",
                KeyConditionExpression=(
                    Key("GSI3PK").eq("STRATEGIES") & Key("GSI3SK").begins_with("METADATA#")
                ),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        result: dict[str, dict[str, Any]] = {}
        for item in items:
            name = item.get("strategy_name", "")
            if name:
                result[name] = {
                    "display_name": item.get("display_name", name),
                    "source_url": item.get("source_url", ""),
                    "filename": item.get("filename", ""),
                    "date_updated": item.get("date_updated", ""),
                    "assets": item.get("assets", []),
                    "frontrunners": item.get("frontrunners", []),
                }

        return result

    except Exception as e:
        st.error(f"Error loading strategy metadata: {e}")
        return {}


# ---------------------------------------------------------------------------
# Attribution Coverage / Data Quality
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def get_attribution_coverage(days: int = 30) -> dict[str, Any]:
    """Assess attribution data quality for recent trades.

    Scans recent trades and reports how many have complete strategy
    attribution (non-empty strategy_names and strategy_weights).

    Args:
        days: Number of days to look back.

    Returns:
        Dict with total_trades, attributed_trades, coverage_pct, and
        unattributed list for drill-down.

    """
    if not _has_credentials():
        return {
            "total_trades": 0,
            "attributed_trades": 0,
            "coverage_pct": 0.0,
            "unattributed": [],
        }

    try:
        table = _get_trade_ledger_table()
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        response = table.scan(
            FilterExpression=(Attr("EntityType").eq("TRADE") & Attr("fill_timestamp").gte(cutoff)),
            ProjectionExpression=(
                "order_id, symbol, direction, fill_timestamp, strategy_names, strategy_weights"
            ),
        )
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression=(
                    Attr("EntityType").eq("TRADE") & Attr("fill_timestamp").gte(cutoff)
                ),
                ProjectionExpression=(
                    "order_id, symbol, direction, fill_timestamp, strategy_names, strategy_weights"
                ),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        total = len(items)
        attributed = 0
        unattributed: list[dict[str, Any]] = []

        for item in items:
            strategy_names = item.get("strategy_names", [])
            strategy_weights = item.get("strategy_weights")

            has_names = isinstance(strategy_names, list) and len(strategy_names) > 0
            has_weights = isinstance(strategy_weights, dict) and len(strategy_weights) > 0

            if has_names and has_weights:
                attributed += 1
            else:
                unattributed.append(
                    {
                        "order_id": item.get("order_id", ""),
                        "symbol": item.get("symbol", ""),
                        "direction": item.get("direction", ""),
                        "fill_timestamp": item.get("fill_timestamp", ""),
                        "has_names": has_names,
                        "has_weights": has_weights,
                    }
                )

        coverage = (attributed / total * 100) if total > 0 else 100.0

        return {
            "total_trades": total,
            "attributed_trades": attributed,
            "coverage_pct": coverage,
            "unattributed": unattributed,
        }

    except Exception as e:
        st.error(f"Error checking attribution coverage: {e}")
        return {
            "total_trades": 0,
            "attributed_trades": 0,
            "coverage_pct": 0.0,
            "unattributed": [],
        }
