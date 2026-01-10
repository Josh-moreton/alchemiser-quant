"""Business Unit: strategy_weighting | Status: current.

Lambda handler for dynamic strategy weight adjustment microservice.

Calculates per-strategy Sharpe ratios from trade history and adjusts strategy
allocations to tilt capital toward better risk-adjusted performers.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any
from uuid import uuid4

from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.repositories.dynamodb_strategy_weights_repository import (
    DynamoDBStrategyWeightsRepository,
)
from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.services.sharpe_calculator import SharpeCalculator

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)

# Weight adjustment constraints
MIN_WEIGHT_MULTIPLIER = Decimal("0.5")  # 50% of baseline (halving)
MAX_WEIGHT_MULTIPLIER = Decimal("2.0")  # 200% of baseline (doubling)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Adjust strategy weights based on recent Sharpe ratios.

    This Lambda runs on a weekly schedule and:
    1. Reads baseline strategy allocations from config
    2. Calculates per-strategy Sharpe ratios from trade history
    3. Adjusts weights to favor higher Sharpe strategies
    4. Stores dynamic weights in DynamoDB (with constraints)

    Args:
        event: EventBridge scheduled event
        context: Lambda context

    Returns:
        Response with status code and adjustment summary

    """
    correlation_id = str(uuid4())

    try:
        logger.info(
            "Strategy weighting Lambda invoked",
            extra={"correlation_id": correlation_id, "event": event},
        )

        # Get configuration from environment
        trade_ledger_table = os.environ.get("TRADE_LEDGER__TABLE_NAME")
        weights_table = os.environ.get("STRATEGY_WEIGHTS__TABLE_NAME")
        lookback_days = int(os.environ.get("LOOKBACK_DAYS", "90"))
        stage = os.environ.get("APP__STAGE", "dev")

        if not trade_ledger_table or not weights_table:
            logger.error(
                "Missing required environment variables",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 500,
                "body": "Configuration error: missing table names",
            }

        # Initialize repositories
        ledger_repo = DynamoDBTradeLedgerRepository(trade_ledger_table)
        weights_repo = DynamoDBStrategyWeightsRepository(weights_table)

        # Load baseline allocations from config
        from the_alchemiser.shared.config.strategy_profiles import get_strategy_profile

        profile = get_strategy_profile(stage)
        baseline_allocations = profile.allocations

        logger.info(
            f"Loaded baseline allocations for {len(baseline_allocations)} strategies",
            extra={"correlation_id": correlation_id, "stage": stage},
        )

        # Calculate Sharpe ratios for each strategy
        sharpe_calculator = SharpeCalculator(ledger_repo, lookback_days=lookback_days)
        sharpe_ratios = sharpe_calculator.calculate_all_strategy_sharpes(correlation_id)

        if not sharpe_ratios:
            logger.warning(
                "No Sharpe ratios calculated - insufficient trade history",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 200,
                "body": "No weight adjustments - insufficient trade history",
            }

        # Calculate dynamic weight multipliers based on Sharpe ratios
        weight_multipliers = _calculate_weight_multipliers(sharpe_ratios, correlation_id)

        # Apply multipliers to baseline allocations with constraints
        dynamic_weights = _apply_weight_adjustments(
            baseline_allocations, weight_multipliers, correlation_id
        )

        # Store dynamic weights in DynamoDB
        weights_repo.put_dynamic_weights(
            weights=dynamic_weights,
            sharpe_ratios=sharpe_ratios,
            baseline_allocations=baseline_allocations,
            correlation_id=correlation_id,
        )

        logger.info(
            "Dynamic weights updated successfully",
            extra={
                "correlation_id": correlation_id,
                "strategy_count": len(dynamic_weights),
                "adjustments": {
                    k: f"{v / baseline_allocations.get(k, Decimal('1.0')):.2f}x"
                    for k, v in dynamic_weights.items()
                },
            },
        )

        return {
            "statusCode": 200,
            "body": f"Dynamic weights updated for {len(dynamic_weights)} strategies",
            "correlation_id": correlation_id,
        }

    except Exception as e:
        logger.error(
            f"Strategy weighting Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return {
            "statusCode": 500,
            "body": f"Weight adjustment failed: {e!s}",
        }


