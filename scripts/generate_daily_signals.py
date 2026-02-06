#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Generate daily strategy signals locally for validation against Composer.trade.

Runs all configured strategies through the DSL engine using completed daily bars
from S3 data lake and writes our_signals to a local CSV. The output CSV is
consumed by validate_signals.py for shifted T-1 comparison.

Run after market close (4:00 PM ET) once the post-close data refresh has
completed (4:05 PM ET). Scheduled via launchd at 4:20 PM local time (Mon-Fri).

Prerequisites:
    - AWS credentials configured (for S3 market data reads)
    - Market data refreshed in S3 (populated by Data Lambda post-close refresh)

Usage:
    make generate-signals                      # Both dev + prod
    make generate-signals stage=dev            # Dev only
    make generate-signals stage=prod           # Prod only

    poetry run python scripts/generate_daily_signals.py --stage both
    poetry run python scripts/generate_daily_signals.py --stage dev
    poetry run python scripts/generate_daily_signals.py --stage prod --log-file /tmp/signals.log
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
STRATEGY_WORKER_PATH = PROJECT_ROOT / "functions" / "strategy_worker"
SHARED_LAYER_PATH = PROJECT_ROOT / "layers" / "shared"
STRATEGIES_PATH = SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "strategies"
CONFIG_PATH = SHARED_LAYER_PATH / "the_alchemiser" / "shared" / "config"
OUTPUT_DIR = PROJECT_ROOT / "validation_results" / "local_signals"

# Add paths for imports
sys.path.insert(0, str(STRATEGY_WORKER_PATH))
sys.path.insert(0, str(SHARED_LAYER_PATH))

# Increase recursion limit for deeply nested DSL strategies (matches Lambda handler).
sys.setrecursionlimit(10000)

# CSV column schema (consumed by validate_signals.py)
CSV_FIELDS = [
    "validation_date",
    "strategy_name",
    "dsl_file",
    "our_signals",
    "generated_at",
]

# Tolerance for allocation sum validation
ALLOCATION_SUM_TOLERANCE = 0.02


def setup_logging(log_file: str | None = None) -> logging.Logger:
    """Configure logging for the signal generator.

    Args:
        log_file: Optional path to write logs to a file.

    Returns:
        Configured logger instance.

    """
    logger = logging.getLogger("generate_daily_signals")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_strategy_config(stage: str) -> dict[str, float]:
    """Load strategy config (files + allocations) from JSON.

    Args:
        stage: Environment stage ('dev' or 'prod').

    Returns:
        Dict mapping DSL filename to allocation weight.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If allocations do not sum to ~1.0.

    """
    config_file = CONFIG_PATH / f"strategy.{stage}.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Strategy config not found: {config_file}")

    with config_file.open() as f:
        config = json.load(f)

    files: list[str] = config.get("files", [])
    allocations: dict[str, float] = config.get("allocations", {})

    # Build mapping (only include files that have allocations)
    result: dict[str, float] = {}
    for dsl_file in files:
        alloc = allocations.get(dsl_file, 0.0)
        if alloc > 0:
            result[dsl_file] = alloc

    # Validate allocations sum
    total = sum(result.values())
    if abs(total - 1.0) > ALLOCATION_SUM_TOLERANCE:
        raise ValueError(f"Strategy allocations for {stage} sum to {total:.4f}, expected ~1.0")

    return result


def run_single_strategy(
    dsl_file: str,
    logger: logging.Logger,
) -> dict[str, float] | None:
    """Run a single strategy and return raw target weights (unscaled).

    Args:
        dsl_file: DSL strategy filename (e.g., 'gold.clj' or 'ftlt/tqqq_ftlt.clj').
        logger: Logger instance.

    Returns:
        Dict mapping symbol to weight (sums to 1.0), or None on failure.

    """
    from engines.dsl.engine import DslEngine

    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )

    # CachedMarketDataAdapter reads historical + today's completed bars from S3
    market_data_adapter = CachedMarketDataAdapter()

    engine = DslEngine(
        strategy_config_path=STRATEGIES_PATH,
        market_data_adapter=market_data_adapter,
        debug_mode=False,
    )

    correlation_id = f"local-signal-{dsl_file}"
    allocation, _trace = engine.evaluate_strategy(dsl_file, correlation_id)

    if not allocation or not allocation.target_weights:
        logger.warning("No target weights returned for %s", dsl_file)
        return None

    return {k: float(v) for k, v in allocation.target_weights.items()}


