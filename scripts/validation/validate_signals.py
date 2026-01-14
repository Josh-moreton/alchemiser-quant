#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Daily validation tool for strategy signals against Composer.trade.

Usage:
    python scripts/validate_signals.py [--stage dev|prod] [--date YYYY-MM-DD]
    python scripts/validate_signals.py --session-id workflow-abc123
    python scripts/validate_signals.py --stage dev --no-browser

Examples:
    # Validate today's dev run
    python scripts/validate_signals.py

    # Validate specific date
    python scripts/validate_signals.py --date 2026-01-02

    # Validate specific session
    python scripts/validate_signals.py --session-id workflow-abc123

    # Don't auto-open browser
    python scripts/validate_signals.py --no-browser
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import webbrowser
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import boto3
import yaml
from botocore.exceptions import ClientError

# Project root for paths (go up two levels: validation/ -> scripts/ -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LEDGER_PATH = (
    PROJECT_ROOT
    / "layers"
    / "shared"
    / "the_alchemiser"
    / "shared"
    / "strategies"
    / "strategy_ledger.yaml"
)
VALIDATION_DIR = PROJECT_ROOT / "validation_results"


# ============================================================================
# DynamoDB Functions
# ============================================================================


def get_dynamodb_client(region: str = "us-east-1") -> Any:
    """Get DynamoDB client."""
    return boto3.client("dynamodb", region_name=region)


def find_sessions_by_date(
    client: Any, table_name: str, target_date: date
) -> list[dict[str, Any]]:
    """Find all completed sessions for a given date.

    Args:
        client: DynamoDB client
        table_name: DynamoDB table name
        target_date: Target date to search for

    Returns:
        List of session metadata dicts, sorted by created_at descending
    """
    sessions: list[dict[str, Any]] = []

    # Scan with pagination
    paginator = client.get_paginator("scan")
    page_iterator = paginator.paginate(
        TableName=table_name,
        FilterExpression="SK = :metadata AND #status = :completed AND begins_with(created_at, :date)",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":metadata": {"S": "METADATA"},
            ":completed": {"S": "COMPLETED"},
            ":date": {"S": target_date.isoformat()},
        },
    )

    for page in page_iterator:
        for item in page.get("Items", []):
            sessions.append(
                {
                    "session_id": item.get("session_id", {}).get("S", ""),
                    "correlation_id": item.get("correlation_id", {}).get("S", ""),
                    "created_at": item.get("created_at", {}).get("S", ""),
                    "status": item.get("status", {}).get("S", ""),
                    "total_strategies": int(
                        item.get("total_strategies", {}).get("N", "0")
                    ),
                }
            )

    # Sort by created_at descending (most recent first)
    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return sessions


def get_recent_sessions(client: Any, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
    """Get recent completed sessions efficiently.

    Uses pagination with early termination to quickly find recent sessions.

    Args:
        client: DynamoDB client
        table_name: DynamoDB table name
        limit: Maximum number of sessions to return

    Returns:
        List of recent session metadata dicts
    """
    sessions: list[dict[str, Any]] = []

    # Use pagination but stop early once we have enough sessions
    # Each page scans up to 1MB of data
    paginator = client.get_paginator("scan")
    page_iterator = paginator.paginate(
        TableName=table_name,
        FilterExpression="SK = :metadata AND #status = :completed",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":metadata": {"S": "METADATA"},
            ":completed": {"S": "COMPLETED"},
        },
        PaginationConfig={"PageSize": 500},  # Items per page
    )

    # Collect sessions from pages, stop when we have enough recent ones
    for page in page_iterator:
        for item in page.get("Items", []):
            sessions.append(
                {
                    "session_id": item.get("session_id", {}).get("S", ""),
                    "correlation_id": item.get("correlation_id", {}).get("S", ""),
                    "created_at": item.get("created_at", {}).get("S", ""),
                    "status": item.get("status", {}).get("S", ""),
                    "total_strategies": int(
                        item.get("total_strategies", {}).get("N", "0")
                    ),
                }
            )
        # Early termination: if we have more than limit * 3 sessions,
        # we likely have the most recent ones in there
        if len(sessions) >= limit * 3:
            break

    # Sort by created_at descending and return top N
    sessions.sort(key=lambda x: x["created_at"], reverse=True)
    return sessions[:limit]


