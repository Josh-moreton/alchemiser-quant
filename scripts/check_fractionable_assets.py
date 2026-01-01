#!/usr/bin/env python3
"""Business Unit: scripts; Status: current.

Check Fractionable Assets Script.

Extracts all unique symbols from DSL strategy files and queries the Alpaca API
to determine which assets are NOT fractionable. This helps identify assets that
may require special handling during order placement.

Usage:
    python scripts/check_fractionable_assets.py
    python scripts/check_fractionable_assets.py --verbose
    python scripts/check_fractionable_assets.py --show-all
    python scripts/check_fractionable_assets.py --config strategy.prod.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

# Get project root for .env file loading
project_root = _setup_imports.PROJECT_ROOT

# Load .env file automatically (simple parser, no dependencies needed)
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith("#"):
                # Simple key=value parsing
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.asset_info import AssetInfo

configure_application_logging()
logger = get_logger(__name__)

STRATEGIES_DIR = project_root / "functions" / "strategy_worker" / "strategies"
CONFIG_DIR = project_root / "functions" / "strategy_worker" / "config"


def extract_symbols_from_dsl(file_path: Path) -> set[str]:
    """Extract all unique symbols from a DSL strategy file.

    Only extracts symbols from (asset "SYMBOL" ...) declarations, not from
    technical indicators, since we only trade the assets, not the indicator symbols.

    Args:
        file_path: Path to the .clj DSL file

    Returns:
        Set of unique symbols found in the file
    """
    symbols: set[str] = set()

    try:
        content = file_path.read_text()

        # Match (asset "SYMBOL" "description")
        # Captures the symbol in the first quoted string after 'asset'
        asset_pattern = r'\(asset\s+"([A-Z]+)"'
        asset_matches = re.findall(asset_pattern, content)
        symbols.update(asset_matches)

        logger.debug(f"Extracted {len(symbols)} symbols from {file_path.name}", symbols=sorted(symbols))

    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")

    return symbols


def load_strategy_config(config_file: str) -> list[str]:
    """Load strategy files from a config JSON file.

    Args:
        config_file: Name of the config file (e.g., 'strategy.dev.json')

    Returns:
        List of strategy file names from the config
    """
    config_path = CONFIG_DIR / config_file

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    try:
        with config_path.open() as f:
            config = json.load(f)

        # Get the "files" list from the config
        files = config.get("files", [])

        if not files:
            logger.error(f"No 'files' found in config: {config_file}")
            sys.exit(1)

        logger.info(f"Loaded {len(files)} strategies from {config_file}")
        return files

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {config_file}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading config {config_file}: {e}")
        sys.exit(1)


def get_all_symbols_from_strategies(
    config_file: str | None = None,
) -> tuple[set[str], dict[str, list[str]]]:
    """Extract all unique symbols from DSL strategy files.

    Args:
        config_file: Optional config file name. If provided, only scan strategies
                     listed in that config. Otherwise, scan all .clj files.

    Returns:
        Tuple of:
        - Set of all unique symbols across selected strategy files
        - Dict mapping each symbol to list of strategy filenames that use it
    """
    all_symbols: set[str] = set()
    symbol_to_strategies: dict[str, list[str]] = {}

    if not STRATEGIES_DIR.exists():
        logger.error(f"Strategies directory not found: {STRATEGIES_DIR}")
        return all_symbols, symbol_to_strategies

    # Determine which files to scan
    if config_file:
        strategy_files = load_strategy_config(config_file)
        clj_files = [STRATEGIES_DIR / f for f in strategy_files]
        # Verify files exist
        clj_files = [f for f in clj_files if f.exists()]
        if len(clj_files) != len(strategy_files):
            logger.warning("Some strategy files from config not found")
    else:
        clj_files = list(STRATEGIES_DIR.glob("*.clj"))

    logger.info(f"Scanning {len(clj_files)} strategy files...")

    for clj_file in clj_files:
        symbols = extract_symbols_from_dsl(clj_file)
        all_symbols.update(symbols)

        # Track which strategies use which symbols
        strategy_name = clj_file.name
        for symbol in symbols:
            if symbol not in symbol_to_strategies:
                symbol_to_strategies[symbol] = []
            symbol_to_strategies[symbol].append(strategy_name)

    return all_symbols, symbol_to_strategies


def check_fractionability(symbols: set[str], verbose: bool = False) -> dict[str, AssetInfo]:
    """Check fractionability for all symbols using Alpaca API.

    Args:
        symbols: Set of symbols to check
        verbose: If True, log detailed progress

    Returns:
        Dictionary mapping symbols to their AssetInfo (only non-fractionable or errors)
    """
    # Initialize Alpaca manager
    api_key = os.environ.get("ALPACA__KEY") or os.environ.get("ALPACA_KEY")
    secret_key = os.environ.get("ALPACA__SECRET") or os.environ.get("ALPACA_SECRET")

    if not api_key or not secret_key:
        logger.error("Alpaca credentials not found!")
        logger.error("Set ALPACA__KEY and ALPACA__SECRET in your environment")
        sys.exit(1)

    alpaca = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=True)

    results: dict[str, AssetInfo] = {}
    fractionable_count = 0
    error_count = 0

    sorted_symbols = sorted(symbols)
    total = len(sorted_symbols)

    logger.info(f"Checking {total} symbols for fractionability...")
    print()

    for i, symbol in enumerate(sorted_symbols, 1):
        try:
            asset_info = alpaca.get_asset_info(symbol)

            if asset_info is None:
                logger.warning(f"[{i}/{total}] {symbol}: Not found")
                error_count += 1
                # Delay before next request
                time.sleep(0.25)
                continue

            if not asset_info.fractionable:
                results[symbol] = asset_info
                status = "❌ NOT FRACTIONABLE"
                if verbose:
                    print(f"[{i}/{total}] {symbol}: {status}")
            else:
                fractionable_count += 1
                if verbose:
                    print(f"[{i}/{total}] {symbol}: ✅ Fractionable")

        except Exception as e:
            logger.error(f"[{i}/{total}] {symbol}: Error - {e}")
            error_count += 1

        # Rate limit: conservative delay between requests (250ms = 4 requests/sec)
        time.sleep(0.25)

    print()
    logger.info(f"Scan complete: {total} symbols checked")
    logger.info(f"  ✅ Fractionable: {fractionable_count}")
    logger.info(f"  ❌ Non-fractionable: {len(results)}")
    logger.info(f"  ⚠️  Errors/Not found: {error_count}")

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check which assets in DSL strategies are not fractionable"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="strategy.dev.json",
        help="Config file to use (default: strategy.dev.json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress for all symbols",
    )
    parser.add_argument(
        "--show-all",
        "-a",
        action="store_true",
        help="Show detailed asset info for non-fractionable assets",
    )
    parser.add_argument(
        "--all-strategies",
        action="store_true",
        help="Scan all .clj files instead of using a config file",
    )

    args = parser.parse_args()

    # Extract all symbols from strategy files
    config_file = None if args.all_strategies else args.config
    symbols, symbol_to_strategies = get_all_symbols_from_strategies(config_file)

    if not symbols:
        logger.error("No symbols found in strategy files!")
        sys.exit(1)

    logger.info(f"Found {len(symbols)} unique symbols in strategies")

    # Check fractionability
    non_fractionable = check_fractionability(symbols, verbose=args.verbose)

    # Display results
    print()
    print("=" * 80)
    print("NON-FRACTIONABLE ASSETS")
    print("=" * 80)
    print()

    if not non_fractionable:
        print("✅ All assets are fractionable!")
    else:
        for symbol, asset_info in sorted(non_fractionable.items()):
            strategies = symbol_to_strategies.get(symbol, [])
            strategy_list = ", ".join(sorted(strategies))

            print(f"  {symbol:6s} - {asset_info.name or 'Unknown'}")
            print(f"           Used in: {strategy_list}")

            if args.show_all:
                print(f"           Exchange: {asset_info.exchange or 'N/A'}")
                print(f"           Asset Class: {asset_info.asset_class or 'N/A'}")
                print(f"           Tradable: {asset_info.tradable}")
                print(f"           Marginable: {asset_info.marginable}")
                print(f"           Shortable: {asset_info.shortable}")
            print()

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
