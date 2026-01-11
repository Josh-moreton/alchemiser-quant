#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Strategy Ledger Management CLI.

Interactive CLI tool for managing the strategy ledger YAML file. Allows adding
new strategies by extracting metadata from .clj strategy files, and syncing
the ledger to DynamoDB for web UI access.

Usage:
    python scripts/strategy_ledger.py add
    python scripts/strategy_ledger.py add-from-config --config strategy.dev.json
    python scripts/strategy_ledger.py list
    python scripts/strategy_ledger.py sync --stage dev
    python scripts/strategy_ledger.py sync --stage prod

The 'add' command will interactively prompt for:
    - Local .clj filename (must exist in strategies directory)
    - Composer source URL

The 'add-from-config' command will:
    - Read all files from a strategy config JSON (e.g., strategy.dev.json)
    - Add entries for any files not already in the ledger
    - Prompt for source URL only for new entries

It will automatically extract:
    - strategy_name from filename stem (matches runtime attribution)
    - display_name from defsymphony declaration
    - Assets (tickers used in asset declarations)
    - Frontrunners (tickers used in indicators but not as assets)

The 'sync' command pushes all ledger entries to DynamoDB for web UI access.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# Strategy files directory (refactored to shared layer)
STRATEGIES_DIR = (
    Path(__file__).parent.parent
    / "layers"
    / "shared"
    / "the_alchemiser"
    / "shared"
    / "strategies"
)
CONFIG_DIR = (
    Path(__file__).parent.parent
    / "layers"
    / "shared"
    / "the_alchemiser"
    / "shared"
    / "config"
)
LEDGER_FILE = STRATEGIES_DIR / "strategy_ledger.yaml"


def load_ledger() -> dict[str, Any]:
    """Load the strategy ledger YAML file."""
    if not LEDGER_FILE.exists():
        return {}
    with LEDGER_FILE.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
        return content if content else {}


