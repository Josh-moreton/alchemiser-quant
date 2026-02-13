"""Business Unit: strategy_analytics | Status: current.

Lambda handler for Strategy Analytics microservice.

Reads per-strategy lots from the trade ledger DynamoDB table, computes
daily returns and summary metrics, then writes results to S3 as Parquet
and JSON files. Triggered daily by an EventBridge schedule after market
close.

S3 Output Layout
----------------
strategy-analytics/
    {strategy_name}/daily_returns.parquet   -- date-indexed daily P&L
    {strategy_name}/metrics.json            -- summary risk/return metrics
    summary.parquet                         -- one row per strategy
    _manifest.json                          -- run metadata
"""

from __future__ import annotations

import io
import json
import math
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.strategy_lot import StrategyLot

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)

configure_application_logging()
logger = get_logger(__name__)

S3_PREFIX = "strategy-analytics"
TRADING_DAYS_PER_YEAR = 252


def _decimal_to_float(val: Decimal | float | int | str | None) -> float:
    """Safely convert a Decimal or numeric value to float."""
    if val is None:
        return 0.0
    return float(val)


def _build_daily_returns(lots: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a date-indexed daily realised P&L series from closed lots.

    Each lot exit record contributes its realised_pnl to the date it
    was closed. Open lots are excluded -- they have no realised P&L yet.

    Returns a DataFrame with columns ``date`` (datetime64) and ``pnl``.
    """
    daily: dict[str, float] = {}

    for lot in lots:
        exit_records = lot.get("exit_records", [])
        if not isinstance(exit_records, list):
            continue
        for ex in exit_records:
            ts = ex.get("exit_timestamp", "")
            if not ts:
                continue
            date_str = ts[:10]
            pnl = _decimal_to_float(ex.get("realized_pnl"))
            daily[date_str] = daily.get(date_str, 0.0) + pnl

    if not daily:
        return pd.DataFrame(columns=["date", "pnl"])

    rows = sorted(daily.items(), key=lambda x: x[0])
    df = pd.DataFrame(rows, columns=["date", "pnl"])
    df["date"] = pd.to_datetime(df["date"], utc=True)
    return df


def _compute_metrics(
    df: pd.DataFrame,
    lots: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute summary risk/return metrics from daily P&L data and lots.

    Metrics computed:
    - total_realized_pnl, total_trades, winning_trades, losing_trades, win_rate
    - pnl_sharpe, max_drawdown, max_drawdown_pct, annualized_volatility
    - profit_factor, avg_profit_per_trade
    - current_holdings (open lots count), current_holdings_value
    """
    # Lot-level stats
    total_pnl = 0.0
    total_trades = 0
    winning = 0
    losing = 0
    open_lots = 0
    open_value = 0.0

    for lot in lots:
        remaining = _decimal_to_float(lot.get("remaining_qty", 0))
        if remaining > 0:
            open_lots += 1
            open_value += remaining * _decimal_to_float(lot.get("entry_price", 0))
        exits = lot.get("exit_records", [])
        if not isinstance(exits, list):
            continue
        for ex in exits:
            pnl = _decimal_to_float(ex.get("realized_pnl"))
            total_pnl += pnl
            total_trades += 1
            if pnl > 0:
                winning += 1
            elif pnl < 0:
                losing += 1

    win_rate = (winning / total_trades * 100.0) if total_trades > 0 else 0.0
    avg_profit = total_pnl / total_trades if total_trades > 0 else 0.0

    # Time-series metrics (need >= 3 daily observations)
    pnl_sharpe = 0.0
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    volatility = 0.0
    profit_factor: float | None = None

    if len(df) >= 3:
        pnl_values = df["pnl"].tolist()
        cum_pnl = [sum(pnl_values[: i + 1]) for i in range(len(pnl_values))]

        # Daily changes
        daily_changes = pnl_values  # each row IS the daily change

        avg_change = sum(daily_changes) / len(daily_changes)
        variance = sum((c - avg_change) ** 2 for c in daily_changes) / max(
            len(daily_changes) - 1, 1
        )
        std_change = math.sqrt(variance)
        if std_change > 0:
            pnl_sharpe = (avg_change / std_change) * math.sqrt(TRADING_DAYS_PER_YEAR)

        # Max drawdown on cumulative P&L
        peak = cum_pnl[0]
        for val in cum_pnl:
            if val > peak:
                peak = val
            dd = peak - val
            if dd > max_drawdown:
                max_drawdown = dd
                if not math.isclose(peak, 0.0, abs_tol=1e-9):
                    max_drawdown_pct = (dd / abs(peak)) * 100.0

        volatility = std_change * math.sqrt(TRADING_DAYS_PER_YEAR)

        # Profit factor
        gross_wins = sum(c for c in daily_changes if c > 0)
        gross_losses = abs(sum(c for c in daily_changes if c < 0))
        if not math.isclose(gross_losses, 0.0, abs_tol=1e-9):
            profit_factor = gross_wins / gross_losses

    return {
        "total_realized_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "winning_trades": winning,
        "losing_trades": losing,
        "win_rate": round(win_rate, 2),
        "avg_profit_per_trade": round(avg_profit, 2),
        "current_holdings": open_lots,
        "current_holdings_value": round(open_value, 2),
        "pnl_sharpe": round(pnl_sharpe, 4),
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "annualized_volatility": round(volatility, 2),
        "profit_factor": round(profit_factor, 4) if profit_factor is not None else None,
        "data_points": len(df),
    }


def _write_parquet_to_s3(
    s3_client: S3Client,
    bucket: str,
    key: str,
    df: pd.DataFrame,
) -> None:
    """Write a DataFrame to S3 as Parquet (snappy compression)."""
    buf = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue(),
        ContentType="application/octet-stream",
    )


