#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Generate quantstats HTML tearsheets for each strategy and upload to S3.

quantstats exceeds the Lambda layer size limit (>250 MB), so tearsheet
generation runs locally and uploads the output to the same S3 bucket
the dashboard reads from.

Usage:
    python scripts/generate_tearsheets.py --stage dev
    python scripts/generate_tearsheets.py --stage prod
    python scripts/generate_tearsheets.py --stage dev --strategy momentum_v2
    python scripts/generate_tearsheets.py --stage dev --account

S3 Layout (reads -- strategy mode):
    strategy-analytics/{strategy_name}/daily_returns.parquet

S3 Layout (reads -- account mode):
    DynamoDB: alchemiser-{stage}-account-data
        PK=REGISTRY / SK=ACCOUNT_ID          -> account_id
        PK=PNL#{account_id} / SK=DATE#YYYY-MM-DD -> daily P&L

S3 Layout (writes):
    strategy-reports/{strategy_name}/tearsheet.html
    strategy-reports/_account/tearsheet.html
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from decimal import Decimal
from typing import Any

import boto3
import pandas as pd
import quantstats as qs

S3_ANALYTICS_PREFIX = "strategy-analytics"
S3_REPORTS_PREFIX = "strategy-reports"


def _bucket_name(stage: str) -> str:
    """Derive the S3 bucket name from the deployment stage."""
    return f"alchemiser-{stage}-reports"


def _discover_strategies(s3_client: object, bucket: str) -> list[str]:
    """Read the analytics manifest to get available strategy names."""
    try:
        response = s3_client.get_object(  # type: ignore[union-attr]
            Bucket=bucket,
            Key=f"{S3_ANALYTICS_PREFIX}/_manifest.json",
        )
        manifest = json.loads(response["Body"].read().decode("utf-8"))
        names: list[str] = manifest.get("strategy_names", [])
        return names
    except Exception as exc:
        print(f"[ERROR] Failed to read analytics manifest: {exc}")
        return []


def _read_daily_returns(s3_client: object, bucket: str, strategy_name: str) -> pd.DataFrame | None:
    """Download the daily_returns.parquet for a strategy from S3."""
    key = f"{S3_ANALYTICS_PREFIX}/{strategy_name}/daily_returns.parquet"
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)  # type: ignore[union-attr]
        buf = io.BytesIO(response["Body"].read())
        df = pd.read_parquet(buf)
        return df
    except Exception as exc:
        print(f"  [WARN] No daily returns for {strategy_name}: {exc}")
        return None


def _generate_tearsheet_html(daily_returns: pd.Series) -> str:
    """Use quantstats to render a full tearsheet as an HTML string."""
    qs.extend_pandas()
    html: str = qs.reports.html(daily_returns, output="", download_filename="tearsheet.html")
    return html


def _upload_tearsheet(s3_client: object, bucket: str, strategy_name: str, html: str) -> None:
    """Upload the tearsheet HTML to S3."""
    key = f"{S3_REPORTS_PREFIX}/{strategy_name}/tearsheet.html"
    s3_client.put_object(  # type: ignore[union-attr]
        Bucket=bucket,
        Key=key,
        Body=html.encode("utf-8"),
        ContentType="text/html",
    )
    print(f"  [OK] Uploaded s3://{bucket}/{key}")


# ---------------------------------------------------------------------------
# Account-level tearsheet (reads PnL history from DynamoDB)
# ---------------------------------------------------------------------------


def _account_table_name(stage: str) -> str:
    """Derive the DynamoDB account-data table name from the stage."""
    return f"alchemiser-{stage}-account-data"


def _discover_account_id(table: Any) -> str:
    """Read the well-known registry entry to get the Alpaca account ID."""
    item = table.get_item(Key={"PK": "REGISTRY", "SK": "ACCOUNT_ID"}).get("Item")
    if not item:
        return ""
    return str(item.get("account_id", ""))


