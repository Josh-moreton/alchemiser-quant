"""Business Unit: shared | Status: current.

Strategy weight management service with Calmar-tilted adjustments.

Implements the Calmar-tilt formula with caps, floors, smoothing, and partial adjustment
for slow capital migration. Manages base weights (from strategy.prod.json) and live
weights (adjusted monthly based on 12-month Calmar ratios).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.dynamodb_strategy_weights_repository import (
    DynamoDBStrategyWeightsRepository,
)
from the_alchemiser.shared.schemas.strategy_weights import CalmarMetrics, StrategyWeights

logger = get_logger(__name__)

__all__ = ["StrategyWeightService"]

# Calmar-tilt parameters (per design spec)
ALPHA = Decimal("0.5")  # Square-root dampening
F_MIN = Decimal("0.5")  # Minimum tilt factor (50% of base weight)
F_MAX = Decimal("2.0")  # Maximum tilt factor (200% of base weight)
DEFAULT_LAMBDA = Decimal("0.1")  # Partial adjustment rate
DEFAULT_REBALANCE_DAYS = 30  # Monthly rebalancing


class StrategyWeightService:
    """Service for managing strategy weights with Calmar-tilted adjustments.

    Responsibilities:
    - Load base weights from strategy.prod.json
    - Load/save live weights from/to DynamoDB
    - Compute Calmar-tilted target weights
    - Apply partial adjustment smoothing
    - Track rebalancing schedule
    """

    def __init__(self, repository: DynamoDBStrategyWeightsRepository) -> None:
        """Initialize service.

        Args:
            repository: DynamoDB repository for strategy weights

        """
        self._repo = repository
        logger.debug("Initialized StrategyWeightService")

    def get_current_weights(
        self, base_weights: dict[str, float], correlation_id: str
    ) -> dict[str, Decimal]:
        """Get current live weights, falling back to base weights if not initialized.

        Args:
            base_weights: Base weights from strategy.prod.json
            correlation_id: Correlation ID for traceability

        Returns:
            Dictionary of realized weights by strategy name

        """
        weights = self._repo.get_current_weights()

        if weights is None:
            logger.info(
                "No live weights found, returning base weights",
                strategy_count=len(base_weights),
                correlation_id=correlation_id,
            )
            # Convert to Decimal for consistency
            return {k: Decimal(str(v)) for k, v in base_weights.items()}

        logger.info(
            "Loaded live weights from DynamoDB",
            version=weights.version,
            strategy_count=len(weights.realized_weights),
            correlation_id=correlation_id,
        )
        return weights.realized_weights

    def initialize_weights(
        self,
        base_weights: dict[str, float],
        initial_calmar_metrics: dict[str, dict[str, float]],
        correlation_id: str,
    ) -> StrategyWeights:
        """Initialize strategy weights from base configuration.

        Used for first-time setup or reset.

        Args:
            base_weights: Base weights from strategy.prod.json
            initial_calmar_metrics: Initial Calmar metrics by strategy name
            correlation_id: Correlation ID for traceability

        Returns:
            Initialized StrategyWeights

        """
        logger.info(
            "Initializing strategy weights",
            strategy_count=len(base_weights),
            correlation_id=correlation_id,
        )

        weights = self._repo.initialize_weights_from_base(
            base_weights=base_weights,
            initial_calmar_metrics=initial_calmar_metrics,
            correlation_id=correlation_id,
        )

        logger.info(
            "Strategy weights initialized successfully",
            version=weights.version,
            correlation_id=correlation_id,
        )
        return weights

    def should_rebalance(self) -> tuple[bool, str | None]:
        """Check if weights should be rebalanced.

        Returns:
            Tuple of (should_rebalance, reason)

        """
        weights = self._repo.get_current_weights()

        if weights is None:
            return False, "no_weights_initialized"

        if weights.next_rebalance is None:
            return True, "no_next_rebalance_set"

        now = datetime.now(UTC)
        if now >= weights.next_rebalance:
            days_since = (now - weights.last_rebalance).days if weights.last_rebalance else 0
            return True, f"scheduled_rebalance_after_{days_since}_days"

        return False, None

    def rebalance_weights(
        self,
        updated_calmar_metrics: dict[str, CalmarMetrics],
        correlation_id: str,
        adjustment_lambda: Decimal | None = None,
    ) -> StrategyWeights:
        """Rebalance strategy weights using updated Calmar metrics.

        Applies the Calmar-tilt formula:
        1. Compute tilt factors from Calmar ratios
        2. Apply caps and floors
        3. Normalize to sum = 1.0
        4. Apply partial adjustment smoothing

        Args:
            updated_calmar_metrics: Updated Calmar metrics by strategy name
            correlation_id: Correlation ID for traceability
            adjustment_lambda: Optional override for partial adjustment rate

        Returns:
            Updated StrategyWeights

        """
        current_weights = self._repo.get_current_weights()

        if current_weights is None:
            raise ValueError("Cannot rebalance: no current weights found. Initialize first.")

        # Use provided lambda or default from current weights
        lambda_value = adjustment_lambda or current_weights.adjustment_lambda

        # Compute new target weights using Calmar-tilt formula
        target_weights = self._compute_target_weights(
            base_weights=current_weights.base_weights,
            calmar_metrics=updated_calmar_metrics,
        )

        # Apply partial adjustment: w_new = w_old + λ × (w_target − w_old)
        realized_weights = self._apply_partial_adjustment(
            current_realized=current_weights.realized_weights,
            target=target_weights,
            lambda_value=lambda_value,
        )

        # Create updated weights
        now = datetime.now(UTC)
        next_rebalance = now + timedelta(days=current_weights.rebalance_frequency_days)

        # Increment version
        version_num = int(current_weights.version.lstrip("v")) + 1
        new_version = f"v{version_num}"

        updated_weights = StrategyWeights(
            version=new_version,
            base_weights=current_weights.base_weights,  # Base weights never change
            target_weights=target_weights,
            realized_weights=realized_weights,
            calmar_metrics=updated_calmar_metrics,
            adjustment_lambda=lambda_value,
            rebalance_frequency_days=current_weights.rebalance_frequency_days,
            last_rebalance=now,
            next_rebalance=next_rebalance,
            created_at=current_weights.created_at,  # Keep original creation time
            updated_at=now,
        )

        # Save to DynamoDB
        self._repo.put_current_weights(
            updated_weights, correlation_id=correlation_id, reason="monthly_rebalance"
        )

        logger.info(
            "Strategy weights rebalanced successfully",
            version=new_version,
            next_rebalance=next_rebalance.isoformat(),
            correlation_id=correlation_id,
        )

        return updated_weights

    def _compute_target_weights(
        self,
        base_weights: dict[str, Decimal],
        calmar_metrics: dict[str, CalmarMetrics],
    ) -> dict[str, Decimal]:
        """Compute target weights using Calmar-tilt formula.

        Formula:
        w_i = Normalise(w_base × clip((Calmar_i / MedianCalmar)^α, f_min, f_max))

        Args:
            base_weights: Base weights from strategy.prod.json
            calmar_metrics: Calmar metrics by strategy name

        Returns:
            Dictionary of target weights by strategy name

        """
        # Extract Calmar ratios
        calmar_ratios = {k: v.calmar_ratio for k, v in calmar_metrics.items()}

        # Compute median Calmar for shrinkage
        sorted_calmars = sorted(calmar_ratios.values())
        n = len(sorted_calmars)
        if n == 0:
            raise ValueError("No Calmar ratios provided")

        if n % 2 == 0:
            median_calmar = (sorted_calmars[n // 2 - 1] + sorted_calmars[n // 2]) / Decimal("2")
        else:
            median_calmar = sorted_calmars[n // 2]

        logger.debug(
            "Computing Calmar-tilted target weights",
            median_calmar=float(median_calmar),
            strategy_count=len(base_weights),
        )

        # Compute tilt factors for each strategy
        tilt_factors: dict[str, Decimal] = {}
        for strategy_name, base_weight in base_weights.items():
            calmar = calmar_ratios.get(strategy_name)

            if calmar is None:
                logger.warning(
                    "Missing Calmar ratio for strategy, using base weight",
                    strategy=strategy_name,
                )
                tilt_factors[strategy_name] = Decimal("1.0")
                continue

            # Compute tilt: (Calmar_i / MedianCalmar)^α
            if median_calmar == 0:
                ratio = Decimal("1.0")
            else:
                ratio = calmar / median_calmar

            # Apply square-root dampening (α = 0.5)
            # Convert to float for pow, then back to Decimal
            tilt = Decimal(str(float(ratio) ** float(ALPHA)))

            # Apply caps and floors
            tilt_clamped = max(F_MIN, min(F_MAX, tilt))

            tilt_factors[strategy_name] = tilt_clamped

            logger.debug(
                "Computed tilt factor",
                strategy=strategy_name,
                calmar=float(calmar),
                tilt_raw=float(tilt),
                tilt_clamped=float(tilt_clamped),
            )

        # Apply tilt to base weights
        tilted_weights = {
            strategy: base_weights[strategy] * tilt_factors[strategy]
            for strategy in base_weights
        }

        # Normalize to sum = 1.0
        total = sum(tilted_weights.values())
        if total == 0:
            raise ValueError("Total tilted weight is zero, cannot normalize")

        normalized_weights = {k: v / total for k, v in tilted_weights.items()}

        # Validate sum using math.isclose (per coding guidelines)
        total_normalized = float(sum(normalized_weights.values()))
        if not math.isclose(total_normalized, 1.0, rel_tol=0.01):
            logger.error(
                "Normalized weights do not sum to 1.0",
                total=total_normalized,
                weights=normalized_weights,
            )
            raise ValueError(f"Normalized weights sum to {total_normalized}, expected 1.0")

        logger.info(
            "Target weights computed successfully",
            strategy_count=len(normalized_weights),
            median_calmar=float(median_calmar),
        )

        return normalized_weights

    def _apply_partial_adjustment(
        self,
        current_realized: dict[str, Decimal],
        target: dict[str, Decimal],
        lambda_value: Decimal,
    ) -> dict[str, Decimal]:
        """Apply partial adjustment smoothing to prevent abrupt weight changes.

        Formula: w_new = w_old + λ × (w_target − w_old)

        Args:
            current_realized: Current realized weights
            target: Target weights from Calmar tilt
            lambda_value: Partial adjustment rate (0.1-0.25 recommended)

        Returns:
            Dictionary of new realized weights after partial adjustment

        """
        realized: dict[str, Decimal] = {}

        for strategy_name, target_weight in target.items():
            current_weight = current_realized.get(strategy_name, target_weight)
            adjustment = lambda_value * (target_weight - current_weight)
            new_weight = current_weight + adjustment
            realized[strategy_name] = new_weight

            logger.debug(
                "Applied partial adjustment",
                strategy=strategy_name,
                current=float(current_weight),
                target=float(target_weight),
                adjustment=float(adjustment),
                realized=float(new_weight),
            )

        # Normalize to sum = 1.0 (may have small rounding errors)
        total = sum(realized.values())
        if total > 0:
            realized = {k: v / total for k, v in realized.items()}

        # Validate sum
        total_realized = float(sum(realized.values()))
        if not math.isclose(total_realized, 1.0, rel_tol=0.01):
            logger.error(
                "Realized weights do not sum to 1.0", total=total_realized, weights=realized
            )
            raise ValueError(f"Realized weights sum to {total_realized}, expected 1.0")

        logger.info(
            "Partial adjustment applied successfully",
            lambda_value=float(lambda_value),
            strategy_count=len(realized),
        )

        return realized

    def get_version_history(self, limit: int = 10) -> list[Any]:
        """Get version history of strategy weights.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of StrategyWeightsHistory entries, newest first

        """
        return self._repo.get_version_history(limit=limit)
