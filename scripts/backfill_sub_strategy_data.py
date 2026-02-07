#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Backfill the Group Historical Selections DynamoDB cache.

The Sub-Strategy Data Lambda runs daily and adds one entry per group per day.
For the filter scoring to work immediately (e.g. a 10-day moving average
needs ~10 trading days of data), we need to populate historical entries.

This script invokes the Sub-Strategy Data Lambda with a ``date`` override for
each trading day in the requested range to backfill the cache.

Usage:
    # Backfill the last 20 calendar days (default) to dev table
    python scripts/backfill_sub_strategy_data.py

    # Backfill a specific range
    python scripts/backfill_sub_strategy_data.py --start 2026-01-20 --end 2026-02-05

    # Specify stage
    python scripts/backfill_sub_strategy_data.py --stage dev --days 25

    # Dry-run: show which dates would be backfilled
    python scripts/backfill_sub_strategy_data.py --dry-run

Environment Variables:
    AWS_PROFILE / AWS_DEFAULT_REGION: For boto3 session
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime, timedelta

import _setup_imports  # noqa: F401

import boto3

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# weekdays only (Mon-Fri)
_WEEKDAYS = {0, 1, 2, 3, 4}

# Known US market holidays in 2026 (extend as needed)
_US_MARKET_HOLIDAYS_2026 = {
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # MLK Day
    date(2026, 2, 16),  # Presidents' Day
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 25),  # Memorial Day
    date(2026, 7, 3),   # Independence Day (observed)
    date(2026, 9, 7),   # Labor Day
    date(2026, 11, 26), # Thanksgiving
    date(2026, 12, 25), # Christmas
}


def _is_trading_day(d: date) -> bool:
    """Check if a date is a US equity trading day (weekday, not holiday)."""
    return d.weekday() in _WEEKDAYS and d not in _US_MARKET_HOLIDAYS_2026


def _get_trading_days(start: date, end: date) -> list[date]:
    """Return list of trading days in [start, end] inclusive, oldest first."""
    days = []
    current = start
    while current <= end:
        if _is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def _resolve_function_name(stage: str) -> str:
    """Resolve the Lambda function name for the given stage."""
    return f"alchemiser-{stage}-sub-strategy-data"


def main() -> None:
    """Run the backfill."""
    parser = argparse.ArgumentParser(
        description="Backfill sub-strategy data DynamoDB table with historical data"
    )
    parser.add_argument(
        "--stage",
        default="dev",
        choices=["dev", "prod"],
        help="Deployment stage (default: dev)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=20,
        help="Number of calendar days to backfill (default: 20)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD). Overrides --days",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD). Default: today",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show dates that would be backfilled without invoking Lambda",
    )
    args = parser.parse_args()

    # Determine date range
    if args.end:
        end_date = date.fromisoformat(args.end)
    else:
        end_date = datetime.now(UTC).date()

    if args.start:
        start_date = date.fromisoformat(args.start)
    else:
        start_date = end_date - timedelta(days=args.days)

    trading_days = _get_trading_days(start_date, end_date)
    function_name = _resolve_function_name(args.stage)

    print(f"Backfill Sub-Strategy Data: {function_name}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Trading days to process: {len(trading_days)}")
    print()

    if args.dry_run:
        print("DRY RUN - would backfill these dates:")
        for d in trading_days:
            print(f"  {d.isoformat()} ({d.strftime('%A')})")
        print(f"\nTotal: {len(trading_days)} trading days")
        return

    # Invoke Lambda for each trading day
    lambda_client = boto3.client("lambda")
    successes = 0
    failures = 0

    for i, d in enumerate(trading_days, 1):
        date_str = d.isoformat()
        print(f"[{i}/{len(trading_days)}] Processing {date_str}...", end=" ", flush=True)

        payload = {
            "date": date_str,
            "correlation_id": f"backfill-{date_str}",
        }

        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            response_payload = json.loads(response["Payload"].read())
            status_code = response_payload.get("statusCode", 0)

            if status_code == 200:
                body = response_payload.get("body", {})
                group_count = body.get("successes", 0)
                print(f"OK ({group_count} groups cached)")
                successes += 1
            else:
                error = response_payload.get("body", {}).get("error", "unknown")
                print(f"FAILED: {error}")
                failures += 1

        except Exception as e:
            print(f"ERROR: {e}")
            failures += 1

    print()
    print(f"Backfill complete: {successes} succeeded, {failures} failed")

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
