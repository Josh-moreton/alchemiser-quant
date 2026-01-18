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
import os
import re
import subprocess
import sys
import tempfile
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


def find_sessions_by_date(client: Any, table_name: str, target_date: date) -> list[dict[str, Any]]:
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
                    "total_strategies": int(item.get("total_strategies", {}).get("N", "0")),
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
                    "total_strategies": int(item.get("total_strategies", {}).get("N", "0")),
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


def get_all_partial_signals(client: Any, table_name: str, session_id: str) -> list[dict[str, Any]]:
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
        consolidated_portfolio_str = item.get("consolidated_portfolio", {}).get("S", "{}")

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
# Composer Holdings Parser Functions
# ============================================================================


def parse_composer_holdings(raw_text: str) -> dict[str, Decimal]:
    """Parse Composer.trade 'Simulated Holdings' copy-paste format.

    Parses the raw text copied from Composer.trade's Simulated Holdings table
    and extracts ticker symbols with their allocation percentages.

    Args:
        raw_text: Raw copy-pasted text from Composer.trade

    Returns:
        Dict of ticker -> allocation as Decimal (e.g., {"BSV": Decimal("0.375")})
        Cash positions ("Symphony Cash Remainder") are skipped.

    Example input format:
        Simulated Holdings
        Jan 18, 2025->Jan 16, 2026 | Assuming an initial investment of $10,000
        Current Price	Quantity	Market Value	Current Allocation
        BSV
        Vanguard Short-Term Bond ETF
        $78.73
        90.571	$7,130.67	37.5%
    """
    holdings: dict[str, Decimal] = {}
    lines = raw_text.strip().split("\n")

    # Track the last potential ticker we've seen
    last_ticker: str | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip "Symphony Cash Remainder" (cash position)
        if "Symphony Cash Remainder" in line:
            last_ticker = None
            continue

        # Check if this line contains an allocation percentage
        # Matches patterns like "37.5%" or "62.5%" at the end of the line
        alloc_match = re.search(r"(\d+\.?\d*)\s*%\s*$", line)
        if alloc_match and last_ticker:
            pct = Decimal(alloc_match.group(1))
            # Convert percentage to decimal (37.5% -> 0.375)
            holdings[last_ticker] = pct / Decimal("100")
            last_ticker = None
            continue

        # Check if this line could be a ticker symbol
        # Tickers are typically 1-5 uppercase letters/numbers, standalone
        # Avoid matching prices like "$78.73" or dates
        if re.match(r"^[A-Z][A-Z0-9]{0,4}$", line):
            last_ticker = line
            continue

        # If line looks like a full name (contains spaces, lowercase), reset ticker
        if " " in line or any(c.islower() for c in line):
            # Don't reset if we're in the middle of parsing a holding
            pass

    return holdings


def capture_live_signals(strategy_name: str) -> dict[str, Decimal] | None:
    """Open editor for user to paste Composer holdings, then parse.

    Creates a temporary file, opens it in the user's editor, waits for them
    to paste the Composer.trade holdings data, then parses the result.

    Args:
        strategy_name: Strategy name (used for temp file naming)

    Returns:
        Parsed holdings dict, or None if cancelled or empty
    """
    # Get editor from environment, fall back to nano then vi
    editor = os.environ.get("EDITOR", "nano")
    if not editor:
        editor = "vi"

    # Create temp file with instructions
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"composer_holdings_{strategy_name}.txt"

    instructions = f"""# Paste the Composer.trade "Simulated Holdings" data below this line.
# Save and close the editor when done.
# To cancel, delete all content and save.
#
# Strategy: {strategy_name}
# -------------------------------------------------------------------------

"""
    with open(temp_path, "w") as f:
        f.write(instructions)

    # Open editor
    print(f"\n  Opening {editor} for live signal capture...")
    print(f"  Paste Composer holdings, save, and close the editor.")

    try:
        result = subprocess.run([editor, str(temp_path)], check=True)
    except subprocess.CalledProcessError:
        print("  Editor exited with error")
        return None
    except FileNotFoundError:
        print(f"  Editor '{editor}' not found. Set EDITOR environment variable.")
        return None

    # Read and parse the file
    try:
        with open(temp_path) as f:
            content = f.read()
    except FileNotFoundError:
        print("  Temp file not found")
        return None

    # Clean up temp file
    try:
        temp_path.unlink()
    except OSError:
        pass

    # Remove instruction lines (lines starting with #)
    lines = [line for line in content.split("\n") if not line.strip().startswith("#")]
    cleaned_content = "\n".join(lines).strip()

    if not cleaned_content:
        print("  No content found (cancelled)")
        return None

    # Parse the holdings
    holdings = parse_composer_holdings(cleaned_content)

    if not holdings:
        print("  Could not parse any holdings from the pasted data")
        return None

    # Display parsed results
    print(f"\n  Parsed {len(holdings)} holdings:")
    for ticker, weight in sorted(holdings.items(), key=lambda x: x[1], reverse=True):
        pct = float(weight) * 100
        print(f"    {ticker:<8} {pct:>6.2f}%")

    # Confirm with user
    confirm = input("\n  Is this correct? [Y/n]: ").strip().lower()
    if confirm in ["n", "no"]:
        print("  Discarded live signals")
        return None

    return holdings


