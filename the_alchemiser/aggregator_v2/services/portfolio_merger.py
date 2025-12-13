"""Business Unit: aggregator_v2 | Status: current.

Service for merging partial portfolios from multiple strategy files.

Aggregates partial signals into a single consolidated portfolio that
preserves the existing SignalGenerated event structure expected by
Portfolio Lambda.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.errors import AlchemiserError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolio,
)

logger = get_logger(__name__)


class AggregationError(AlchemiserError):
    """Error during signal aggregation."""


class PortfolioMerger:
    """Merges partial portfolios from multiple strategy files.

    Each strategy file produces a partial portfolio with allocations
    already scaled by its weight. This service sums allocations across
    all files to produce the final consolidated portfolio.
    """

    def __init__(self, allocation_tolerance: float = 0.01) -> None:
        """Initialize the portfolio merger.

        Args:
            allocation_tolerance: Tolerance for total allocation validation.
                Default 0.01 means 99%-101% is acceptable.

        """
        self._tolerance = Decimal(str(allocation_tolerance))

    def merge_portfolios(
        self,
        partial_signals: list[dict[str, Any]],
        correlation_id: str,
    ) -> ConsolidatedPortfolio:
        """Merge multiple partial portfolios into one consolidated portfolio.

        Each partial portfolio already has allocations scaled by the
        strategy file's weight. We sum them to get the final allocation.

        Example:
            Strategy 1 (KLM.clj, weight=0.5): {"AAPL": 0.5} (already scaled)
            Strategy 2 (momentum.clj, weight=0.5): {"SPY": 0.5} (already scaled)
            Merged: {"AAPL": 0.5, "SPY": 0.5}

        Args:
            partial_signals: List of partial signal dicts with
                'consolidated_portfolio' and 'dsl_file' keys.
            correlation_id: Workflow correlation ID.

        Returns:
            Merged ConsolidatedPortfolio.

        Raises:
            AggregationError: If allocations don't sum to ~1.0.

        """
        merged_allocations: dict[str, Decimal] = {}
        merged_contributions: dict[str, dict[str, Decimal]] = {}
        source_strategies: list[str] = []
        total_signal_count = 0

        for partial in partial_signals:
            dsl_file = partial["dsl_file"]
            source_strategies.append(dsl_file)
            total_signal_count += partial.get("signal_count", 0)

            # Get target allocations from partial portfolio
            portfolio_data = partial["consolidated_portfolio"]

            # Handle both raw dict and nested format
            if isinstance(portfolio_data, dict):
                target_allocations = portfolio_data.get("target_allocations", portfolio_data)
                # Also get strategy_contributions if present
                strategy_contributions = portfolio_data.get("strategy_contributions", {})
            else:
                target_allocations = portfolio_data
                strategy_contributions = {}

            for symbol, weight in target_allocations.items():
                if symbol in (
                    "correlation_id",
                    "timestamp",
                    "strategy_count",
                    "source_strategies",
                    "schema_version",
                    "strategy_contributions",
                ):
                    continue  # Skip metadata fields

                # Convert to Decimal if needed
                if not isinstance(weight, Decimal):
                    weight = Decimal(str(weight))

                if symbol in merged_allocations:
                    merged_allocations[symbol] += weight
                else:
                    merged_allocations[symbol] = weight

            # Merge strategy contributions
            for strategy_id, allocations in strategy_contributions.items():
                if strategy_id not in merged_contributions:
                    merged_contributions[strategy_id] = {}

                for symbol, weight in allocations.items():
                    if not isinstance(weight, Decimal):
                        weight = Decimal(str(weight))

                    if symbol in merged_contributions[strategy_id]:
                        merged_contributions[strategy_id][symbol] += weight
                    else:
                        merged_contributions[strategy_id][symbol] = weight

        # Validate total allocation
        total = sum(merged_allocations.values())
        min_valid = Decimal("1") - self._tolerance
        max_valid = Decimal("1") + self._tolerance

        if not (min_valid <= total <= max_valid):
            raise AggregationError(
                f"Invalid total allocation: {total}. Expected ~1.0 "
                f"(tolerance: {self._tolerance}). Allocations: {merged_allocations}",
                context={
                    "total_allocation": str(total),
                    "tolerance": str(self._tolerance),
                    "symbol_count": len(merged_allocations),
                    "strategies_merged": len(partial_signals),
                },
            )

        logger.info(
            "Merged portfolios successfully",
            extra={
                "correlation_id": correlation_id,
                "strategies_merged": len(partial_signals),
                "symbols_in_portfolio": len(merged_allocations),
                "total_allocation": str(total),
                "total_signal_count": total_signal_count,
            },
        )

        return ConsolidatedPortfolio(
            target_allocations=merged_allocations,
            strategy_contributions=merged_contributions,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
            strategy_count=len(partial_signals),
            source_strategies=source_strategies,
        )

    def merge_signals_data(
        self,
        partial_signals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Merge signals_data from multiple partial signals.

        Combines all per-strategy signals into a unified signals_data
        structure that preserves individual strategy information.

        Args:
            partial_signals: List of partial signal dicts with
                'signals_data' and 'dsl_file' keys.

        Returns:
            Merged signals_data dict.

        """
        merged: dict[str, Any] = {
            "strategies": {},
            "aggregated": True,
            "total_files": len(partial_signals),
        }

        for partial in partial_signals:
            dsl_file = partial["dsl_file"]
            signals_data = partial.get("signals_data", {})

            # Store each strategy's signals under its file name
            merged["strategies"][dsl_file] = signals_data

        return merged
