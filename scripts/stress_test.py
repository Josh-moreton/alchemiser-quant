#!/usr/bin/env python3
"""Business Unit: utilities | Status: current.

Stress Test Script for The Alchemiser Trading System.

This script runs comprehensive stress testing by:
1. Running the trading system with real Alpaca Paper API
2. Liquidating all positions (liquidation mode) OR maintaining portfolio state (stateful mode)
3. Mocking different market conditions (RSI values, prices)
4. Iterating through all possible market scenarios
5. Logging outcomes and detecting edge cases

The script uses real Alpaca Paper trading endpoints and is expected
to have a runtime of 1+ hours as it iterates through all market conditions.

Market conditions are simulated by mocking the IndicatorService to return
controlled RSI values and prices for all symbols used in strategy CLJ files.

Usage:
    python scripts/stress_test.py [--quick] [--dry-run] [--stateful]

Options:
    --quick     Run a subset of scenarios for faster testing (~14 scenarios)
    --dry-run   Skip actual trading system execution, just show plan
    --stateful  Maintain portfolio state across scenarios (no liquidation)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))  # Add scripts dir to path

# Import from modular stress_test package
from stress_test.runner import StressTestRunner

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import configure_application_logging

# Configure logging
configure_application_logging()

# Constant: always force paper endpoint for stress testing to avoid live trades
PAPER_ENDPOINT = "https://paper-api.alpaca.markets/v2"


def _ensure_stress_test_credentials() -> bool:
    """If STRESS_TEST_KEY/SECRET are set, override runtime Alpaca env vars.

    Returns:
        True if stress-test credentials were applied, False otherwise.

    Notes:
        - Endpoint is always forced to Alpaca paper to prevent accidental live usage.
        - Secrets are not logged.

    """
    key = os.getenv("STRESS_TEST_KEY")
    secret = os.getenv("STRESS_TEST_SECRET")
    if key and secret:
        # Override standard environment variables consumed by the app
        os.environ["ALPACA_KEY"] = key
        os.environ["ALPACA_SECRET"] = secret
        os.environ["ALPACA_ENDPOINT"] = PAPER_ENDPOINT
        return True
    return False


def main_cli() -> int:
    """Run stress test CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    parser = argparse.ArgumentParser(
        description="Stress test The Alchemiser trading system across all market conditions"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with subset of scenarios (~14 scenarios)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - show plan without executing trades",
    )
    parser.add_argument(
        "--stateful",
        action="store_true",
        help="Stateful mode - maintain portfolio state across scenarios (no liquidation)",
    )
    parser.add_argument(
        "--output",
        default="stress_test_results.json",
        help="Output file for results (default: stress_test_results.json)",
    )

    args = parser.parse_args()

    # Prefer dedicated stress-test credentials if provided
    used_stress_creds = _ensure_stress_test_credentials()
    # Always force paper endpoint for stress testing (even if regular ALPACA_KEY/SECRET are used)
    os.environ["ALPACA_ENDPOINT"] = PAPER_ENDPOINT

    # Verify environment
    if not args.dry_run:
        try:
            api_key, secret_key, _ = get_alpaca_keys()
            if not api_key or not secret_key:
                print("ERROR: Alpaca API credentials not found in environment")
                print("Please set ALPACA_KEY and ALPACA_SECRET environment variables")
                return 1
        except Exception as e:
            print(f"ERROR: Failed to load Alpaca credentials: {e}")
            return 1

    # Run stress test
    runner = StressTestRunner(
        quick_mode=args.quick, dry_run=args.dry_run, stateful_mode=args.stateful
    )

    print("\n" + "=" * 80)
    print("THE ALCHEMISER - STRESS TEST")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN' if args.dry_run else 'LIVE PAPER TRADING'}")
    print(f"Portfolio Mode: {'STATEFUL' if args.stateful else 'LIQUIDATION'}")
    print(f"Scenarios: {'Quick (~14)' if args.quick else 'Full (~34)'}")
    print(f"Output: {args.output}")
    if used_stress_creds:
        print("Credentials: using STRESS_TEST_KEY/SECRET (paper endpoint forced)")
    else:
        print("Credentials: using ALPACA_KEY/SECRET from environment (paper endpoint forced)")
    print("\n" + "=" * 80 + "\n")

    if args.dry_run:
        # In dry run, just show the plan
        conditions = runner.generate_market_conditions()
        print(f"\nWould execute {len(conditions)} scenarios:\n")
        for i, condition in enumerate(conditions, 1):
            print(f"{i:3d}. {condition.scenario_id}: {condition.description}")
        print("\nUse without --dry-run to execute actual stress test")
        return 0

    # Execute full stress test
    start_time = time.time()
    results = runner.run_all_scenarios()
    total_time = time.time() - start_time

    # Get reporter and save results
    reporter = runner.get_reporter()
    report = reporter.generate_report()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    reporter.print_summary()

    print(f"\nTotal execution time: {total_time / 60:.1f} minutes")
    print(f"Results saved to: {args.output}\n")

    # Return success if all scenarios passed
    return 0 if all(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main_cli())