def save_ledger(ledger: dict[str, Any]) -> None:
    """Save the strategy ledger YAML file."""
    with LEDGER_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(ledger, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def extract_strategy_name(content: str) -> str | None:
    """Extract strategy name from defsymphony declaration.

    Format: (defsymphony "Strategy Name" ...) or with newline after defsymphony
    """
    # Use re.DOTALL to handle newlines between defsymphony and the string
    match = re.search(r'\(defsymphony\s+"([^"]+)"', content, re.DOTALL)
    return match.group(1) if match else None


def extract_assets(content: str) -> set[str]:
    """Extract all asset tickers from (asset "TICKER" ...) declarations."""
    # Match (asset "TICKER" ...) - captures the ticker symbol
    # Allow 1-10 chars: uppercase letters, numbers, dots, slashes (for BRK.B, BTC/USD, etc.)
    pattern = re.compile(r'\(asset\s+"([A-Z0-9./]{1,10})"')
    return set(pattern.findall(content))


def extract_indicator_tickers(content: str) -> set[str]:
    """Extract all tickers used in indicators (rsi, current-price, moving-average-price).

    These are tickers used in conditional logic but not necessarily held as assets.
    """
    tickers: set[str] = set()

    # RSI pattern: (rsi "TICKER" {:window N})
    rsi_pattern = re.compile(r'\(rsi\s+"([A-Z/]{1,5})"\s+\{')
    tickers.update(rsi_pattern.findall(content))

    # current-price pattern: (current-price "TICKER")
    price_pattern = re.compile(r'\(current-price\s+"([A-Z/]{1,5})"\)')
    tickers.update(price_pattern.findall(content))

    # moving-average-price pattern: (moving-average-price "TICKER" {:window N})
    ma_pattern = re.compile(r'\(moving-average-price\s+"([A-Z/]{1,5})"\s+\{')
    tickers.update(ma_pattern.findall(content))

    return tickers


def extract_strategy_name_from_filename(filename: str) -> str:
    """Extract strategy_name from filename (stem without extension).

    This matches the runtime attribution pattern used in strategy_engine.py.

    Examples:
        - rains_core_catalysts.clj -> rains_core_catalysts
        - dev/rain.clj -> rain

    """
    path = Path(filename)
    return path.stem


def prompt_yes_no(question: str, *, default: bool = True) -> bool:
    """Prompt user for yes/no confirmation."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        response = input(question + suffix).strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'")


def prompt_file_selection(clj_files: list[Path]) -> tuple[Path, str] | None:
    """Prompt user to select a strategy file.

    Args:
        clj_files: List of available .clj files

    Returns:
        Tuple of (filepath, relative_filename) or None if cancelled

    """
    while True:
        filename_input = input("Enter the .clj filename (or number): ").strip()
        if not filename_input:
            print("ERROR: Filename is required")
            continue

        # Allow selection by number
        if filename_input.isdigit():
            idx = int(filename_input) - 1
            if 0 <= idx < len(clj_files):
                filepath = clj_files[idx]
                filename = str(filepath.relative_to(STRATEGIES_DIR))
                return filepath, filename
            print(f"ERROR: Invalid number. Choose 1-{len(clj_files)}")
            continue

        # Direct filename input
        filename = filename_input
        if not filename.endswith(".clj"):
            filename += ".clj"
        filepath = STRATEGIES_DIR / filename
        if not filepath.exists():
            print(f"ERROR: File not found: {filepath}")
            continue
        return filepath, filename


def prompt_source_url() -> str:
    """Prompt user for Composer source URL.

    Returns:
        Valid URL string

    """
    while True:
        source_url = input("\nEnter Composer source URL: ").strip()
        if not source_url:
            print("ERROR: Source URL is required")
            continue
        if not source_url.startswith("http"):
            print("ERROR: URL must start with http:// or https://")
            continue
        return source_url


def cmd_add() -> int:
    """Interactive command to add a strategy to the ledger."""
    print("\n=== Add Strategy to Ledger ===\n")

    # List available .clj files (including subdirectories)
    clj_files = sorted(STRATEGIES_DIR.rglob("*.clj"))
    if not clj_files:
        print(f"ERROR: No .clj files found in {STRATEGIES_DIR}")
        return 1

    print("Available strategy files:")
    for i, f in enumerate(clj_files, 1):
        rel_path = f.relative_to(STRATEGIES_DIR)
        print(f"  {i}. {rel_path}")
    print()

    # Prompt for filename
    result = prompt_file_selection(clj_files)
    if result is None:
        return 1
    filepath, filename = result

    # Read strategy file
    content = filepath.read_text(encoding="utf-8")

    # Extract strategy_name from filename (matches runtime attribution)
    strategy_name = extract_strategy_name_from_filename(filename)
    print(f"\nstrategy_name (from filename): {strategy_name}")

    # Extract display_name from defsymphony
    display_name = extract_strategy_name(content)
    if display_name:
        print(f"display_name (from defsymphony): {display_name}")
    else:
        print("WARNING: Could not extract display_name from defsymphony declaration")
        display_name = strategy_name  # Fallback to strategy_name

    # Extract assets and frontrunners
    assets = extract_assets(content)
    indicator_tickers = extract_indicator_tickers(content)
    frontrunners = indicator_tickers - assets  # Tickers used in indicators but not as assets

    print(f"Found {len(assets)} assets: {sorted(assets)}")
    if frontrunners:
        print(f"Found {len(frontrunners)} frontrunners: {sorted(frontrunners)}")

    # Prompt for Composer URL
    source_url = prompt_source_url()

    # Load existing ledger
    ledger = load_ledger()

    # Check if strategy already exists
    if strategy_name in ledger:
        print(f"\nWARNING: Strategy '{strategy_name}' already exists in ledger.")
        if not prompt_yes_no("Do you want to update/overwrite it?"):
            print("Aborted.")
            return 0

    # Build entry using strategy_name as the key (matches runtime attribution)
    entry: dict[str, Any] = {
        "strategy_name": strategy_name,
        "display_name": display_name,
        "source_url": source_url,
        "filename": filename,
        "date_updated": datetime.now(UTC).strftime("%Y-%m-%d"),
        "assets": sorted(assets),
    }

    if frontrunners:
        entry["frontrunners"] = sorted(frontrunners)

    # Confirm before saving
    print("\n--- Entry Preview ---")
    print(yaml.dump({strategy_name: entry}, default_flow_style=False, allow_unicode=True))

    if not prompt_yes_no("Save this entry?"):
        print("Aborted.")
        return 0

    # Save
    ledger[strategy_name] = entry
    save_ledger(ledger)
    print(f"\n✓ Strategy '{strategy_name}' added to ledger.")

    return 0


def cmd_add_from_config(config_file: str) -> int:
    """Add all strategies from a config file to the ledger.

    Args:
        config_file: Strategy config JSON filename (e.g., strategy.dev.json)

    Returns:
        Exit code (0 for success)

    """
    print(f"\n=== Add Strategies from Config: {config_file} ===\n")

    # Load config
    config_path = CONFIG_DIR / config_file
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return 1

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    files = config.get("files", [])
    if not files:
        print("ERROR: No files found in config")
        return 1

    print(f"Found {len(files)} strategy files in config:")
    for f in files:
        print(f"  - {f}")
    print()

    # Load existing ledger
    ledger = load_ledger()

    added_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in files:
        # Extract strategy_name from filename
        strategy_name = extract_strategy_name_from_filename(file_path)

        # Check if already exists
        if strategy_name in ledger:
            print(f"  ⊘ {strategy_name} (already in ledger)")
            skipped_count += 1
            continue

        # Read strategy file
        full_path = STRATEGIES_DIR / file_path
        if not full_path.exists():
            print(f"  ✗ {strategy_name}: file not found: {full_path}")
            error_count += 1
            continue

        content = full_path.read_text(encoding="utf-8")

        # Extract display_name from defsymphony
        display_name = extract_strategy_name(content) or strategy_name

        # Extract assets and frontrunners
        assets = extract_assets(content)
        indicator_tickers = extract_indicator_tickers(content)
        frontrunners = indicator_tickers - assets

        # Prompt for source URL
        print(f"\n  Strategy: {strategy_name} ({display_name})")
        print(f"    Assets: {len(assets)}, Frontrunners: {len(frontrunners)}")

        while True:
            source_url = input(f"    Enter Composer URL for '{display_name}': ").strip()
            if not source_url:
                if prompt_yes_no("      Skip this strategy?", default=False):
                    break
                continue
            if not source_url.startswith("http"):
                print("      ERROR: URL must start with http:// or https://")
                continue
            break

        if not source_url:
            print(f"  ⊘ {strategy_name} (skipped by user)")
            skipped_count += 1
            continue

        # Build entry
        entry: dict[str, Any] = {
            "strategy_name": strategy_name,
            "display_name": display_name,
            "source_url": source_url,
            "filename": file_path,
            "date_updated": datetime.now(UTC).strftime("%Y-%m-%d"),
            "assets": sorted(assets),
        }

        if frontrunners:
            entry["frontrunners"] = sorted(frontrunners)

        # Add to ledger
        ledger[strategy_name] = entry
        print(f"  ✓ {strategy_name}")
        added_count += 1

    # Save ledger
    save_ledger(ledger)

    print(f"\nComplete: {added_count} added, {skipped_count} skipped, {error_count} errors")
    return 0 if error_count == 0 else 1


def cmd_list() -> int:
    """List all strategies in the ledger."""
    ledger = load_ledger()

    if not ledger:
        print("Ledger is empty.")
        return 0

    print(f"\n=== Strategy Ledger ({len(ledger)} strategies) ===\n")

    for strategy_name, entry in ledger.items():
        display_name = entry.get("display_name", strategy_name)
        filename = entry.get("filename", "?")
        assets_count = len(entry.get("assets", []))
        frontrunners_count = len(entry.get("frontrunners", []))
        date_updated = entry.get("date_updated", "?")

        print(f"  {strategy_name}")
        print(f"    Display: {display_name}")
        print(f"    File: {filename}")
        print(f"    Assets: {assets_count}, Frontrunners: {frontrunners_count}")
        print(f"    Updated: {date_updated}")
        print()

    return 0


def cmd_sync(stage: str) -> int:
    """Sync strategy ledger to DynamoDB.

    Args:
        stage: Deployment stage ('dev' or 'prod')

    Returns:
        Exit code (0 for success)

    """
    # Import here to avoid boto3 dependency for non-sync commands
    try:
        from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
            DynamoDBTradeLedgerRepository,
        )
    except ImportError as e:
        print(f"ERROR: Could not import DynamoDB repository: {e}")
        print("Make sure you're running with 'poetry run python'")
        return 1

    # Determine table name
    table_name = f"alchemiser-{stage}-trade-ledger"
    print("\n=== Syncing Strategy Ledger to DynamoDB ===")
    print(f"Table: {table_name}\n")

    # Load ledger
    ledger = load_ledger()
    if not ledger:
        print("Ledger is empty. Nothing to sync.")
        return 0

    # Initialize repository
    try:
        repo = DynamoDBTradeLedgerRepository(table_name)
    except Exception as e:
        print(f"ERROR: Could not connect to DynamoDB: {e}")
        return 1

    # Sync each entry
    success_count = 0
    error_count = 0

    for strategy_name, entry in ledger.items():
        # Validate strategy_name matches entry
        if entry.get("strategy_name") != strategy_name:
            print(f"  ⚠ Skipping '{strategy_name}': strategy_name mismatch in entry")
            error_count += 1
            continue

        try:
            repo.put_strategy_metadata(
                strategy_name=strategy_name,
                display_name=entry.get("display_name", strategy_name),
                source_url=entry.get("source_url", ""),
                filename=entry.get("filename", ""),
                assets=entry.get("assets", []),
                frontrunners=entry.get("frontrunners"),
                date_updated=entry.get("date_updated"),
            )
            print(f"  ✓ {strategy_name}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {strategy_name}: {e}")
            error_count += 1

    print(f"\nSync complete: {success_count} succeeded, {error_count} failed")
    return 0 if error_count == 0 else 1


def cmd_list_dynamo(stage: str) -> int:
    """List strategies from DynamoDB.

    Args:
        stage: Deployment stage ('dev' or 'prod')

    Returns:
        Exit code (0 for success)

    """
    try:
        from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
            DynamoDBTradeLedgerRepository,
        )
    except ImportError as e:
        print(f"ERROR: Could not import DynamoDB repository: {e}")
        return 1

    table_name = f"alchemiser-{stage}-trade-ledger"
    print(f"\n=== Strategies in DynamoDB ({table_name}) ===\n")

    try:
        repo = DynamoDBTradeLedgerRepository(table_name)
        strategies = repo.list_strategy_metadata()
    except Exception as e:
        print(f"ERROR: Could not query DynamoDB: {e}")
        return 1

    if not strategies:
        print("No strategies found in DynamoDB.")
        return 0

    for entry in strategies:
        strategy_name = entry.get("strategy_name", "?")
        display_name = entry.get("display_name", "?")
        assets = entry.get("assets", [])
        frontrunners = entry.get("frontrunners", [])
        synced_at = entry.get("synced_at", "?")

        print(f"  {strategy_name}")
        print(f"    Display: {display_name}")
        print(f"    Assets: {len(assets)}, Frontrunners: {len(frontrunners)}")
        print(f"    Synced: {synced_at}")
        print()

    return 0


def main() -> int:
    """Run the strategy ledger CLI."""
    parser = argparse.ArgumentParser(
        description="Strategy Ledger Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    subparsers.add_parser("add", help="Add a strategy to the ledger interactively")

    # Add from config command
    add_config_parser = subparsers.add_parser(
        "add-from-config", help="Add strategies from a config file (e.g., strategy.dev.json)"
    )
    add_config_parser.add_argument(
        "--config",
        default="strategy.dev.json",
        help="Strategy config filename (default: strategy.dev.json)",
    )

    # List command
    subparsers.add_parser("list", help="List all strategies in the YAML ledger")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync ledger to DynamoDB for web UI access")
    sync_parser.add_argument(
        "--stage",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment stage (default: dev)",
    )

    # List from DynamoDB command
    list_dynamo_parser = subparsers.add_parser("list-dynamo", help="List strategies from DynamoDB")
    list_dynamo_parser.add_argument(
        "--stage",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Deployment stage (default: dev)",
    )

    args = parser.parse_args()

    if args.command == "add":
        return cmd_add()
    if args.command == "add-from-config":
        return cmd_add_from_config(args.config)
    if args.command == "list":
        return cmd_list()
    if args.command == "sync":
        return cmd_sync(args.stage)
    if args.command == "list-dynamo":
        return cmd_list_dynamo(args.stage)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