def get_latest_session(client: Any, table_name: str) -> dict[str, Any] | None:
    """Get the most recent completed session.

    This is an optimized function that quickly finds the latest session
    without scanning the entire table.

    Args:
        client: DynamoDB client
        table_name: DynamoDB table name

    Returns:
        Latest session metadata dict or None if no sessions found
    """
    sessions = get_recent_sessions(client, table_name, limit=1)
    return sessions[0] if sessions else None


def get_all_partial_signals(
    client: Any, table_name: str, session_id: str
) -> list[dict[str, Any]]:
    """Query all partial signals for a session.

    Args:
        client: DynamoDB client
        table_name: DynamoDB table name
        session_id: Session ID to query

    Returns:
        List of partial signal dicts
    """
    response = client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {"S": f"SESSION#{session_id}"},
            ":sk_prefix": {"S": "STRATEGY#"},
        },
    )

    signals = []
    for item in response.get("Items", []):
        # Parse JSON fields
        signals_data_str = item.get("signals_data", {}).get("S", "{}")
        consolidated_portfolio_str = item.get("consolidated_portfolio", {}).get(
            "S", "{}"
        )

        signals.append(
            {
                "dsl_file": item.get("dsl_file", {}).get("S", ""),
                "allocation": Decimal(item.get("allocation", {}).get("N", "0")),
                "signals_data": json.loads(signals_data_str),
                "consolidated_portfolio": json.loads(consolidated_portfolio_str),
                "signal_count": int(item.get("signal_count", {}).get("N", "0")),
                "completed_at": item.get("completed_at", {}).get("S", ""),
            }
        )

    # Sort by dsl_file for consistent ordering
    signals.sort(key=lambda x: x["dsl_file"])
    return signals


# ============================================================================
# Strategy Ledger Functions
# ============================================================================


def load_strategy_ledger(ledger_path: Path) -> dict[str, dict[str, Any]]:
    """Load strategy ledger from YAML file.

    Args:
        ledger_path: Path to strategy ledger YAML file

    Returns:
        Dict keyed by strategy_name
    """
    with open(ledger_path) as f:
        return yaml.safe_load(f)


def find_strategy_by_filename(
    ledger: dict[str, dict[str, Any]], dsl_file: str
) -> dict[str, Any] | None:
    """Find strategy metadata by DSL filename.

    Args:
        ledger: Strategy ledger dict
        dsl_file: DSL filename (e.g., "nuclear_feaver.clj")

    Returns:
        Strategy metadata dict or None if not found
    """
    for strategy_name, strategy_info in ledger.items():
        if strategy_info.get("filename") == dsl_file:
            return strategy_info
    return None


# ============================================================================
# CSV Persistence Functions
# ============================================================================


def get_csv_path(validation_date: date) -> Path:
    """Get CSV path for a validation date.

    Args:
        validation_date: Date of validation

    Returns:
        Path to CSV file
    """
    filename = f"signal_validation_{validation_date.isoformat()}.csv"
    return VALIDATION_DIR / filename


def load_validated_strategies(csv_path: Path) -> set[str]:
    """Load already-validated dsl_files from CSV.

    Args:
        csv_path: Path to CSV file

    Returns:
        Set of dsl_file values already validated
    """
    if not csv_path.exists():
        return set()

    validated = set()
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            validated.add(row["dsl_file"])

    return validated


def append_validation(csv_path: Path, record: dict[str, Any]) -> None:
    """Append validation record to CSV.

    Args:
        csv_path: Path to CSV file
        record: Validation record dict
    """
    fieldnames = [
        "validation_date",
        "session_id",
        "strategy_name",
        "dsl_file",
        "matches",
        "notes",
        "validated_at",
    ]

    # Create file with header if it doesn't exist
    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


# ============================================================================
# Interactive UI Functions
# ============================================================================


