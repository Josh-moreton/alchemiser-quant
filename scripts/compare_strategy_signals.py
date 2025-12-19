#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Compare strategy signals between dev and production environments.

This script queries DynamoDB trade ledgers from both environments and compares
the generated signals to verify parity during migration periods.

Usage:
    python scripts/compare_strategy_signals.py --date 2025-12-09
    python scripts/compare_strategy_signals.py --date today
    python scripts/compare_strategy_signals.py --days-back 7
    python scripts/compare_strategy_signals.py --date today --time 14:35 --window 5

Output:
    - Signal comparison summary (matching vs divergent)
    - Detailed diff for any divergent signals
    - CSV export for further analysis
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3

# AWS configuration
REGION = "us-east-1"
DEV_TABLE = "alchemiser-dev-trade-ledger"
PROD_TABLE = "alchemiser-prod-trade-ledger"


class SignalRecord:
    """Simplified signal record for comparison."""

    def __init__(self, item: dict[str, Any]) -> None:
        """Initialize from DynamoDB item."""
        self.signal_id = item.get("signal_id", "")
        self.correlation_id = item.get("correlation_id", "")
        self.timestamp = item.get("timestamp", "")
        self.strategy_name = item.get("strategy_name", "")
        self.symbol = item.get("symbol", "")
        self.action = item.get("action", "")
        self.target_allocation = Decimal(item.get("target_allocation", "0"))
        self.signal_strength = (
            Decimal(item["signal_strength"]) if "signal_strength" in item else None
        )
        self.reasoning = item.get("reasoning", "")
        self.lifecycle_state = item.get("lifecycle_state", "")
        self.data_source = item.get("data_source", "")

    def __eq__(self, other: object) -> bool:
        """Compare signals for equality (ignoring IDs and timestamps)."""
        if not isinstance(other, SignalRecord):
            return False
        return (
            self.strategy_name == other.strategy_name
            and self.symbol == other.symbol
            and self.action == other.action
            and abs(self.target_allocation - other.target_allocation) < Decimal("0.0001")
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            "signal_id": self.signal_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "action": self.action,
            "target_allocation": str(self.target_allocation),
            "signal_strength": str(self.signal_strength) if self.signal_strength else "",
            "lifecycle_state": self.lifecycle_state,
            "data_source": self.data_source,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Signal(strategy={self.strategy_name}, symbol={self.symbol}, "
            f"action={self.action}, allocation={self.target_allocation})"
        )


def query_signals_by_date(
    table_name: str,
    start_date: datetime,
    end_date: datetime,
    target_time: datetime | None = None,
    window_minutes: int | None = None,
) -> list[SignalRecord]:
    """Query signals from DynamoDB for date range with optional time window.

    Args:
        table_name: DynamoDB table name
        start_date: Start datetime (inclusive)
        end_date: End datetime (exclusive)
        target_time: Optional target time to filter around (UTC)
        window_minutes: Optional window in minutes around target_time (e.g., ±5 mins)

    Returns:
        List of SignalRecord objects

    """
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(table_name)

    signals: list[SignalRecord] = []

    try:
        # Scan with filter for SIGNAL entities in date range
        # Note: For production use with large datasets, consider using GSI queries
        response = table.scan(
            FilterExpression="EntityType = :entity_type AND #ts BETWEEN :start AND :end",
            ExpressionAttributeNames={"#ts": "timestamp"},
            ExpressionAttributeValues={
                ":entity_type": "SIGNAL",
                ":start": start_date.isoformat(),
                ":end": end_date.isoformat(),
            },
        )

        for item in response.get("Items", []):
            signals.append(SignalRecord(item))

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = table.scan(
                FilterExpression="EntityType = :entity_type AND #ts BETWEEN :start AND :end",
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":entity_type": "SIGNAL",
                    ":start": start_date.isoformat(),
                    ":end": end_date.isoformat(),
                },
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            for item in response.get("Items", []):
                signals.append(SignalRecord(item))

    except Exception as e:
        print(f"Error querying {table_name}: {e}")
        return []

    # Apply time window filter if specified
    if target_time and window_minutes:
        filtered_signals = []
        window_delta = timedelta(minutes=window_minutes)
        window_start = target_time - window_delta
        window_end = target_time + window_delta

        for sig in signals:
            sig_time = datetime.fromisoformat(sig.timestamp)
            if window_start <= sig_time <= window_end:
                filtered_signals.append(sig)

        print(
            f"   Filtered to {len(filtered_signals)} signals within ±{window_minutes} min "
            f"of {target_time.strftime('%H:%M UTC')}"
        )
        return filtered_signals

    return signals


def compare_signals(
    dev_signals: list[SignalRecord], prod_signals: list[SignalRecord]
) -> dict[str, Any]:
    """Compare dev and prod signals.

    Args:
        dev_signals: Signals from dev environment
        prod_signals: Signals from prod environment

    Returns:
        Comparison results dictionary

    """
    # Group by strategy + symbol for comparison
    dev_by_key = {}
    for sig in dev_signals:
        key = (sig.strategy_name, sig.symbol)
        if key not in dev_by_key:
            dev_by_key[key] = []
        dev_by_key[key].append(sig)

    prod_by_key = {}
    for sig in prod_signals:
        key = (sig.strategy_name, sig.symbol)
        if key not in prod_by_key:
            prod_by_key[key] = []
        prod_by_key[key].append(sig)

    # Find matches and divergences
    matches = []
    dev_only = []
    prod_only = []
    divergent = []

    all_keys = set(dev_by_key.keys()) | set(prod_by_key.keys())

    for key in all_keys:
        dev_sigs = dev_by_key.get(key, [])
        prod_sigs = prod_by_key.get(key, [])

        if not dev_sigs:
            prod_only.extend(prod_sigs)
        elif not prod_sigs:
            dev_only.extend(dev_sigs)
        else:
            # Compare signal lists (allowing for slight ordering differences)
            if len(dev_sigs) == len(prod_sigs) and all(
                d == p for d, p in zip(dev_sigs, prod_sigs)
            ):
                matches.extend(dev_sigs)
            else:
                divergent.append({"key": key, "dev": dev_sigs, "prod": prod_sigs})

    return {
        "matches": matches,
        "dev_only": dev_only,
        "prod_only": prod_only,
        "divergent": divergent,
        "total_dev": len(dev_signals),
        "total_prod": len(prod_signals),
    }


def print_comparison_summary(results: dict[str, Any]) -> None:
    """Print human-readable comparison summary."""
    print("\n" + "=" * 80)
    print("SIGNAL COMPARISON SUMMARY")
    print("=" * 80)
    print(f"Total Dev Signals:  {results['total_dev']}")
    print(f"Total Prod Signals: {results['total_prod']}")
    print(f"Matching Signals:   {len(results['matches'])}")
    print(f"Dev Only:           {len(results['dev_only'])}")
    print(f"Prod Only:          {len(results['prod_only'])}")
    print(f"Divergent:          {len(results['divergent'])}")

    if results["matches"] and not (
        results["dev_only"] or results["prod_only"] or results["divergent"]
    ):
        print("\n✅ PERFECT PARITY - All signals match!")
    else:
        print("\n⚠️  PARITY ISSUES DETECTED")

    # Show divergent signals in detail
    if results["divergent"]:
        print("\n" + "-" * 80)
        print("DIVERGENT SIGNALS (same strategy+symbol, different actions/allocations):")
        print("-" * 80)
        for div in results["divergent"]:
            key = div["key"]
            print(f"\n{key[0]} / {key[1]}:")
            print(f"  Dev:  {div['dev']}")
            print(f"  Prod: {div['prod']}")

    # Show dev-only signals
    if results["dev_only"]:
        print("\n" + "-" * 80)
        print("DEV-ONLY SIGNALS (not in prod):")
        print("-" * 80)
        for sig in results["dev_only"]:
            print(f"  {sig}")

    # Show prod-only signals
    if results["prod_only"]:
        print("\n" + "-" * 80)
        print("PROD-ONLY SIGNALS (not in dev):")
        print("-" * 80)
        for sig in results["prod_only"]:
            print(f"  {sig}")

    print("\n" + "=" * 80 + "\n")


def export_to_csv(results: dict[str, Any], output_file: str) -> None:
    """Export comparison results to CSV.

    Args:
        results: Comparison results
        output_file: Output CSV filename

    """
    fieldnames = [
        "environment",
        "match_status",
        "signal_id",
        "correlation_id",
        "timestamp",
        "strategy_name",
        "symbol",
        "action",
        "target_allocation",
        "signal_strength",
        "lifecycle_state",
        "data_source",
    ]

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Write matches
        for sig in results["matches"]:
            row = sig.to_dict()
            row["environment"] = "both"
            row["match_status"] = "match"
            writer.writerow(row)

        # Write dev-only
        for sig in results["dev_only"]:
            row = sig.to_dict()
            row["environment"] = "dev"
            row["match_status"] = "dev_only"
            writer.writerow(row)

        # Write prod-only
        for sig in results["prod_only"]:
            row = sig.to_dict()
            row["environment"] = "prod"
            row["match_status"] = "prod_only"
            writer.writerow(row)

        # Write divergent (both versions)
        for div in results["divergent"]:
            for sig in div["dev"]:
                row = sig.to_dict()
                row["environment"] = "dev"
                row["match_status"] = "divergent"
                writer.writerow(row)
            for sig in div["prod"]:
                row = sig.to_dict()
                row["environment"] = "prod"
                row["match_status"] = "divergent"
                writer.writerow(row)

    print(f"📊 Results exported to: {output_file}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compare strategy signals between dev and prod environments"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to compare (YYYY-MM-DD or 'today')",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        help="Number of days to look back from today",
    )
    parser.add_argument(
        "--time",
        type=str,
        help="Target time in UTC (HH:MM, e.g., 19:30 for 7:30 PM UK / 3:30 PM ET)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Time window in minutes around target time (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="signal_comparison.csv",
        help="Output CSV filename (default: signal_comparison.csv)",
    )

    args = parser.parse_args()

    # Determine date range
    if args.date:
        if args.date.lower() == "today":
            target_date = datetime.now(UTC).date()
        else:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        start_date = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
        end_date = start_date + timedelta(days=1)
    elif args.days_back:
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=args.days_back)
    else:
        # Default: today
        target_date = datetime.now(UTC).date()
        start_date = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
        end_date = start_date + timedelta(days=1)

    # Parse target time if specified (3:30 PM ET = 19:30 UTC = 7:30 PM UK)
    target_time = None
    if args.time:
        try:
            hour, minute = map(int, args.time.split(":"))
            target_time = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC).replace(
                hour=hour, minute=minute
            )
        except ValueError:
            print(f"❌ Invalid time format: {args.time}. Use HH:MM (e.g., 19:30)")
            return 1

    print(f"🔍 Comparing signals from {start_date.date()} to {end_date.date()}")
    if target_time:
        print(f"   Time window: ±{args.window} min around {target_time.strftime('%H:%M UTC')}")
        print(f"                (3:30 PM ET / 7:30 PM UK = 19:30 UTC)")
    print(f"   Dev table:  {DEV_TABLE}")
    print(f"   Prod table: {PROD_TABLE}")

    # Query both environments
    print("\n📥 Fetching dev signals...")
    dev_signals = query_signals_by_date(DEV_TABLE, start_date, end_date, target_time, args.window)
    print(f"   Found {len(dev_signals)} signals")

    print("\n📥 Fetching prod signals...")
    prod_signals = query_signals_by_date(PROD_TABLE, start_date, end_date, target_time, args.window)
    print(f"   Found {len(prod_signals)} signals")

    # Compare
    print("\n🔄 Comparing signals...")
    results = compare_signals(dev_signals, prod_signals)

    # Print summary
    print_comparison_summary(results)

    # Export to CSV
    export_to_csv(results, args.output)

    # Return exit code based on parity
    if results["dev_only"] or results["prod_only"] or results["divergent"]:
        return 1  # Parity issues detected
    return 0  # Perfect parity


if __name__ == "__main__":
    sys.exit(main())
