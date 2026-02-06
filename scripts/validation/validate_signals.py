#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Daily signal validation using shifted comparison (T-1).

Workflow:
1. Load today's our_signals from locally-generated CSV (default) or DynamoDB
2. Capture today's live_signals from Composer for all strategies
3. Compare today's our_signals against YESTERDAY's live_signals
4. Report match rate

This handles the lookahead bias in Composer backtests where:
- Today's live_signals (Composer backtest) = Tomorrow's our_signals

Signal sources:
- Default: Local CSV from validation_results/local_signals/ (via generate_daily_signals.py)
- Legacy:  DynamoDB aggregation sessions (use --dynamo flag)

Usage:
    make validate-signals                    # Validate using local signals (dev)
    make validate-signals stage=prod         # Validate prod signals
    make validate-signals fresh=1            # Start fresh (ignore previous captures)
    make validate-signals dynamo=1           # Use DynamoDB instead of local CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
import webbrowser
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
from the_alchemiser.shared.indicators.partial_bar_config import get_all_indicator_configs

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
LOCAL_SIGNALS_DIR = VALIDATION_DIR / "local_signals"


# ============================================================================
# DynamoDB Functions (lazy-loaded, only needed with --dynamo)
# ============================================================================


def _import_boto3() -> tuple[Any, Any]:
    """Lazy-import boto3 and botocore (only needed for --dynamo mode).

    Returns:
        Tuple of (boto3 module, ClientError class).

    Raises:
        SystemExit: If boto3 is not installed.

    """
    try:
        import boto3 as _boto3
        from botocore.exceptions import ClientError as _ClientError

        return _boto3, _ClientError
    except ImportError:
        print("boto3 is required for --dynamo mode. Install with: poetry add boto3")
        sys.exit(1)


def get_dynamodb_client(region: str = "us-east-1") -> Any:
    """Get DynamoDB client."""
    boto3_mod, _ = _import_boto3()
    return boto3_mod.client("dynamodb", region_name=region)


def get_latest_session(client: Any, table_name: str) -> dict[str, Any] | None:
    """Get the most recent completed session."""
    sessions_map: dict[str, dict[str, Any]] = {}
    items_scanned = 0

    paginator = client.get_paginator("scan")
    page_iterator = paginator.paginate(
        TableName=table_name,
        FilterExpression="begins_with(SK, :strategy_prefix)",
        ExpressionAttributeValues={":strategy_prefix": {"S": "STRATEGY#"}},
        PaginationConfig={"PageSize": 100},
    )

    for page in page_iterator:
        for item in page.get("Items", []):
            items_scanned += 1
            pk = item.get("PK", {}).get("S", "")
            if pk.startswith("SESSION#"):
                session_id = pk.replace("SESSION#", "")
                completed_at = item.get("completed_at", {}).get("S", "")

                if session_id not in sessions_map:
                    sessions_map[session_id] = {
                        "session_id": session_id,
                        "created_at": completed_at,
                        "total_strategies": 1,
                    }
                else:
                    sessions_map[session_id]["total_strategies"] += 1
                    if completed_at > sessions_map[session_id]["created_at"]:
                        sessions_map[session_id]["created_at"] = completed_at

            if len(sessions_map) >= 3 and items_scanned > 2000:
                break
        if len(sessions_map) >= 3 and items_scanned > 2000:
            break

    if not sessions_map:
        return None

    sessions = sorted(sessions_map.values(), key=lambda x: x["created_at"], reverse=True)
    return sessions[0]


def get_all_partial_signals(client: Any, table_name: str, session_id: str) -> list[dict[str, Any]]:
    """Query all partial signals for a session."""
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
        signals.append(
            {
                "dsl_file": item.get("dsl_file", {}).get("S", ""),
                "allocation": Decimal(item.get("allocation", {}).get("N", "0")),
                "consolidated_portfolio": json.loads(
                    item.get("consolidated_portfolio", {}).get("S", "{}")
                ),
                "signal_count": int(item.get("signal_count", {}).get("N", "0")),
            }
        )

    signals.sort(key=lambda x: x["dsl_file"])
    return signals


