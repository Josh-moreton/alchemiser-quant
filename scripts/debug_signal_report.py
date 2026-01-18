#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Generate a report of signal changes for a given date from the debugging stack.

This script queries the SignalHistoryTable and presents:
- All signal snapshots for the day
- Changes detected between consecutive snapshots
- Summary statistics

Usage:
    python scripts/debug_signal_report.py --date 2026-01-18
    python scripts/debug_signal_report.py  # Defaults to today
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

SIGNAL_HISTORY_TABLE = "alchemiser-debug-signal-history"


def main() -> None:
    """Generate signal change report."""
    parser = argparse.ArgumentParser(description="Generate signal change report")
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().isoformat(),
        help="Date to generate report for (YYYY-MM-DD). Defaults to today.",
    )
    args = parser.parse_args()

    report_date = args.date

    print(f"\n{'='*80}")
    print(f"Signal Change Report for {report_date}")
    print(f"{'='*80}\n")

    try:
        # Query DynamoDB for all snapshots on this date
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(SIGNAL_HISTORY_TABLE)

        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"DATE#{report_date}"),
            ScanIndexForward=True,  # Ascending order (chronological)
        )

        snapshots = response.get("Items", [])

        if not snapshots:
            print(f"❌ No signal snapshots found for {report_date}")
            print(f"\nℹ️  Possible reasons:")
            print(f"   - Debugging stack not deployed")
            print(f"   - Market was closed on this date")
            print(f"   - No signals were generated (check Lambda logs)")
            sys.exit(1)

        print(f"📊 Found {len(snapshots)} signal snapshots\n")

        # Track overall statistics
        total_changes = 0
        snapshots_with_changes = 0

        # Print each snapshot
        for i, snapshot in enumerate(snapshots, 1):
            timestamp = snapshot.get("timestamp", "")
            correlation_id = snapshot.get("correlation_id", "")
            signals_data = snapshot.get("signals_data", {})
            changes = snapshot.get("changes_detected", {})

            # Format time from ISO timestamp
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%I:%M:%S %p ET")
                except Exception:
                    time_str = timestamp

            print(f"┌─ Snapshot {i}: {time_str}")
            print(f"│  Correlation ID: {correlation_id}")
            print(f"│  Signals: {len(signals_data)} tickers")

            # Show top 5 positions by weight
            sorted_signals = sorted(
                signals_data.items(),
                key=lambda x: float(x[1]),
                reverse=True,
            )
            print(f"│  Top positions:")
            for ticker, weight in sorted_signals[:5]:
                print(f"│    {ticker}: {float(weight):.2%}")

            # Show changes
            is_first = changes.get("is_first_snapshot", False)
            has_changes = changes.get("has_changes", False)

            if is_first:
                print(f"│  ✨ First snapshot of the day")
            elif has_changes:
                snapshots_with_changes += 1

                added = changes.get("added_tickers", [])
                removed = changes.get("removed_tickers", [])
                weight_changes = changes.get("weight_changes", [])

                if added:
                    total_changes += len(added)
                    print(f"│  ➕ Added tickers: {', '.join(added)}")

                if removed:
                    total_changes += len(removed)
                    print(f"│  ➖ Removed tickers: {', '.join(removed)}")

                if weight_changes:
                    total_changes += len(weight_changes)
                    print(f"│  ⚖️  Weight changes:")
                    for change in weight_changes[:5]:  # Show top 5 changes
                        ticker = change["ticker"]
                        prev = change["prev_weight"]
                        curr = change["curr_weight"]
                        delta = change["change"]
                        print(f"│      {ticker}: {prev} → {curr} ({delta})")
                    if len(weight_changes) > 5:
                        print(f"│      ... and {len(weight_changes) - 5} more")

            else:
                print(f"│  ✓ No changes from previous snapshot")

            print(f"└{'─'*78}\n")

        # Summary
        print(f"{'='*80}")
        print(f"Summary")
        print(f"{'='*80}")
        print(f"Total snapshots: {len(snapshots)}")
        print(f"Snapshots with changes: {snapshots_with_changes}")
        print(f"Total changes detected: {total_changes}")

        if snapshots_with_changes > 0:
            print(
                f"Average changes per snapshot: {total_changes / snapshots_with_changes:.1f}"
            )

        print()

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