def display_signal_comparison(
    our_signals: dict[str, Decimal],
    live_signals: dict[str, Decimal] | None,
) -> None:
    """Display side-by-side comparison of our signals vs live Composer signals.

    Args:
        our_signals: Our computed allocations (ticker -> decimal weight)
        live_signals: Live signals from Composer (ticker -> decimal weight), or None
    """
    if live_signals is None:
        return

    # Collect all symbols from both sources
    all_symbols = set(our_signals.keys()) | set(live_signals.keys())

    print("\n" + "━" * 55)
    print("  Signal Comparison")
    print("━" * 55)
    print(f"  {'Symbol':<8}  {'Ours':>10}  {'Live':>10}  {'Status':<12}")
    print("  " + "-" * 50)

    matches = 0
    differences = 0

    for symbol in sorted(all_symbols):
        ours = our_signals.get(symbol)
        live = live_signals.get(symbol)

        ours_str = f"{float(ours) * 100:.2f}%" if ours else "-"
        live_str = f"{float(live) * 100:.2f}%" if live else "-"

        # Determine status
        if ours is None:
            status = "✗ Missing (ours)"
            differences += 1
        elif live is None:
            status = "✗ Extra (ours)"
            differences += 1
        elif abs(float(ours) - float(live)) < 0.001:  # 0.1% tolerance
            status = "✓ Match"
            matches += 1
        else:
            diff = (float(ours) - float(live)) * 100
            status = f"✗ Diff ({diff:+.1f}%)"
            differences += 1

        print(f"  {symbol:<8}  {ours_str:>10}  {live_str:>10}  {status:<12}")

    print("  " + "-" * 50)
    print(f"  Matches: {matches}  |  Differences: {differences}")
    print("━" * 55)


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
        record: Validation record dict (should include our_signals and live_signals as JSON)
    """
    fieldnames = [
        "validation_date",
        "session_id",
        "strategy_name",
        "dsl_file",
        "matches",
        "notes",
        "our_signals",
        "live_signals",
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
            target_allocations.items(), key=lambda x: Decimal(str(x[1])), reverse=True
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


def prompt_validation(
    strategy_name: str,
    our_signals: dict[str, Decimal],
) -> tuple[str, str, dict[str, Decimal] | None]:
    """Interactive prompt for validation result.

    Args:
        strategy_name: Name of the strategy being validated
        our_signals: Our computed allocations for comparison display

    Returns:
        Tuple of (matches_str, notes_str, live_signals_dict_or_none)
        Raises KeyboardInterrupt if user quits
    """
    live_signals: dict[str, Decimal] | None = None

    while True:
        response = (
            input("Does the signal match? (y/n/s=skip/l=capture live/q=quit): ").strip().lower()
        )

        if response == "q":
            raise KeyboardInterrupt("User quit validation")

        if response == "l":
            # Capture live signals from Composer
            live_signals = capture_live_signals(strategy_name)
            if live_signals:
                # Display comparison
                display_signal_comparison(our_signals, live_signals)
            # Return to prompt for final answer
            continue

        if response in ["y", "n", "s"]:
            matches_map = {"y": "yes", "n": "no", "s": "skip"}
            matches = matches_map[response]

            notes = input("Notes (optional): ").strip()

            return matches, notes, live_signals

        print("  Invalid input. Please enter y, n, s, l, or q.")


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
            choice = input(
                "\nSelect session [1-{}] or enter session ID: ".format(len(sessions))
            ).strip()

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
        choices=["dev", "staging", "prod"],
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
    parser.add_argument(
        "--capture-live",
        action="store_true",
        help="Always prompt to capture live signals from Composer for each strategy",
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
            strategy_name = dsl_file.replace(".clj", "")

            # Skip if already validated
            if dsl_file in validated_strategies:
                print(f"\n✓ Skipping {dsl_file} (already validated)")
                continue

            # Find strategy metadata
            strategy = find_strategy_by_filename(ledger, dsl_file)

            # Extract our signals (un-scaled to match Composer's 100% view)
            raw_allocations = signal["consolidated_portfolio"].get("target_allocations", {})
            allocation_weight = signal["allocation"]
            our_signals: dict[str, Decimal] = {}
            for symbol, weight in raw_allocations.items():
                # Un-scale: divide by strategy allocation to get original 100% portfolio
                original_weight = Decimal(str(weight)) / allocation_weight
                our_signals[symbol] = original_weight

            # Display signal
            display_signal(signal, strategy, i, len(signals))

            # Optionally open browser
            if not args.no_browser and strategy and strategy.get("source_url"):
                open_prompt = input("Open Composer URL? [Y/n]: ").strip().lower()
                if open_prompt in ["", "y", "yes"]:
                    open_url_in_browser(strategy["source_url"])

            # If --capture-live flag, auto-invoke live signal capture
            live_signals: dict[str, Decimal] | None = None
            if args.capture_live:
                print("\n📥 Capture live signals (--capture-live enabled)")
                live_signals = capture_live_signals(strategy_name)
                if live_signals:
                    display_signal_comparison(our_signals, live_signals)

            # Prompt for validation
            matches, notes, captured_live = prompt_validation(strategy_name, our_signals)

            # Use live signals from prompt if not already captured
            if captured_live and not live_signals:
                live_signals = captured_live

            # Serialize signals to JSON for CSV storage
            def signals_to_json(signals_dict: dict[str, Decimal] | None) -> str:
                if not signals_dict:
                    return ""
                # Convert Decimal to float for JSON serialization
                return json.dumps({k: float(v) for k, v in signals_dict.items()}, sort_keys=True)

            # Record validation
            record = {
                "validation_date": validation_date.isoformat(),
                "session_id": session_id,
                "strategy_name": strategy_name,
                "dsl_file": dsl_file,
                "matches": matches,
                "notes": notes,
                "our_signals": signals_to_json(our_signals),
                "live_signals": signals_to_json(live_signals),
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