def display_signal(
    signal: dict[str, Any],
    strategy: dict[str, Any] | None,
    index: int,
    total: int,
) -> None:
    """Display signal data for user review.

    Args:
        signal: Partial signal dict
        strategy: Strategy metadata dict (or None if not found)
        index: Current strategy index (1-based)
        total: Total number of strategies
    """
    print("\n" + "━" * 80)
    print(f"\nStrategy {index} of {total}: {signal['dsl_file'].replace('.clj', '')}")
    print()

    if strategy:
        print(f"Composer URL: {strategy.get('source_url', 'N/A')}")
    else:
        print("⚠️  Strategy not found in ledger - Composer URL: (unknown)")

    # Extract target allocations from consolidated_portfolio
    target_allocations = signal["consolidated_portfolio"].get("target_allocations", {})

    if target_allocations:
        print(f"\nTarget Allocations ({signal['signal_count']} positions):")

        # Un-scale allocations to show as standalone 100% portfolio (to match Composer)
        # The allocations are scaled by the strategy weight, so divide to get original
        allocation_weight = signal["allocation"]

        # Sort by allocation descending
        sorted_allocations = sorted(
            target_allocations.items(),
            key=lambda x: Decimal(str(x[1])),
            reverse=True
        )

        for symbol, weight in sorted_allocations:
            # Un-scale: divide by strategy allocation to get original 100% portfolio
            original_weight = Decimal(str(weight)) / allocation_weight
            weight_pct = float(original_weight) * 100
            print(f"  {symbol:<8} {weight_pct:>6.2f}%")
    else:
        print("\n⚠️  No target allocations found")

    print()


def open_url_in_browser(url: str) -> None:
    """Open URL in default browser.

    Args:
        url: URL to open
    """
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"  ⚠️  Could not open browser: {e}")


def prompt_validation() -> tuple[str, str]:
    """Interactive prompt for validation result.

    Returns:
        Tuple of (matches_str, notes_str)
        Raises KeyboardInterrupt if user quits
    """
    while True:
        response = input("Does the signal match? (y/n/s=skip/q=quit): ").strip().lower()

        if response == "q":
            raise KeyboardInterrupt("User quit validation")

        if response in ["y", "n", "s"]:
            matches_map = {"y": "yes", "n": "no", "s": "skip"}
            matches = matches_map[response]

            notes = input("Notes (optional): ").strip()

            return matches, notes

        print("  Invalid input. Please enter y, n, s, or q.")


def select_session(sessions: list[dict[str, Any]]) -> str:
    """Interactive session selection.

    Args:
        sessions: List of session metadata dicts

    Returns:
        Selected session_id
    """
    if not sessions:
        print("❌ No sessions available")
        sys.exit(1)

    if len(sessions) == 1:
        return sessions[0]["session_id"]

    print("\nMultiple sessions found:")
    for i, session in enumerate(sessions, 1):
        created_at = session["created_at"]
        session_id = session["session_id"]
        print(f"  {i}. {created_at} - {session_id}")

    while True:
        try:
            choice = input("\nSelect session [1-{}] or enter session ID: ".format(len(sessions))).strip()

            # Try as index first
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(sessions):
                    return sessions[index]["session_id"]

            # Try as session ID
            if choice.startswith("workflow-"):
                return choice

            print(f"  Invalid selection. Please enter 1-{len(sessions)} or a valid session ID.")

        except KeyboardInterrupt:
            print("\n\nValidation cancelled")
            sys.exit(0)