def _calculate_weight_multipliers(
    sharpe_ratios: dict[str, Decimal], correlation_id: str
) -> dict[str, Decimal]:
    """Calculate weight multipliers based on Sharpe ratio rankings.

    Strategies with higher Sharpe ratios receive higher multipliers,
    with constraints to prevent extreme tilts.

    Args:
        sharpe_ratios: Dict mapping strategy name to Sharpe ratio
        correlation_id: Correlation ID for tracing

    Returns:
        Dict mapping strategy name to weight multiplier (0.5 to 2.0)

    """
    if not sharpe_ratios:
        return {}

    # Sort strategies by Sharpe ratio (descending)
    sorted_strategies = sorted(sharpe_ratios.items(), key=lambda x: x[1], reverse=True)

    # Normalize Sharpe ratios to [0, 1] range
    min_sharpe = min(sharpe_ratios.values())
    max_sharpe = max(sharpe_ratios.values())
    sharpe_range = max_sharpe - min_sharpe

    weight_multipliers = {}

    if sharpe_range == Decimal("0"):
        # All strategies have same Sharpe - no adjustment
        logger.info(
            "All strategies have equal Sharpe ratios - no weight adjustments",
            extra={"correlation_id": correlation_id},
        )
        for strategy_name in sharpe_ratios:
            weight_multipliers[strategy_name] = Decimal("1.0")
    else:
        # Map normalized Sharpe to multiplier range [0.5, 2.0]
        for strategy_name, sharpe in sorted_strategies:
            normalized_sharpe = (sharpe - min_sharpe) / sharpe_range
            # Linear mapping: 0 -> 0.5x, 1 -> 2.0x
            multiplier = MIN_WEIGHT_MULTIPLIER + normalized_sharpe * (
                MAX_WEIGHT_MULTIPLIER - MIN_WEIGHT_MULTIPLIER
            )
            weight_multipliers[strategy_name] = multiplier

            logger.debug(
                f"Strategy {strategy_name}: Sharpe={sharpe:.3f}, multiplier={multiplier:.2f}x",
                extra={"correlation_id": correlation_id},
            )

    return weight_multipliers


def _apply_weight_adjustments(
    baseline_allocations: dict[str, Decimal],
    weight_multipliers: dict[str, Decimal],
    correlation_id: str,
) -> dict[str, Decimal]:
    """Apply weight multipliers to baseline allocations and renormalize.

    Args:
        baseline_allocations: Dict mapping strategy name to baseline allocation (0-1)
        weight_multipliers: Dict mapping strategy name to multiplier (0.5-2.0)
        correlation_id: Correlation ID for tracing

    Returns:
        Dict mapping strategy name to adjusted allocation (renormalized to sum to 1.0)

    """
    # Apply multipliers
    adjusted_weights = {}
    for strategy_name, baseline_weight in baseline_allocations.items():
        multiplier = weight_multipliers.get(strategy_name, Decimal("1.0"))
        adjusted_weights[strategy_name] = baseline_weight * multiplier

    # Renormalize to sum to 1.0
    total_weight = sum(adjusted_weights.values())

    if total_weight == Decimal("0"):
        logger.error(
            "Total adjusted weight is zero - cannot renormalize",
            extra={"correlation_id": correlation_id},
        )
        return baseline_allocations

    dynamic_weights = {
        strategy_name: weight / total_weight for strategy_name, weight in adjusted_weights.items()
    }

    logger.info(
        "Weight adjustments applied and renormalized",
        extra={
            "correlation_id": correlation_id,
            "original_sum": float(sum(baseline_allocations.values())),
            "adjusted_sum": float(sum(dynamic_weights.values())),
        },
    )

    return dynamic_weights
