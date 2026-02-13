"""Business Unit: dashboard | Status: current.

Data access layer for the Strategy Performance dashboard page.

Reads from two sources:
- S3 PerformanceReportsBucket: strategy analytics Parquet/JSON (metrics, daily returns)
- TradeLedgerTable: strategy lots, trade links, and strategy metadata

All functions are cached via st.cache_data for efficient Streamlit re-renders.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

import boto3
import pandas as pd
from botocore.exceptions import ClientError
import streamlit as st
from boto3.dynamodb.conditions import Attr, Key
from settings import get_dashboard_settings

from data import account as account_access

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
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
    table_name = settings.trade_ledger_table
    logger.info("Using trade ledger table: %s (stage=%s)", table_name, settings.stage)
    return dynamodb.Table(table_name)


def _get_s3_client() -> Any:
    """Get a boto3 S3 client with dashboard credentials."""
    settings = get_dashboard_settings()
    return boto3.client("s3", **settings.get_boto3_client_kwargs())


def _get_reports_bucket() -> str:
    """Get the performance reports S3 bucket name."""
    return get_dashboard_settings().strategy_performance_bucket


def _has_credentials() -> bool:
    """Check if AWS credentials are available (explicit or default chain)."""
    settings = get_dashboard_settings()
    if settings.has_aws_credentials():
        return True
    # Fall back: check if the default credential chain can resolve credentials
    try:
        session = boto3.Session(**settings.get_boto3_client_kwargs())
        creds = session.get_credentials()
        return creds is not None
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Strategy Analytics (from S3 Parquet/JSON)
# ---------------------------------------------------------------------------

S3_ANALYTICS_PREFIX = "strategy-analytics"
S3_REPORTS_PREFIX = "strategy-reports"


@st.cache_data(ttl=60)
def get_all_strategy_snapshots() -> list[dict[str, Any]]:
    """Fetch the latest metrics for every strategy from S3.

    Reads the summary.parquet written by the Strategy Analytics Lambda.
    Returns one dict per strategy with realized_pnl, win_rate, etc.
    """
    if not _has_credentials():
        return []

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()
        response = s3.get_object(
            Bucket=bucket,
            Key=f"{S3_ANALYTICS_PREFIX}/summary.parquet",
        )
        buf = io.BytesIO(response["Body"].read())
        df = pd.read_parquet(buf)

        if df.empty:
            return []

        snapshots = []
        for _, row in df.iterrows():
            snapshots.append({
                "strategy_name": row.get("strategy_name", ""),
                "realized_pnl": float(row.get("total_realized_pnl", 0)),
                "current_holdings_value": float(row.get("current_holdings_value", 0)),
                "current_holdings": int(row.get("current_holdings", 0)),
                "completed_trades": int(row.get("total_trades", 0)),
                "winning_trades": int(row.get("winning_trades", 0)),
                "losing_trades": int(row.get("losing_trades", 0)),
                "win_rate": float(row.get("win_rate", 0)),
                "avg_profit_per_trade": float(row.get("avg_profit_per_trade", 0)),
                "pnl_sharpe": float(row.get("pnl_sharpe", 0)),
                "max_drawdown": float(row.get("max_drawdown", 0)),
                "max_drawdown_pct": float(row.get("max_drawdown_pct", 0)),
                "annualized_volatility": float(row.get("annualized_volatility", 0)),
                "profit_factor": (
                    float(row["profit_factor"])
                    if row.get("profit_factor") is not None
                    and not pd.isna(row.get("profit_factor"))
                    else None
                ),
            })
        return snapshots

    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.info("No strategy analytics summary found yet")
            return []
        st.error(f"Error loading strategy snapshots: {e}")
        return []
    except Exception as e:
        st.error(f"Error loading strategy snapshots: {e}")
        return []


@st.cache_data(ttl=60)
def get_strategy_time_series(strategy_name: str) -> list[dict[str, Any]]:
    """Fetch historical daily returns for a single strategy from S3.

    Reads the daily_returns.parquet written by the Strategy Analytics Lambda.
    Returns a list of dicts with ``date`` and ``realized_pnl`` (cumulative).
    """
    if not _has_credentials():
        return []

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()
        response = s3.get_object(
            Bucket=bucket,
            Key=f"{S3_ANALYTICS_PREFIX}/{strategy_name}/daily_returns.parquet",
        )
        buf = io.BytesIO(response["Body"].read())
        df = pd.read_parquet(buf)

        if df.empty:
            return []

        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.sort_values("date")

        # Build cumulative P&L for time-series display
        cum_pnl = df["pnl"].cumsum()

        return [
            {
                "snapshot_timestamp": row["date"].isoformat(),
                "realized_pnl": float(cum_val),
                "daily_pnl": float(row["pnl"]),
            }
            for (_, row), cum_val in zip(df.iterrows(), cum_pnl)
        ]

    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.info("No daily returns found for %s", strategy_name)
            return []
        st.error(f"Error loading time series for {strategy_name}: {e}")
        return []
    except Exception as e:
        st.error(f"Error loading time series for {strategy_name}: {e}")
        return []


@st.cache_data(ttl=60)
def get_strategy_metrics(strategy_name: str) -> dict[str, Any] | None:
    """Fetch per-strategy risk/return metrics from S3 JSON.

    Reads the metrics.json written by the Strategy Analytics Lambda.
    """
    if not _has_credentials():
        return None

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()
        response = s3.get_object(
            Bucket=bucket,
            Key=f"{S3_ANALYTICS_PREFIX}/{strategy_name}/metrics.json",
        )
        return json.loads(response["Body"].read().decode("utf-8"))  # type: ignore[no-any-return]

    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            return None
        logger.warning("Failed to load metrics for %s: %s", strategy_name, e)
        return None
    except Exception as e:
        logger.warning("Failed to load metrics for %s: %s", strategy_name, e)
        return None


@st.cache_data(ttl=60)
def get_strategy_tearsheet_url(strategy_name: str) -> str | None:
    """Generate a presigned URL for the quantstats tearsheet HTML.

    Returns a URL valid for 1 hour, or None if the report does not exist.
    """
    if not _has_credentials():
        return None

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()
        key = f"{S3_REPORTS_PREFIX}/{strategy_name}/tearsheet.html"

        # Check if the object exists first
        s3.head_object(Bucket=bucket, Key=key)

        url: str = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
        return url

    except Exception:
        return None


@st.cache_data(ttl=300)
def get_tearsheet_html(name: str) -> str | None:
    """Download the raw HTML content of a quantstats tearsheet from S3.

    Args:
        name: Strategy name or '_account' for the account-level tearsheet.

    Returns:
        HTML string, or None if the tearsheet does not exist.
    """
    if not _has_credentials():
        return None

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()
        key = f"{S3_REPORTS_PREFIX}/{name}/tearsheet.html"
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode("utf-8")  # type: ignore[no-any-return]
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "NoSuchKey":
            return None
        logger.warning("Failed to load tearsheet for %s: %s", name, e)
        return None
    except Exception as e:
        logger.warning("Failed to load tearsheet for %s: %s", name, e)
        return None


@st.cache_data(ttl=300)
def get_available_tearsheets() -> list[str]:
    """List strategy names that have a tearsheet in S3.

    Reads the analytics manifest for strategy names and checks whether
    each has a tearsheet HTML object.  Also checks for the account-level
    tearsheet (``_account``).
    """
    if not _has_credentials():
        return []

    try:
        s3 = _get_s3_client()
        bucket = _get_reports_bucket()

        # List objects under the reports prefix to discover tearsheets
        paginator = s3.get_paginator("list_objects_v2")
        available: list[str] = []
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{S3_REPORTS_PREFIX}/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/tearsheet.html"):
                    # Extract the name between the prefix and /tearsheet.html
                    parts = key.replace(f"{S3_REPORTS_PREFIX}/", "", 1)
                    name = parts.replace("/tearsheet.html", "")
                    if name:
                        available.append(name)

        return sorted(available)
    except Exception as e:
        logger.warning("Failed to discover tearsheets: %s", e)
        return []


@st.cache_data(ttl=60)
def get_capital_deployed() -> float | None:
    """Compute capital deployed percentage from strategy snapshots.

    Derives this from the total current holdings value relative to
    portfolio equity. Returns None if data is unavailable.
    """
    snapshots = get_all_strategy_snapshots()
    if not snapshots:
        return None

    total_holdings_value = sum(s.get("current_holdings_value", 0) for s in snapshots)
    if total_holdings_value <= 0:
        return None

    # Get portfolio equity from account data
    try:
        account = account_access.get_latest_account_data()
        if account and float(account.get("equity", 0)) > 0:
            return (total_holdings_value / float(account["equity"])) * 100.0
    except Exception:
        logger.exception("Failed to compute capital deployed from account data")

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


@st.cache_data(ttl=120)
def get_current_price_map() -> dict[str, float]:
    """Build a symbol -> current_price mapping from account positions.

    Used by the open lots view to compute per-lot unrealized P&L.
    Returns an empty dict if positions cannot be loaded.
    """
    try:
        positions = account_access.get_latest_positions()
        if not positions:
            return {}
        return {
            pos.symbol: float(pos.current_price)
            for pos in positions
            if hasattr(pos, "symbol") and hasattr(pos, "current_price")
        }
    except Exception:
        logger.warning("Failed to load current prices for unrealized P&L", exc_info=True)
        return {}


@st.cache_data(ttl=900)  # 15-min TTL — full table scan, call sparingly
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