def get_output_path(validation_date: str, stage: str) -> Path:
    """Get output CSV path for a given date and stage.

    Args:
        validation_date: ISO date string (YYYY-MM-DD).
        stage: Environment stage ('dev' or 'prod').

    Returns:
        Path to output CSV file.

    """
    return OUTPUT_DIR / f"{validation_date}_{stage}.csv"


def generate_signals_for_stage(
    stage: str,
    validation_date: str,
    logger: logging.Logger,
) -> tuple[int, int]:
    """Generate signals for all strategies in a given stage.

    Args:
        stage: Environment stage ('dev' or 'prod').
        validation_date: ISO date string (YYYY-MM-DD).
        logger: Logger instance.

    Returns:
        Tuple of (success_count, error_count).

    """
    logger.info("Loading %s strategy config...", stage)
    strategies = load_strategy_config(stage)
    logger.info(
        "Loaded %d strategies for %s (total allocation: %.4f)",
        len(strategies),
        stage,
        sum(strategies.values()),
    )

    # Prepare output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = get_output_path(validation_date, stage)

    success_count = 0
    error_count = 0

    # Write CSV header + rows incrementally
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for i, (dsl_file, _allocation) in enumerate(strategies.items(), 1):
            # _allocation is the weight from strategy config, not used here
            # since we output raw (unscaled) strategy signals for validation
            strategy_name = dsl_file.replace(".clj", "")

            logger.info(
                "[%d/%d] Running %s...",
                i,
                len(strategies),
                strategy_name,
            )

            try:
                raw_signal = run_single_strategy(dsl_file, logger)

                if raw_signal is None:
                    logger.warning(
                        "[%d/%d] %s returned no signal",
                        i,
                        len(strategies),
                        strategy_name,
                    )
                    error_count += 1
                    continue

                # Format signal as JSON (sorted keys for deterministic output)
                signal_json = json.dumps(raw_signal, sort_keys=True)

                writer.writerow(
                    {
                        "validation_date": validation_date,
                        "strategy_name": strategy_name,
                        "dsl_file": dsl_file,
                        "our_signals": signal_json,
                        "generated_at": datetime.now(UTC).isoformat(),
                    }
                )

                # Log the signal
                symbols = ", ".join(f"{sym}={w:.2%}" for sym, w in sorted(raw_signal.items()))
                logger.info(
                    "[%d/%d] %s -> %s",
                    i,
                    len(strategies),
                    strategy_name,
                    symbols,
                )
                success_count += 1

            except Exception as e:
                logger.error(
                    "[%d/%d] %s FAILED: %s: %s",
                    i,
                    len(strategies),
                    strategy_name,
                    type(e).__name__,
                    e,
                )
                error_count += 1

    logger.info(
        "%s complete: %d/%d succeeded, %d errors -> %s",
        stage.upper(),
        success_count,
        success_count + error_count,
        error_count,
        output_path,
    )

    return success_count, error_count


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate daily strategy signals locally for validation",
    )
    parser.add_argument(
        "--stage",
        choices=["dev", "prod", "both"],
        default="both",
        help="Which strategy profile to run (default: both)",
    )
    parser.add_argument(
        "--log-file",
        help="Optional log file path (appends)",
    )
    parser.add_argument(
        "--date",
        help="Override validation date (YYYY-MM-DD). Default: today.",
    )

    args = parser.parse_args()

    logger = setup_logging(args.log_file)

    # Determine validation date
    validation_date = args.date or datetime.now(UTC).strftime("%Y-%m-%d")

    logger.info("=" * 70)
    logger.info("DAILY SIGNAL GENERATION -- %s", validation_date)
    logger.info("=" * 70)

    # Determine which stages to run
    stages: list[str] = []
    if args.stage == "both":
        stages = ["dev", "prod"]
    else:
        stages = [args.stage]

    total_success = 0
    total_errors = 0

    for stage in stages:
        logger.info("-" * 50)
        logger.info("Stage: %s", stage.upper())
        logger.info("-" * 50)

        try:
            success, errors = generate_signals_for_stage(
                stage,
                validation_date,
                logger,
            )
            total_success += success
            total_errors += errors
        except Exception as e:
            logger.error(
                "Failed to run %s stage: %s: %s",
                stage,
                type(e).__name__,
                e,
            )
            total_errors += 1

    # Summary
    logger.info("=" * 70)
    logger.info(
        "COMPLETE: %d succeeded, %d errors across %s",
        total_success,
        total_errors,
        ", ".join(stages),
    )
    for stage in stages:
        output_path = get_output_path(validation_date, stage)
        if output_path.exists():
            logger.info("  %s: %s", stage, output_path)
    logger.info("=" * 70)

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
