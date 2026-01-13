#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Strategy Weights Management CLI.

CLI tool for managing strategy weights with Calmar-tilted adjustments. Allows
initializing weights from base configuration with starter Calmar ratios, viewing
current weights, and forcing rebalancing.

Usage:
    python scripts/strategy_weights.py init --config strategy.prod.json --calmar starter_calmar.json
    python scripts/strategy_weights.py show --stage dev
    python scripts/strategy_weights.py show --stage prod
    python scripts/strategy_weights.py rebalance --stage prod --calmar updated_calmar.json
    python scripts/strategy_weights.py history --stage dev --limit 5

The 'init' command will:
    - Read base weights from strategy config JSON
    - Read initial Calmar metrics from starter_calmar.json
    - Initialize DynamoDB with base weights and Calmar metrics
    - Set realized weights = target weights = base weights (no tilt on first init)

The 'show' command displays current live weights from DynamoDB.

The 'rebalance' command applies Calmar-tilt formula with updated metrics.

The 'history' command shows version history of weight adjustments.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Setup PYTHONPATH for shared layer imports
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent
        / "layers"
        / "shared"
    ),
)

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.repositories.dynamodb_strategy_weights_repository import (
    DynamoDBStrategyWeightsRepository,
)
from the_alchemiser.shared.schemas.strategy_weights import CalmarMetrics
from the_alchemiser.shared.services.strategy_weight_service import StrategyWeightService

# Initialize logging
configure_application_logging()
logger = get_logger(__name__)

CONFIG_DIR = (
    Path(__file__).parent.parent
    / "layers"
    / "shared"
    / "the_alchemiser"
    / "shared"
    / "config"
)