def _write_json_to_s3(
    s3_client: S3Client,
    bucket: str,
    key: str,
    data: dict[str, Any],
) -> None:
    """Write a JSON dict to S3."""
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, default=str).encode("utf-8"),
        ContentType="application/json",
    )


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Compute strategy analytics and write results to S3.

    Triggered daily by EventBridge schedule. Reads all strategy lots
    from the trade ledger, computes daily returns and metrics per
    strategy, and writes Parquet/JSON to S3.

    Args:
        event: Lambda event (EventBridge schedule or direct invoke).
        context: Lambda context.

    Returns:
        Response with processed strategy count.

    """
    run_id = str(uuid.uuid4())[:8]
    run_timestamp = datetime.now(UTC).isoformat()

    table_name = os.environ.get("TRADE_LEDGER__TABLE_NAME", "")
    bucket_name = os.environ.get("PERFORMANCE_REPORTS_BUCKET", "")
    stage = os.environ.get("STAGE", "dev")

    if not table_name or not bucket_name:
        logger.error(
            "Missing required environment variables",
            extra={"table_name": table_name, "bucket_name": bucket_name},
        )
        return {"statusCode": 500, "body": {"error": "Missing configuration"}}

    logger.info(
        "Strategy analytics run starting",
        extra={"run_id": run_id, "stage": stage},
    )

    repo = DynamoDBTradeLedgerRepository(table_name=table_name)
    s3_client = boto3.client("s3")

    # Discover all strategies
    strategy_summaries = repo.get_all_strategy_summaries()
    strategy_names = [s["strategy_name"] for s in strategy_summaries if s.get("strategy_name")]

    if not strategy_names:
        logger.warning("No strategies found in trade ledger")
        return {"statusCode": 200, "body": {"strategies_processed": 0}}

    logger.info(
        "Processing strategies",
        extra={"count": len(strategy_names), "names": strategy_names},
    )

    summary_rows: list[dict[str, Any]] = []

    for strategy_name in strategy_names:
        try:
            lots = repo.query_all_lots_by_strategy(strategy_name)
            # Convert StrategyLot objects to dicts for processing
            lot_dicts = [_lot_to_dict(lot) for lot in lots]

            daily_df = _build_daily_returns(lot_dicts)
            metrics = _compute_metrics(daily_df, lot_dicts)
            metrics["strategy_name"] = strategy_name

            # Write per-strategy daily returns
            if not daily_df.empty:
                _write_parquet_to_s3(
                    s3_client,
                    bucket_name,
                    f"{S3_PREFIX}/{strategy_name}/daily_returns.parquet",
                    daily_df,
                )

            # Write per-strategy metrics
            _write_json_to_s3(
                s3_client,
                bucket_name,
                f"{S3_PREFIX}/{strategy_name}/metrics.json",
                metrics,
            )

            summary_rows.append(metrics)

            logger.info(
                "Strategy analytics written",
                extra={
                    "strategy": strategy_name,
                    "trades": metrics["total_trades"],
                    "pnl": metrics["total_realized_pnl"],
                },
            )

        except Exception:
            logger.exception(
                "Failed to process strategy",
                extra={"strategy": strategy_name},
            )

    # Write summary parquet (one row per strategy)
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        _write_parquet_to_s3(
            s3_client,
            bucket_name,
            f"{S3_PREFIX}/summary.parquet",
            summary_df,
        )

    # Write manifest
    manifest = {
        "run_id": run_id,
        "run_timestamp": run_timestamp,
        "stage": stage,
        "strategies_processed": len(summary_rows),
        "strategy_names": [r["strategy_name"] for r in summary_rows],
    }
    _write_json_to_s3(
        s3_client,
        bucket_name,
        f"{S3_PREFIX}/_manifest.json",
        manifest,
    )

    logger.info(
        "Strategy analytics run complete",
        extra={"run_id": run_id, "strategies": len(summary_rows)},
    )

    return {
        "statusCode": 200,
        "body": {
            "run_id": run_id,
            "strategies_processed": len(summary_rows),
        },
    }


def _lot_to_dict(lot: StrategyLot) -> dict[str, Any]:
    """Convert a StrategyLot Pydantic model to a plain dict for processing."""
    exit_records = []
    for ex in lot.exit_records:
        exit_records.append(
            {
                "exit_timestamp": ex.exit_timestamp if hasattr(ex, "exit_timestamp") else "",
                "exit_qty": _decimal_to_float(ex.exit_qty) if hasattr(ex, "exit_qty") else 0.0,
                "exit_price": _decimal_to_float(ex.exit_price)
                if hasattr(ex, "exit_price")
                else 0.0,
                "realized_pnl": _decimal_to_float(ex.realized_pnl)
                if hasattr(ex, "realized_pnl")
                else 0.0,
            }
        )
    return {
        "lot_id": lot.lot_id,
        "strategy_name": lot.strategy_name,
        "symbol": lot.symbol,
        "entry_timestamp": lot.entry_timestamp,
        "entry_price": _decimal_to_float(lot.entry_price),
        "entry_qty": _decimal_to_float(lot.entry_qty),
        "remaining_qty": _decimal_to_float(lot.remaining_qty),
        "is_open": lot.is_open,
        "exit_records": exit_records,
    }