# ============================================================================
# Local Signal Loading
# ============================================================================


def load_local_signals(
    validation_date: date,
    stage: str,
) -> list[dict[str, Any]] | None:
    """Load our_signals from locally-generated CSV.

    Reads the CSV produced by generate_daily_signals.py for the given date
    and stage. Returns signal dicts compatible with the capture flow.

    Args:
        validation_date: Date to load signals for.
        stage: Environment stage ('dev' or 'prod').

    Returns:
        List of signal dicts with keys: dsl_file, our_signals (as dict).
        Returns None if no local signals file exists for this date.

    """
    csv_path = LOCAL_SIGNALS_DIR / f"{validation_date.isoformat()}_{stage}.csv"
    if not csv_path.exists():
        return None

    signals: list[dict[str, Any]] = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            dsl_file = row.get("dsl_file", "")
            signals_json = row.get("our_signals", "")
            if not dsl_file or not signals_json:
                continue

            try:
                parsed = json.loads(signals_json)
                our_signals = {k: Decimal(str(v)) for k, v in parsed.items()}
            except (json.JSONDecodeError, ValueError):
                continue

            signals.append(
                {
                    "dsl_file": dsl_file,
                    "our_signals": our_signals,
                }
            )

    signals.sort(key=lambda x: x["dsl_file"])
    return signals if signals else None


# ============================================================================
# Strategy Ledger
# ============================================================================


def load_strategy_ledger(ledger_path: Path) -> dict[str, dict[str, Any]]:
    """Load strategy ledger from YAML file."""
    with open(ledger_path) as f:
        return yaml.safe_load(f)


def find_strategy_by_filename(
    ledger: dict[str, dict[str, Any]], dsl_file: str
) -> dict[str, Any] | None:
    """Find strategy metadata by DSL filename.

    Handles both full paths (e.g., 'ftlt/holy_grail.clj') and basenames ('holy_grail.clj').
    """
    # Extract basename for nested folder support
    basename = Path(dsl_file).name

    for strategy_info in ledger.values():
        ledger_filename = strategy_info.get("filename", "")
        # Match either full path or basename
        if ledger_filename == dsl_file or ledger_filename == basename:
            return strategy_info
    return None


# ============================================================================
# Composer Holdings Parser
# ============================================================================


def parse_composer_holdings(raw_text: str) -> dict[str, Decimal]:
    """Parse Composer.trade 'Simulated Holdings' copy-paste format."""
    holdings: dict[str, Decimal] = {}
    lines = raw_text.strip().split("\n")
    last_ticker: str | None = None

    for line in lines:
        line = line.strip()
        if not line or "Symphony Cash Remainder" in line:
            last_ticker = None
            continue

        alloc_match = re.search(r"(\d+\.?\d*)\s*%\s*$", line)
        if alloc_match and last_ticker:
            holdings[last_ticker] = Decimal(alloc_match.group(1)) / Decimal("100")
            last_ticker = None
            continue

        if re.match(r"^[A-Z][A-Z0-9]{0,4}$", line):
            last_ticker = line

    return holdings