def load_json_file(filepath: str) -> dict[str, Any]:
    """Load JSON file."""
    path = Path(filepath)
    if not path.exists():
        # Try relative to CONFIG_DIR
        path = CONFIG_DIR / filepath
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_table_name(stage: str) -> str:
    """Get DynamoDB table name for stage."""
    # Construct table name following SAM template pattern
    return f"alchemiser-{stage}-strategy-weights"


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize strategy weights from base configuration."""
    correlation_id = f"init-{uuid.uuid4()}"

    # Load base weights from strategy config
    config_data = load_json_file(args.config)
    base_allocations = config_data.get("allocations", {})

    if not base_allocations:
        logger.error("No allocations found in config file")
        sys.exit(1)

    logger.info(
        "Loaded base allocations",
        extra={"config": args.config, "strategy_count": len(base_allocations)},
    )

    # Load initial Calmar metrics
    calmar_data = load_json_file(args.calmar)

    if not calmar_data:
        logger.error("No Calmar metrics found in file")
        sys.exit(1)

    logger.info(
        "Loaded starter Calmar metrics",
        extra={"calmar_file": args.calmar, "strategy_count": len(calmar_data)},
    )

    # Validate that all strategies have Calmar metrics
    missing = set(base_allocations.keys()) - set(calmar_data.keys())
    if missing:
        logger.error(
            "Missing Calmar metrics for strategies",
            extra={"missing": list(missing)},
        )
        sys.exit(1)

    # Initialize service
    table_name = get_table_name(args.stage)
    repo = DynamoDBStrategyWeightsRepository(table_name=table_name)
    service = StrategyWeightService(repository=repo)

    # Initialize weights
    try:
        weights = service.initialize_weights(
            base_weights=base_allocations,
            initial_calmar_metrics=calmar_data,
            correlation_id=correlation_id,
        )

        print(f"\n✅ Strategy weights initialized successfully")
        print(f"Version: {weights.version}")
        print(f"Stage: {args.stage}")
        print(f"Table: {table_name}")
        print(f"\nBase Weights:")
        for strategy, weight in sorted(weights.base_weights.items()):
            print(f"  {strategy}: {float(weight):.4f} ({float(weight)*100:.2f}%)")

        print(f"\nCalmar Ratios:")
        for strategy, metrics in sorted(weights.calmar_metrics.items()):
            print(
                f"  {strategy}: {float(metrics.calmar_ratio):.4f} "
                f"(return={float(metrics.twelve_month_return)*100:.2f}%, "
                f"mdd={float(metrics.twelve_month_max_drawdown)*100:.2f}%)"
            )

        print(f"\n🔄 Next rebalance: {weights.next_rebalance.isoformat() if weights.next_rebalance else 'Not set'}")

    except Exception as e:
        logger.error("Failed to initialize weights", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    """Show current strategy weights."""
    table_name = get_table_name(args.stage)
    repo = DynamoDBStrategyWeightsRepository(table_name=table_name)

    try:
        weights = repo.get_current_weights()

        if weights is None:
            print(f"\n⚠️  No strategy weights found for stage: {args.stage}")
            print(f"Run 'python scripts/strategy_weights.py init' to initialize.")
            return

        print(f"\n📊 Current Strategy Weights")
        print(f"Version: {weights.version}")
        print(f"Stage: {args.stage}")
        print(f"Last Rebalance: {weights.last_rebalance.isoformat() if weights.last_rebalance else 'Never'}")
        print(f"Next Rebalance: {weights.next_rebalance.isoformat() if weights.next_rebalance else 'Not set'}")

        print(f"\n{'Strategy':<30} {'Base':<10} {'Target':<10} {'Realized':<10} {'Calmar':<10}")
        print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

        for strategy in sorted(weights.base_weights.keys()):
            base_w = float(weights.base_weights[strategy])
            target_w = float(weights.target_weights[strategy])
            realized_w = float(weights.realized_weights[strategy])
            calmar = (
                float(weights.calmar_metrics[strategy].calmar_ratio)
                if strategy in weights.calmar_metrics
                else 0.0
            )

            print(
                f"{strategy:<30} {base_w:<10.4f} {target_w:<10.4f} {realized_w:<10.4f} {calmar:<10.4f}"
            )

        print(f"\nAdjustment λ: {float(weights.adjustment_lambda):.2f}")
        print(f"Rebalance Frequency: {weights.rebalance_frequency_days} days")

    except Exception as e:
        logger.error("Failed to retrieve weights", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


def cmd_rebalance(args: argparse.Namespace) -> None:
    """Force rebalance with updated Calmar metrics."""
    correlation_id = f"rebalance-{uuid.uuid4()}"

    # Load updated Calmar metrics
    calmar_data = load_json_file(args.calmar)

    if not calmar_data:
        logger.error("No Calmar metrics found in file")
        sys.exit(1)

    # Convert to CalmarMetrics DTOs
    now = datetime.now(UTC)
    calmar_metrics: dict[str, CalmarMetrics] = {}
    for strategy_name, metrics in calmar_data.items():
        calmar_metrics[strategy_name] = CalmarMetrics(
            strategy_name=strategy_name,
            twelve_month_return=Decimal(str(metrics["twelve_month_return"])),
            twelve_month_max_drawdown=Decimal(str(metrics["twelve_month_max_drawdown"])),
            calmar_ratio=Decimal(str(metrics["calmar_ratio"])),
            months_of_data=int(metrics.get("months_of_data", 12)),
            as_of=now,
        )

    # Initialize service
    table_name = get_table_name(args.stage)
    repo = DynamoDBStrategyWeightsRepository(table_name=table_name)
    service = StrategyWeightService(repository=repo)

    # Rebalance
    try:
        weights = service.rebalance_weights(
            updated_calmar_metrics=calmar_metrics,
            correlation_id=correlation_id,
        )

        print(f"\n✅ Strategy weights rebalanced successfully")
        print(f"Version: {weights.version}")
        print(f"Stage: {args.stage}")

        print(f"\n{'Strategy':<30} {'Base':<10} {'Target':<10} {'Realized':<10} {'Δ Target':<10}")
        print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

        for strategy in sorted(weights.base_weights.keys()):
            base_w = float(weights.base_weights[strategy])
            target_w = float(weights.target_weights[strategy])
            realized_w = float(weights.realized_weights[strategy])
            delta = target_w - base_w

            print(
                f"{strategy:<30} {base_w:<10.4f} {target_w:<10.4f} {realized_w:<10.4f} {delta:<+10.4f}"
            )

        print(f"\n🔄 Next rebalance: {weights.next_rebalance.isoformat()}")

    except Exception as e:
        logger.error("Failed to rebalance weights", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


def cmd_history(args: argparse.Namespace) -> None:
    """Show version history of weight adjustments."""
    table_name = get_table_name(args.stage)
    repo = DynamoDBStrategyWeightsRepository(table_name=table_name)

    try:
        history = repo.get_version_history(limit=args.limit)

        if not history:
            print(f"\n⚠️  No weight history found for stage: {args.stage}")
            return

        print(f"\n📜 Strategy Weights History (last {len(history)} versions)")
        print(f"Stage: {args.stage}\n")

        for entry in history:
            print(f"Version: {entry.version}")
            print(f"  Reason: {entry.reason}")
            print(f"  Created: {entry.created_at.isoformat()}")
            print(f"  Correlation ID: {entry.correlation_id}")
            print(f"  Weights (realized):")
            for strategy, weight in sorted(entry.weights.realized_weights.items()):
                print(f"    {strategy}: {float(weight):.4f}")
            print()

    except Exception as e:
        logger.error("Failed to retrieve history", extra={"error": str(e)}, exc_info=True)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage strategy weights with Calmar-tilted adjustments"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize weights from base configuration")
    init_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Strategy config JSON file (e.g., strategy.prod.json)",
    )
    init_parser.add_argument(
        "--calmar",
        type=str,
        required=True,
        help="Initial Calmar metrics JSON file",
    )
    init_parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Deployment stage",
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show current strategy weights")
    show_parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Deployment stage",
    )

    # Rebalance command
    rebalance_parser = subparsers.add_parser("rebalance", help="Force rebalance with updated Calmar metrics")
    rebalance_parser.add_argument(
        "--calmar",
        type=str,
        required=True,
        help="Updated Calmar metrics JSON file",
    )
    rebalance_parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Deployment stage",
    )

    # History command
    history_parser = subparsers.add_parser("history", help="Show version history of weight adjustments")
    history_parser.add_argument(
        "--stage",
        type=str,
        default="dev",
        choices=["dev", "staging", "prod"],
        help="Deployment stage",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of versions to show",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "init":
        cmd_init(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "rebalance":
        cmd_rebalance(args)
    elif args.command == "history":
        cmd_history(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