def _read_account_pnl(table: Any, account_id: str) -> pd.DataFrame:
    """Query all daily PnL records for the account from DynamoDB.

    Returns a date-sorted DataFrame with columns: date, return_pct.
    """
    from boto3.dynamodb.conditions import Key

    pk = f"PNL#{account_id}"
    response = table.query(KeyConditionExpression=Key("PK").eq(pk))
    items: list[dict[str, Any]] = response.get("Items", [])

    while response.get("LastEvaluatedKey"):
        response = table.query(
            KeyConditionExpression=Key("PK").eq(pk),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    rows: list[dict[str, Any]] = []
    for item in items:
        sk = str(item.get("SK", ""))
        date_str = sk.replace("DATE#", "") if sk.startswith("DATE#") else sk
        equity = float(Decimal(str(item.get("equity", "0"))))
        pnl_pct = float(Decimal(str(item.get("profit_loss_pct", "0"))))
        if equity > 0:
            rows.append({"date": date_str, "return_pct": pnl_pct / 100.0})

    df = pd.DataFrame(rows, columns=["date", "return_pct"])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df = df.sort_values("date")
    return df


def _process_account_tearsheet(s3_client: object, bucket: str, stage: str) -> bool:
    """Generate a whole-account tearsheet from DynamoDB PnL history.

    Returns True if the tearsheet was generated, False otherwise.
    """
    table_name = _account_table_name(stage)
    print(f"Reading account PnL from DynamoDB table: {table_name}")

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    account_id = _discover_account_id(table)
    if not account_id:
        print("[ERROR] Could not discover account ID from registry.")
        return False
    print(f"  Account ID: {account_id}")

    df = _read_account_pnl(table, account_id)
    if df.empty:
        print("[SKIP] No PnL records found in DynamoDB.")
        return False

    returns = df.set_index("date")["return_pct"]
    returns.index.name = "Date"

    if len(returns) < 3:
        print(f"[SKIP] Only {len(returns)} data points -- need at least 3.")
        return False

    print(f"  Data points: {len(returns)} ({returns.index.min().date()} to {returns.index.max().date()})")

    html = _generate_tearsheet_html(returns)
    _upload_tearsheet(s3_client, bucket, "_account", html)
    return True


# ---------------------------------------------------------------------------
# Per-strategy tearsheet (reads Parquet from S3)
# ---------------------------------------------------------------------------


def _process_strategy(s3_client: object, bucket: str, strategy_name: str) -> bool:
    """Generate and upload a tearsheet for a single strategy.

    Returns True if the tearsheet was generated, False otherwise.
    """
    print(f"Processing: {strategy_name}")

    df = _read_daily_returns(s3_client, bucket, strategy_name)
    if df is None or df.empty:
        print(f"  [SKIP] No data for {strategy_name}")
        return False

    # Build a date-indexed returns Series from the daily P&L DataFrame.
    # The analytics Lambda writes columns: date (datetime64), pnl (float).
    if "date" not in df.columns or "pnl" not in df.columns:
        print(f"  [SKIP] Unexpected columns {list(df.columns)} for {strategy_name}")
        return False

    df = df.sort_values("date")
    returns = df.set_index("date")["pnl"]
    returns.index = pd.to_datetime(returns.index, utc=True)
    returns.index.name = "Date"

    if len(returns) < 3:
        print(f"  [SKIP] Only {len(returns)} data points for {strategy_name}")
        return False

    html = _generate_tearsheet_html(returns)
    _upload_tearsheet(s3_client, bucket, strategy_name, html)
    return True


def main() -> None:
    """Entry point -- parse args and generate tearsheets."""
    parser = argparse.ArgumentParser(
        description="Generate quantstats HTML tearsheets and upload to S3.",
    )
    parser.add_argument(
        "--stage",
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Deployment stage (determines S3 bucket name).",
    )
    parser.add_argument(
        "--strategy",
        default=None,
        help="Generate tearsheet for a single strategy only.",
    )
    parser.add_argument(
        "--account",
        action="store_true",
        default=False,
        help="Generate a whole-account tearsheet from DynamoDB PnL history.",
    )
    args = parser.parse_args()

    bucket = _bucket_name(args.stage)
    s3_client = boto3.client("s3")

    # Account mode: read from DynamoDB, generate one tearsheet, done.
    if args.account:
        print(f"Bucket: {bucket}")
        print("Mode: account tearsheet")
        print()
        ok = _process_account_tearsheet(s3_client, bucket, args.stage)
        sys.exit(0 if ok else 1)

    # Strategy mode (default): read Parquet from S3.
    if args.strategy:
        strategies = [args.strategy]
    else:
        strategies = _discover_strategies(s3_client, bucket)
        if not strategies:
            print("No strategies found in manifest. Run the analytics Lambda first.")
            sys.exit(1)

    print(f"Bucket: {bucket}")
    print(f"Strategies: {len(strategies)}")
    print()

    generated = 0
    for name in strategies:
        if _process_strategy(s3_client, bucket, name):
            generated += 1

    print()
    print(f"Done. Generated {generated}/{len(strategies)} tearsheets.")


if __name__ == "__main__":
    main()