def capture_live_signals(strategy_name: str) -> dict[str, Decimal] | None:
    """Capture Composer holdings via paste + Ctrl+D."""
    # Sanitize strategy name for temp file (replace / with _)
    safe_name = strategy_name.replace("/", "_")
    temp_path = Path(tempfile.gettempdir()) / f"composer_{safe_name}.txt"

    print("\n  Paste Composer holdings, then press Enter + Ctrl+D:")

    try:
        with open(temp_path, "w") as f:
            subprocess.run(["cat"], stdout=f, check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        print("  Cancelled")
        return None

    try:
        content = temp_path.read_text()
        temp_path.unlink()
    except (FileNotFoundError, OSError):
        return None

    if not content.strip():
        print("  Empty (cancelled)")
        return None

    holdings = parse_composer_holdings(content)
    if not holdings:
        print("  Could not parse holdings")
        return None

    print(f"\n  Parsed {len(holdings)} holdings:")
    for ticker, weight in sorted(holdings.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ticker:<8} {float(weight) * 100:>6.2f}%")

    return holdings


# ============================================================================
# CSV Functions
# ============================================================================


def get_csv_path(validation_date: date, stage: str) -> Path:
    """Get CSV path (creates unique filename if exists)."""
    base = VALIDATION_DIR / f"signal_validation_{validation_date.isoformat()}_{stage}.csv"
    if not base.exists():
        return base

    counter = 1
    while True:
        path = (
            VALIDATION_DIR
            / f"signal_validation_{validation_date.isoformat()}_{stage}_{counter}.csv"
        )
        if not path.exists():
            return path
        counter += 1


def find_previous_csv(current_date: date, stage: str, max_lookback: int = 5) -> Path | None:
    """Find the most recent previous validation CSV."""
    for days_back in range(1, max_lookback + 1):
        check_date = current_date - timedelta(days=days_back)

        # Check base filename
        base = VALIDATION_DIR / f"signal_validation_{check_date.isoformat()}_{stage}.csv"
        if base.exists():
            return base

        # Check numbered versions
        counter = 1
        latest = None
        while True:
            path = (
                VALIDATION_DIR / f"signal_validation_{check_date.isoformat()}_{stage}_{counter}.csv"
            )
            if path.exists():
                latest = path
                counter += 1
            else:
                break
        if latest:
            return latest

    return None


def load_live_signals_from_csv(csv_path: Path) -> dict[str, dict[str, Decimal]]:
    """Load live_signals from a validation CSV."""
    result: dict[str, dict[str, Decimal]] = {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            name = row.get("strategy_name", "")
            live_json = row.get("live_signals", "")
            if name and live_json:
                try:
                    signals = json.loads(live_json)
                    result[name] = {k: Decimal(str(v)) for k, v in signals.items()}
                except (json.JSONDecodeError, ValueError):
                    pass
    return result


def load_captured_strategies(csv_path: Path) -> set[str]:
    """Load already-captured dsl_files from CSV."""
    if not csv_path.exists():
        return set()

    captured = set()
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            captured.add(row["dsl_file"])
    return captured


def append_record(csv_path: Path, record: dict[str, Any]) -> None:
    """Append record to CSV."""
    fieldnames = [
        "validation_date",
        "session_id",
        "strategy_name",
        "dsl_file",
        "our_signals",
        "live_signals",
        "partial_bar_config",
        "captured_at",
    ]

    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)


# ============================================================================
# Comparison Report
# ============================================================================

MASTER_REPORT_PATH = VALIDATION_DIR / "validation_master_report.csv"


def run_comparison_report(
    today_our_signals: dict[str, dict[str, Decimal]],
    previous_live_signals: dict[str, dict[str, Decimal]],
    previous_date: str,
    validation_date: date,
    stage: str,
) -> None:
    """Compare today's our_signals vs yesterday's live_signals and save to master report."""
    print("\n" + "=" * 80)
    print("SHIFTED VALIDATION REPORT")
    print(f"Comparing today's our_signals vs {previous_date}'s live_signals")
    print("=" * 80)

    matches = mismatches = skipped = 0
    all_strategies = sorted(set(today_our_signals.keys()) | set(previous_live_signals.keys()))
    report_rows: list[dict[str, Any]] = []

    print(f"\n{'Strategy':<25} {'Status':<15} {'Details'}")
    print("-" * 70)

    for name in all_strategies:
        ours = today_our_signals.get(name)
        prev = previous_live_signals.get(name)

        if ours is None:
            print(f"{name:<25} {'SKIP':<15} No our_signals today")
            skipped += 1
            continue

        if prev is None:
            print(f"{name:<25} {'SKIP':<15} No live_signals from {previous_date}")
            skipped += 1
            continue

        all_symbols = set(ours.keys()) | set(prev.keys())
        is_match = True
        diffs = []
        symbol_details = []

        for sym in sorted(all_symbols):
            o, p = ours.get(sym), prev.get(sym)
            o_pct = float(o) * 100 if o else 0
            p_pct = float(p) * 100 if p else 0

            if o is None:
                is_match = False
                diffs.append(f"{sym}: missing")
                symbol_details.append(f"{sym}:0%vs{p_pct:.1f}%")
            elif p is None:
                is_match = False
                diffs.append(f"{sym}: extra")
                symbol_details.append(f"{sym}:{o_pct:.1f}%vs0%")
            elif abs(float(o) - float(p)) >= 0.05:
                is_match = False
                diffs.append(f"{sym}: {(float(o) - float(p)) * 100:+.1f}%")
                symbol_details.append(f"{sym}:{o_pct:.1f}%vs{p_pct:.1f}%")
            else:
                symbol_details.append(f"{sym}:{o_pct:.1f}%")

        status = "MATCH" if is_match else "MISMATCH"
        if is_match:
            matches += 1
            print(f"{name:<25} {'✅ MATCH':<15}")
        else:
            mismatches += 1
            details = ", ".join(diffs[:3])
            if len(diffs) > 3:
                details += f" (+{len(diffs) - 3} more)"
            print(f"{name:<25} {'❌ MISMATCH':<15} {details}")

        # Prepare row for master report
        report_rows.append(
            {
                "validation_date": validation_date.isoformat(),
                "comparison_date": previous_date,
                "stage": stage,
                "strategy_name": name,
                "status": status,
                "our_signals": json.dumps({k: float(v) for k, v in ours.items()}, sort_keys=True),
                "live_signals": json.dumps({k: float(v) for k, v in prev.items()}, sort_keys=True),
                "symbol_details": "; ".join(symbol_details),
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )

    total = matches + mismatches
    rate = (matches / total * 100) if total > 0 else 0

    print("-" * 70)
    print(f"\nSUMMARY: {matches}/{total} matched ({rate:.1f}%)")
    if skipped:
        print(f"         {skipped} skipped (missing data)")
    print("=" * 80)

    # Write to master report
    _append_to_master_report(report_rows, matches, total, validation_date, previous_date, stage)


def _append_to_master_report(
    rows: list[dict[str, Any]],
    matches: int,
    total: int,
    validation_date: date,
    comparison_date: str,
    stage: str,
) -> None:
    """Append comparison results to master report CSV."""
    fieldnames = [
        "validation_date",
        "comparison_date",
        "stage",
        "strategy_name",
        "status",
        "our_signals",
        "live_signals",
        "symbol_details",
        "recorded_at",
    ]

    file_exists = MASTER_REPORT_PATH.exists()
    with open(MASTER_REPORT_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"\n📊 Master report updated: {MASTER_REPORT_PATH}")
    print(f"   Added {len(rows)} rows for {validation_date} ({matches}/{total} matched)")


# ============================================================================
# Main
# ============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate signals using shifted T-1 comparison")
    parser.add_argument("--stage", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument(
        "--session-id", type=str, help="Specific DynamoDB session ID (implies --dynamo)"
    )
    parser.add_argument(
        "--dynamo", action="store_true", help="Use DynamoDB instead of local CSV for our_signals"
    )
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open URLs")
    parser.add_argument("--fresh", action="store_true", help="Start fresh")
    # Keep --shifted for backwards compatibility but it's now a no-op
    parser.add_argument("--shifted", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("Signal Validation (Shifted T-1)")
    print("=" * 80)
    print(f"\nStage: {args.stage}")
    print("\nWorkflow:")
    print("  1. Load our_signals (local CSV or DynamoDB)")
    print("  2. Capture today's live_signals from Composer")
    print("  3. Compare today's our_signals vs YESTERDAY's live_signals")

    # --session-id implies --dynamo
    use_dynamo = args.dynamo or args.session_id is not None

    if use_dynamo:
        _run_dynamo_flow(args)
    else:
        _run_local_flow(args)


def _run_local_flow(args: argparse.Namespace) -> None:
    """Default flow: load our_signals from locally-generated CSV.

    Args:
        args: Parsed CLI arguments.

    """
    validation_date = datetime.now(tz=UTC).date()
    print("\nSource: Local CSV (validation_results/local_signals/)")
    print(f"Date: {validation_date.isoformat()}")

    signals = load_local_signals(validation_date, args.stage)

    if signals is None:
        local_path = LOCAL_SIGNALS_DIR / f"{validation_date.isoformat()}_{args.stage}.csv"
        print(f"\nNo local signals found for {validation_date} ({args.stage})")
        print(f"Expected: {local_path}")
        print("\nRun signal generation first:")
        print(f"  make generate-signals stage={args.stage}")
        print("\nOr use DynamoDB as source:")
        print(f"  make validate-signals stage={args.stage} dynamo=1")
        sys.exit(1)

    print(f"Loaded {len(signals)} signals from local CSV")

    session_id = f"local-{validation_date.isoformat()}"
    _run_capture_flow(args, signals, session_id, validation_date)


def _run_dynamo_flow(args: argparse.Namespace) -> None:
    """Legacy flow: load our_signals from DynamoDB.

    Args:
        args: Parsed CLI arguments.

    """
    _, ClientError = _import_boto3()

    print("\nSource: DynamoDB (legacy mode)")

    # Initialize DynamoDB
    table_name = f"alchemiser-{args.stage}-aggregation-sessions"
    try:
        client = get_dynamodb_client()
    except Exception as e:
        print(f"\nDynamoDB error: {e}")
        sys.exit(1)

    # Find session
    print("\nFinding latest session...")
    if args.session_id:
        session_id = args.session_id
        validation_date = datetime.now(tz=UTC).date()
    else:
        try:
            latest = get_latest_session(client, table_name)
            if not latest:
                print("No sessions found")
                sys.exit(1)

            session_id = latest["session_id"]
            session_date = latest["created_at"].split("T")[0]
            session_time = latest["created_at"].split("T")[1].split(".")[0]
            validation_date = date.fromisoformat(session_date)
            print(f"\nFound: {session_date} @ {session_time} UTC")
            print(f"   Session: {session_id}")
            print(f"   Strategies: {latest['total_strategies']}")
        except ClientError as e:
            print(f"\nDynamoDB error: {e}")
            sys.exit(1)

    # Get signals from DynamoDB
    print("\nLoading signals from DynamoDB...")
    try:
        raw_signals = get_all_partial_signals(client, table_name, session_id)
        print(f"Found {len(raw_signals)} signals")
    except ClientError as e:
        print(f"\nQuery error: {e}")
        sys.exit(1)

    if not raw_signals:
        print("No signals found")
        sys.exit(1)

    # Convert DynamoDB format to common format: list of {dsl_file, our_signals}
    signals: list[dict[str, Any]] = []
    for sig in raw_signals:
        raw = sig["consolidated_portfolio"].get("target_allocations", {})
        alloc = sig["allocation"]
        our_signals = {sym: Decimal(str(w)) / alloc for sym, w in raw.items()}
        signals.append(
            {
                "dsl_file": sig["dsl_file"],
                "our_signals": our_signals,
            }
        )

    _run_capture_flow(args, signals, session_id, validation_date)


def _run_capture_flow(
    args: argparse.Namespace,
    signals: list[dict[str, Any]],
    session_id: str,
    validation_date: date,
) -> None:
    """Common capture flow: prompt for Composer holdings + run comparison.

    Args:
        args: Parsed CLI arguments.
        signals: List of signal dicts with 'dsl_file' and 'our_signals' keys.
        session_id: Session ID for CSV records.
        validation_date: Date of the signal data.

    """
    # Load ledger
    print("\nLoading strategy ledger...")
    try:
        ledger = load_strategy_ledger(LEDGER_PATH)
        print(f"Loaded {len(ledger)} strategies")
    except Exception as e:
        print(f"\nLedger error: {e}")
        sys.exit(1)

    # Setup CSV
    csv_path = get_csv_path(validation_date, args.stage)
    if args.fresh and csv_path.exists():
        csv_path.unlink()
        print("\nFresh mode - cleared previous")

    captured = load_captured_strategies(csv_path) if not args.fresh else set()
    if captured:
        print(f"\nResuming ({len(captured)} already captured)")

    # Capture loop
    stats = {"captured": 0, "skipped": 0}
    today_our_signals: dict[str, dict[str, Decimal]] = {}

    try:
        for i, signal in enumerate(signals, 1):
            dsl_file = signal["dsl_file"]
            strategy_name = dsl_file.replace(".clj", "")
            our_signals: dict[str, Decimal] = signal["our_signals"]

            if dsl_file in captured:
                print(f"\nSkipping {strategy_name} (already captured)")
                continue

            today_our_signals[strategy_name] = our_signals.copy()

            strategy = find_strategy_by_filename(ledger, dsl_file)

            # Display
            print("\n" + "-" * 80)
            print(f"\nStrategy {i} of {len(signals)}: {strategy_name}")
            if strategy:
                print(f"Composer URL: {strategy.get('source_url', 'N/A')}")

            # Show our signal
            print("Our signal: ", end="")
            for sym, w in sorted(our_signals.items(), key=lambda x: -float(x[1])):
                print(f"{sym}={float(w) * 100:.1f}% ", end="")
            print()

            # Open browser
            if not args.no_browser and strategy and strategy.get("source_url"):
                try:
                    webbrowser.open(strategy["source_url"])
                except Exception:
                    pass

            # Capture
            print("\nCapture live_signals from Composer:")
            live_signals = capture_live_signals(strategy_name)

            if live_signals:
                stats["captured"] += 1
                print(f"\nCaptured {len(live_signals)} holdings")
            else:
                stats["skipped"] += 1
                print("\nNo capture")

            # Save record
            def to_json(d: dict[str, Decimal] | None) -> str:
                return json.dumps({k: float(v) for k, v in d.items()}, sort_keys=True) if d else ""

            configs = get_all_indicator_configs()
            config_json = json.dumps(
                {n: c.use_live_bar for n, c in configs.items()}, sort_keys=True
            )

            append_record(
                csv_path,
                {
                    "validation_date": validation_date.isoformat(),
                    "session_id": session_id,
                    "strategy_name": strategy_name,
                    "dsl_file": dsl_file,
                    "our_signals": to_json(our_signals),
                    "live_signals": to_json(live_signals),
                    "partial_bar_config": config_json,
                    "captured_at": datetime.now(UTC).isoformat(),
                },
            )

    except KeyboardInterrupt:
        print("\n\nInterrupted - progress saved")
        print(f"Run again to resume from: {csv_path}")
        sys.exit(0)

    # Summary
    print("\n" + "=" * 80)
    print("Capture Complete!")
    print("=" * 80)
    print(f"\nCaptured: {stats['captured']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"\nSaved to: {csv_path}")

    # Run comparison
    previous_csv = find_previous_csv(validation_date, args.stage)
    if previous_csv:
        match = re.search(r"signal_validation_(\d{4}-\d{2}-\d{2})", previous_csv.name)
        prev_date = match.group(1) if match else "previous"

        prev_live = load_live_signals_from_csv(previous_csv)
        if prev_live:
            run_comparison_report(
                today_our_signals, prev_live, prev_date, validation_date, args.stage
            )
        else:
            print(f"\nNo live_signals in: {previous_csv}")
    else:
        print(f"\nNo previous CSV found (searched 5 days back from {validation_date})")


if __name__ == "__main__":
    main()