# ============================================================================
# Main Workflow
# ============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate strategy signals against Composer.trade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        choices=["dev", "prod"],
        default="dev",
        help="Environment stage (default: dev)",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Validation date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Specific session ID to validate (skips date search)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't auto-open URLs in browser",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Ignore previous validations and start fresh (creates new CSV)",
    )

    args = parser.parse_args()

    # Parse validation date
    if args.date:
        try:
            validation_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"❌ Invalid date format: {args.date}")
            print("Please use YYYY-MM-DD format")
            sys.exit(1)
    else:
        validation_date = date.today()

    # Print header
    print("\n" + "=" * 80)
    print("Signal Validation Tool")
    print("=" * 80)
    print(f"\nStage: {args.stage}")
    print(f"Validation date: {validation_date.isoformat()}")

    # Initialize DynamoDB client
    table_name = f"alchemiser-{args.stage}-aggregation-sessions"
    try:
        client = get_dynamodb_client()
    except Exception as e:
        print(f"\n❌ Error initializing DynamoDB client: {e}")
        print("\nPlease ensure:")
        print("1. AWS credentials are configured")
        print("2. You have access to the table")
        sys.exit(1)

    # Find or select session
    session_id = None
    if args.session_id:
        session_id = args.session_id
        print(f"\nUsing session: {session_id}")
    else:
        print("\nFinding latest session...")
        try:
            # Default: just get the latest session (fast)
            latest = get_latest_session(client, table_name)

            if latest:
                session_id = latest["session_id"]
                session_date = latest["created_at"].split("T")[0]
                session_time = latest["created_at"].split("T")[1].split(".")[0]
                validation_date = date.fromisoformat(session_date)
                print(f"\n✅ Found latest session: {session_date} @ {session_time} UTC")
                print(f"   Session ID: {session_id}")
                print(f"   Strategies: {latest['total_strategies']}")
            else:
                print("\n❌ No completed sessions found")
                print("\nRecent sessions:")
                recent = get_recent_sessions(client, table_name, limit=5)
                for i, session in enumerate(recent, 1):
                    created_date = session["created_at"].split("T")[0]
                    print(
                        f"  {i}. {created_date} - {session['created_at']} - {session['session_id']}"
                    )
                if recent:
                    session_id = select_session(recent)
                else:
                    print("\nNo sessions available.")
                    sys.exit(1)

        except ClientError as e:
            print(f"\n❌ DynamoDB error: {e}")
            print(f"\nPlease check access to table: {table_name}")
            sys.exit(1)

    if not session_id:
        print("\n❌ No session selected")
        sys.exit(1)

    # Load strategy ledger
    print("\nLoading strategy ledger...")
    try:
        ledger = load_strategy_ledger(LEDGER_PATH)
        print(f"Loaded {len(ledger)} strategies from ledger")
    except Exception as e:
        print(f"\n❌ Error loading strategy ledger: {e}")
        sys.exit(1)

    # Get all partial signals
    print(f"\nLoading signals for session {session_id}...")
    try:
        signals = get_all_partial_signals(client, table_name, session_id)
        print(f"Found {len(signals)} partial signals")
    except ClientError as e:
        print(f"\n❌ Error querying signals: {e}")
        sys.exit(1)

    if not signals:
        print("\n❌ No signals found for this session")
        sys.exit(1)

    # Load existing validations (for resume capability)
    csv_path = get_csv_path(validation_date)

    if args.fresh:
        # Delete existing CSV if --fresh flag is set
        if csv_path.exists():
            csv_path.unlink()
            print("\n🔄 Fresh validation requested - cleared previous results")
        validated_strategies: set[str] = set()
    else:
        validated_strategies = load_validated_strategies(csv_path)

    if validated_strategies:
        print(f"\nResuming validation ({len(validated_strategies)} already completed)")
        print("  (Use --fresh to start over)")
    else:
        print("\nStarting fresh validation")

    # Validate each signal
    stats = {"validated_yes": 0, "validated_no": 0, "skipped": 0}

    try:
        for i, signal in enumerate(signals, 1):
            dsl_file = signal["dsl_file"]

            # Skip if already validated
            if dsl_file in validated_strategies:
                print(f"\n✓ Skipping {dsl_file} (already validated)")
                continue

            # Find strategy metadata
            strategy = find_strategy_by_filename(ledger, dsl_file)

            # Display signal
            display_signal(signal, strategy, i, len(signals))

            # Optionally open browser
            if not args.no_browser and strategy and strategy.get("source_url"):
                open_prompt = input("Open Composer URL? [Y/n]: ").strip().lower()
                if open_prompt in ["", "y", "yes"]:
                    open_url_in_browser(strategy["source_url"])

            # Prompt for validation
            matches, notes = prompt_validation()

            # Record validation
            record = {
                "validation_date": validation_date.isoformat(),
                "session_id": session_id,
                "strategy_name": dsl_file.replace(".clj", ""),
                "dsl_file": dsl_file,
                "matches": matches,
                "notes": notes,
                "validated_at": datetime.now(UTC).isoformat(),
            }

            append_validation(csv_path, record)

            # Update stats
            if matches == "yes":
                stats["validated_yes"] += 1
                print(f"\n✓ Validated {dsl_file}")
            elif matches == "no":
                stats["validated_no"] += 1
                print(f"\n✗ Validated {dsl_file} (mismatch)")
            else:
                stats["skipped"] += 1
                print(f"\n⊘ Skipped {dsl_file}")

    except KeyboardInterrupt:
        print("\n\n✋ Validation interrupted")
        print(f"\nProgress saved to: {csv_path}")
        print("Run again to resume from where you left off")
        sys.exit(0)

    # Print summary
    print("\n" + "=" * 80)
    print("Validation Complete!")
    print("=" * 80)
    print(f"\nTotal strategies: {len(signals)}")
    print(f"Validated (match): {stats['validated_yes']}")
    print(f"Validated (no match): {stats['validated_no']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"\nResults saved to: {csv_path}")


if __name__ == "__main__":
    main()
