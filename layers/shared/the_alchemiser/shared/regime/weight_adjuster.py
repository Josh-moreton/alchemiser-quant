"""Business Unit: shared | Status: current.

Regime-based strategy weight adjuster.

This module adjusts strategy allocations based on the current market regime
and per-strategy Sharpe ratios within each regime. Uses inverse-variance
weighted Sharpe allocation (industry standard) with configurable constraints.

Weight Adjustment Methods:
1. sharpe_weighted: Allocate proportional to Sharpe ratio (normalized)
2. multiplier: Apply pre-configured multipliers per regime
3. hybrid: Blend both approaches

The adjuster enforces:
- Minimum weight floor (prevents zero allocation)
- Maximum weight cap (prevents concentration)
- Sharpe floor (negative Sharpe = no allocation)
- Normalization to sum to 1.0
"""

from __future__ import annotations

import json
import math
from decimal import ROUND_HALF_UP, Decimal
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any

from .schemas import RegimeState, RegimeType, RegimeWeightConfig, StrategyRegimeMetrics


class RegimeWeightAdjuster:
    """Adjusts strategy weights based on current market regime.

    This service reads base allocations from strategy config and adjusts
    them based on the current regime and per-strategy Sharpe ratios.

    Example:
        adjuster = RegimeWeightAdjuster.from_config()
        base_allocs = {"simons_kmlm.clj": Decimal("0.16"), ...}
        regime = RegimeState(regime=RegimeType.RISK_ON, ...)
        adjusted = adjuster.compute_adjusted_allocations(base_allocs, regime)

    """

    # Quantization for weight rounding
    WEIGHT_QUANTIZE = Decimal("0.0001")

    def __init__(self, config: RegimeWeightConfig) -> None:
        """Initialize with regime weight configuration.

        Args:
            config: Configuration with per-strategy metrics and constraints

        """
        self.config = config

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> RegimeWeightAdjuster:
        """Load configuration from a JSON file.

        Args:
            config_path: Path to regime_weights.json file

        Returns:
            Configured RegimeWeightAdjuster instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If JSON is malformed

        """
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls._from_dict(data)

    @classmethod
    def from_packaged_config(cls, filename: str = "regime_weights.json") -> RegimeWeightAdjuster:
        """Load configuration from packaged JSON file.

        Args:
            filename: Config filename in the_alchemiser.shared.config package

        Returns:
            Configured RegimeWeightAdjuster instance

        """
        package = "the_alchemiser.shared.config"
        try:
            cfg_path = importlib_resources.files(package).joinpath(filename)
            with cfg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return cls._from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file not found
            return cls(RegimeWeightConfig())

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> RegimeWeightAdjuster:
        """Create instance from parsed JSON dictionary.

        Args:
            data: Parsed JSON data

        Returns:
            Configured RegimeWeightAdjuster instance

        """
        # Parse strategies
        strategies_raw = data.get("strategies", {})
        strategies: dict[str, StrategyRegimeMetrics] = {}

        for strategy_file, metrics in strategies_raw.items():
            strategies[strategy_file] = StrategyRegimeMetrics(
                strategy_file=strategy_file,
                sharpe_by_regime=metrics.get("sharpe_by_regime", {}),
                weight_multiplier_by_regime=metrics.get("weight_multiplier_by_regime", {}),
                sample_days_by_regime=metrics.get("sample_days_by_regime", {}),
            )

        config = RegimeWeightConfig(
            strategies=strategies,
            adjustment_method=data.get("adjustment_method", "sharpe_weighted"),
            min_weight=Decimal(str(data.get("min_weight", "0.02"))),
            max_weight=Decimal(str(data.get("max_weight", "0.40"))),
            sharpe_floor=Decimal(str(data.get("sharpe_floor", "0.0"))),
            enable_regime_adjustment=data.get("enable_regime_adjustment", True),
        )

        return cls(config)

    def compute_adjusted_allocations(
        self,
        base_allocations: dict[str, Decimal],
        regime_state: RegimeState,
    ) -> dict[str, Decimal]:
        """Compute regime-adjusted strategy allocations.

        Args:
            base_allocations: Original allocations from strategy config (file -> weight)
            regime_state: Current market regime from detector

        Returns:
            Adjusted allocations normalized to sum to 1.0

        """
        if not self.config.enable_regime_adjustment:
            return base_allocations

        current_regime = regime_state.regime
        method = self.config.adjustment_method

        if method == "multiplier":
            return self._apply_multiplier_adjustment(base_allocations, current_regime)
        elif method == "hybrid":
            return self._apply_hybrid_adjustment(base_allocations, current_regime)
        else:  # sharpe_weighted (default)
            return self._apply_sharpe_weighted_adjustment(base_allocations, current_regime)

    def _apply_sharpe_weighted_adjustment(
        self,
        base_allocations: dict[str, Decimal],
        current_regime: RegimeType,
    ) -> dict[str, Decimal]:
        """Apply Sharpe-weighted allocation adjustment.

        Strategies with higher Sharpe in the current regime get more allocation.
        Uses inverse-variance weighting where weight ∝ max(0, Sharpe - floor).

        Args:
            base_allocations: Original allocations
            current_regime: Current market regime

        Returns:
            Sharpe-weighted allocations

        """
        # Collect Sharpe ratios for current regime
        sharpe_values: dict[str, Decimal] = {}
        for strategy_file in base_allocations:
            if strategy_file in self.config.strategies:
                metrics = self.config.strategies[strategy_file]
                sharpe = metrics.sharpe_by_regime.get(current_regime, Decimal("0.5"))
            else:
                # Unknown strategy - use neutral Sharpe of 0.5
                sharpe = Decimal("0.5")

            # Apply floor - negative/low Sharpe gets floored
            adjusted_sharpe = max(Decimal("0"), sharpe - self.config.sharpe_floor)
            sharpe_values[strategy_file] = adjusted_sharpe

        # If all Sharpe values are zero, fall back to base allocations
        total_sharpe = sum(sharpe_values.values())
        if total_sharpe <= Decimal("0"):
            return self._normalize_allocations(base_allocations)

        # Compute Sharpe-weighted allocations
        raw_weights: dict[str, Decimal] = {}
        for strategy_file, sharpe in sharpe_values.items():
            # Blend with base allocation: 50% Sharpe-based, 50% base
            base_weight = base_allocations[strategy_file]
            sharpe_weight = sharpe / total_sharpe
            blended = (base_weight + sharpe_weight) / Decimal("2")
            raw_weights[strategy_file] = blended

        return self._apply_constraints_and_normalize(raw_weights)

    def _apply_multiplier_adjustment(
        self,
        base_allocations: dict[str, Decimal],
        current_regime: RegimeType,
    ) -> dict[str, Decimal]:
        """Apply pre-configured multiplier adjustment.

        Each strategy has a weight multiplier per regime. A multiplier of 1.0
        means no change, 1.5 means 50% more allocation, 0.5 means half.

        Args:
            base_allocations: Original allocations
            current_regime: Current market regime

        Returns:
            Multiplier-adjusted allocations

        """
        adjusted: dict[str, Decimal] = {}

        for strategy_file, base_weight in base_allocations.items():
            multiplier = Decimal("1.0")  # Default: no change

            if strategy_file in self.config.strategies:
                metrics = self.config.strategies[strategy_file]
                multiplier = metrics.weight_multiplier_by_regime.get(
                    current_regime, Decimal("1.0")
                )

            adjusted[strategy_file] = base_weight * multiplier

        return self._apply_constraints_and_normalize(adjusted)

    def _apply_hybrid_adjustment(
        self,
        base_allocations: dict[str, Decimal],
        current_regime: RegimeType,
    ) -> dict[str, Decimal]:
        """Apply hybrid adjustment: Sharpe-weighted with multiplier overlay.

        First applies Sharpe weighting, then applies regime multipliers.
        This allows both data-driven and expert-tuned adjustments.

        Args:
            base_allocations: Original allocations
            current_regime: Current market regime

        Returns:
            Hybrid-adjusted allocations

        """
        # First pass: Sharpe weighting
        sharpe_adjusted = self._apply_sharpe_weighted_adjustment(
            base_allocations, current_regime
        )

        # Second pass: Multiplier overlay
        return self._apply_multiplier_adjustment(sharpe_adjusted, current_regime)

    def _apply_constraints_and_normalize(
        self,
        weights: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        """Apply min/max constraints and normalize to sum to 1.0.

        Args:
            weights: Raw weight values

        Returns:
            Constrained and normalized weights

        """
        # Apply min/max constraints
        constrained: dict[str, Decimal] = {}
        for strategy_file, weight in weights.items():
            constrained_weight = max(self.config.min_weight, min(self.config.max_weight, weight))
            constrained[strategy_file] = constrained_weight

        return self._normalize_allocations(constrained)

    def _normalize_allocations(
        self,
        allocations: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        """Normalize allocations to sum to 1.0.

        Args:
            allocations: Raw allocations

        Returns:
            Normalized allocations summing to 1.0

        """
        total = sum(allocations.values())

        if total <= Decimal("0"):
            # Edge case: all weights are zero - equal weight fallback
            n = len(allocations)
            if n == 0:
                return {}
            equal_weight = (Decimal("1") / Decimal(n)).quantize(
                self.WEIGHT_QUANTIZE, rounding=ROUND_HALF_UP
            )
            return {k: equal_weight for k in allocations}

        normalized: dict[str, Decimal] = {}
        for strategy_file, weight in allocations.items():
            norm_weight = (weight / total).quantize(
                self.WEIGHT_QUANTIZE, rounding=ROUND_HALF_UP
            )
            normalized[strategy_file] = norm_weight

        # Adjust for rounding errors - ensure sum is exactly 1.0
        current_sum = sum(normalized.values())
        if current_sum != Decimal("1"):
            # Add/subtract difference to the largest weight
            diff = Decimal("1") - current_sum
            largest_key = max(normalized, key=lambda k: normalized[k])
            normalized[largest_key] += diff

        return normalized

    def get_regime_summary(
        self,
        base_allocations: dict[str, Decimal],
        regime_state: RegimeState,
    ) -> dict[str, Any]:
        """Get a summary of regime adjustment for logging/debugging.

        Args:
            base_allocations: Original allocations
            regime_state: Current regime state

        Returns:
            Dictionary with adjustment details

        """
        adjusted = self.compute_adjusted_allocations(base_allocations, regime_state)

        changes: dict[str, dict[str, str]] = {}
        for strategy_file in base_allocations:
            base = base_allocations[strategy_file]
            adj = adjusted.get(strategy_file, Decimal("0"))
            pct_change = (
                float((adj - base) / base * 100) if base > 0 else 0.0
            )
            changes[strategy_file] = {
                "base_weight": str(base),
                "adjusted_weight": str(adj),
                "pct_change": f"{pct_change:+.1f}%",
            }

        return {
            "regime": regime_state.regime.value,
            "probability": str(regime_state.probability),
            "adjustment_method": self.config.adjustment_method,
            "changes": changes,
            "base_total": str(sum(base_allocations.values())),
            "adjusted_total": str(sum(adjusted.values())),
        }
