"""Business Unit: aggregator_v2 | Status: current.

Unit tests for PortfolioMerger service.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from the_alchemiser.aggregator_v2.services.portfolio_merger import (
    AggregationError,
    PortfolioMerger,
)


class TestPortfolioMerger:
    """Tests for PortfolioMerger service."""

    @pytest.fixture
    def merger(self) -> PortfolioMerger:
        """Create a PortfolioMerger instance."""
        return PortfolioMerger()

    def test_merge_single_portfolio(self, merger: PortfolioMerger) -> None:
        """Test merging a single partial portfolio."""
        partial_signals = [
            {
                "dsl_file": "strategy1.clj",
                "allocation": Decimal("1.0"),
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.6", "MSFT": "0.4"}
                },
                "signals_data": {"strategy1": {"symbols": ["AAPL", "MSFT"]}},
                "signal_count": 2,
            }
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        assert "AAPL" in result.target_allocations
        assert "MSFT" in result.target_allocations
        # Single portfolio - allocations preserved
        assert result.target_allocations["AAPL"] == Decimal("0.6")
        assert result.target_allocations["MSFT"] == Decimal("0.4")

    def test_merge_multiple_portfolios_non_overlapping(
        self, merger: PortfolioMerger
    ) -> None:
        """Test merging multiple portfolios with non-overlapping symbols."""
        partial_signals = [
            {
                "dsl_file": "strategy1.clj",
                "allocation": Decimal("0.5"),
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.25", "MSFT": "0.25"}
                },
                "signals_data": {},
                "signal_count": 2,
            },
            {
                "dsl_file": "strategy2.clj",
                "allocation": Decimal("0.5"),
                "consolidated_portfolio": {
                    "target_allocations": {"GOOG": "0.30", "AMZN": "0.20"}
                },
                "signals_data": {},
                "signal_count": 2,
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        assert len(result.target_allocations) == 4
        assert result.target_allocations["AAPL"] == Decimal("0.25")
        assert result.target_allocations["MSFT"] == Decimal("0.25")
        assert result.target_allocations["GOOG"] == Decimal("0.30")
        assert result.target_allocations["AMZN"] == Decimal("0.20")

    def test_merge_multiple_portfolios_overlapping(
        self, merger: PortfolioMerger
    ) -> None:
        """Test merging portfolios with overlapping symbols (allocations summed)."""
        partial_signals = [
            {
                "dsl_file": "strategy1.clj",
                "allocation": Decimal("0.6"),
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.30", "MSFT": "0.30"}
                },
                "signals_data": {},
                "signal_count": 2,
            },
            {
                "dsl_file": "strategy2.clj",
                "allocation": Decimal("0.4"),
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.20", "GOOG": "0.20"}
                },
                "signals_data": {},
                "signal_count": 2,
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        # AAPL appears in both - allocations summed
        assert result.target_allocations["AAPL"] == Decimal("0.50")
        assert result.target_allocations["MSFT"] == Decimal("0.30")
        assert result.target_allocations["GOOG"] == Decimal("0.20")

    def test_merge_empty_portfolios_raises(self, merger: PortfolioMerger) -> None:
        """Test merging with no partial signals raises error."""
        with pytest.raises(AggregationError, match="Invalid total allocation: 0"):
            merger.merge_portfolios([], "test-correlation")

    def test_merge_signals_data(self, merger: PortfolioMerger) -> None:
        """Test merging signals data from multiple strategies."""
        partial_signals = [
            {
                "dsl_file": "momentum.clj",
                "allocation": Decimal("0.5"),
                "consolidated_portfolio": {"target_allocations": {"AAPL": "0.25"}},
                "signals_data": {"momentum": {"symbols": ["AAPL"], "action": "BUY"}},
                "signal_count": 1,
            },
            {
                "dsl_file": "value.clj",
                "allocation": Decimal("0.5"),
                "consolidated_portfolio": {"target_allocations": {"MSFT": "0.25"}},
                "signals_data": {"value": {"symbols": ["MSFT"], "action": "HOLD"}},
                "signal_count": 1,
            },
        ]

        result = merger.merge_signals_data(partial_signals)

        assert "strategies" in result
        assert "momentum.clj" in result["strategies"]
        assert "value.clj" in result["strategies"]
        assert result["aggregated"] is True
        assert result["total_files"] == 2

    def test_merge_handles_malformed_portfolio(self, merger: PortfolioMerger) -> None:
        """Test that malformed portfolio data raises appropriate error."""
        partial_signals = [
            {
                "dsl_file": "bad.clj",
                "allocation": Decimal("1.0"),
                "consolidated_portfolio": {"AAPL": "not-a-number"},
                "signals_data": {},
                "signal_count": 0,
            },
        ]

        with pytest.raises(Exception):  # Decimal conversion will fail
            merger.merge_portfolios(partial_signals, "test-correlation")

    def test_total_allocation_sums_correctly(self, merger: PortfolioMerger) -> None:
        """Test that merged portfolio allocations sum to ~1.0."""
        partial_signals = [
            {
                "dsl_file": "strat1.clj",
                "allocation": Decimal("0.333"),
                "consolidated_portfolio": {"target_allocations": {"AAPL": "0.333"}},
                "signals_data": {},
                "signal_count": 1,
            },
            {
                "dsl_file": "strat2.clj",
                "allocation": Decimal("0.333"),
                "consolidated_portfolio": {"target_allocations": {"MSFT": "0.333"}},
                "signals_data": {},
                "signal_count": 1,
            },
            {
                "dsl_file": "strat3.clj",
                "allocation": Decimal("0.334"),
                "consolidated_portfolio": {"target_allocations": {"GOOG": "0.334"}},
                "signals_data": {},
                "signal_count": 1,
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        total = sum(result.target_allocations.values())
        assert Decimal("0.99") <= total <= Decimal("1.01")

    def test_allocation_tolerance_is_configurable(self) -> None:
        """Test that allocation tolerance can be configured."""
        # Create merger with stricter tolerance
        strict_merger = PortfolioMerger(allocation_tolerance=0.001)

        partial_signals = [
            {
                "dsl_file": "strat1.clj",
                "consolidated_portfolio": {"target_allocations": {"AAPL": "0.95"}},
                "signals_data": {},
                "signal_count": 1,
            },
        ]

        # Should fail with strict tolerance (0.95 is outside 0.999-1.001)
        with pytest.raises(AggregationError, match="Invalid total allocation"):
            strict_merger.merge_portfolios(partial_signals, "test-correlation")

        # Same data with lenient tolerance passes merger but may fail portfolio validation
        # since ConsolidatedPortfolio also validates
        lenient_merger = PortfolioMerger(allocation_tolerance=0.10)

        # Use allocation that passes ConsolidatedPortfolio validation (0.99-1.01)
        valid_signals = [
            {
                "dsl_file": "strat1.clj",
                "consolidated_portfolio": {"target_allocations": {"AAPL": "0.995"}},
                "signals_data": {},
                "signal_count": 1,
            },
        ]
        result = lenient_merger.merge_portfolios(valid_signals, "test-correlation")
        assert result.target_allocations["AAPL"] == Decimal("0.995")

    def test_source_strategies_tracked(self, merger: PortfolioMerger) -> None:
        """Test that source strategies are tracked in merged portfolio."""
        partial_signals = [
            {
                "dsl_file": "strategy1.clj",
                "consolidated_portfolio": {"target_allocations": {"AAPL": "0.5"}},
                "signals_data": {},
                "signal_count": 1,
            },
            {
                "dsl_file": "strategy2.clj",
                "consolidated_portfolio": {"target_allocations": {"MSFT": "0.5"}},
                "signals_data": {},
                "signal_count": 1,
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        assert "strategy1.clj" in result.source_strategies
        assert "strategy2.clj" in result.source_strategies
        assert result.strategy_count == 2

    def test_merge_preserves_strategy_contributions(self, merger: PortfolioMerger) -> None:
        """Test that strategy contributions are merged correctly across partials."""
        partial_signals = [
            {
                "dsl_file": "momentum",
                "signal_count": 2,
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.6"},
                    "strategy_contributions": {"momentum": {"AAPL": "0.6"}},
                },
            },
            {
                "dsl_file": "mean_rev",
                "signal_count": 1,
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.4"},
                    "strategy_contributions": {"mean_rev": {"AAPL": "0.4"}},
                },
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        # Verify target allocations summed correctly
        assert result.target_allocations["AAPL"] == Decimal("1.0")

        # Verify strategy contributions preserved
        assert "momentum" in result.strategy_contributions
        assert "mean_rev" in result.strategy_contributions
        assert result.strategy_contributions["momentum"]["AAPL"] == Decimal("0.6")
        assert result.strategy_contributions["mean_rev"]["AAPL"] == Decimal("0.4")

    def test_merge_strategy_contributions_multiple_symbols(self, merger: PortfolioMerger) -> None:
        """Test strategy contributions with multiple symbols across strategies."""
        partial_signals = [
            {
                "dsl_file": "momentum",
                "signal_count": 2,
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.4", "MSFT": "0.2"},
                    "strategy_contributions": {
                        "momentum": {"AAPL": "0.4", "MSFT": "0.2"}
                    },
                },
            },
            {
                "dsl_file": "mean_rev",
                "signal_count": 2,
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.2", "GOOGL": "0.2"},
                    "strategy_contributions": {
                        "mean_rev": {"AAPL": "0.2", "GOOGL": "0.2"}
                    },
                },
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        # Verify overlapping symbol (AAPL) summed correctly
        assert result.target_allocations["AAPL"] == Decimal("0.6")
        assert result.target_allocations["MSFT"] == Decimal("0.2")
        assert result.target_allocations["GOOGL"] == Decimal("0.2")

        # Verify contributions preserved with correct breakdown
        assert result.strategy_contributions["momentum"]["AAPL"] == Decimal("0.4")
        assert result.strategy_contributions["mean_rev"]["AAPL"] == Decimal("0.2")
        assert result.strategy_contributions["momentum"]["MSFT"] == Decimal("0.2")
        assert result.strategy_contributions["mean_rev"]["GOOGL"] == Decimal("0.2")
        # mean_rev shouldn't have MSFT, momentum shouldn't have GOOGL
        assert "MSFT" not in result.strategy_contributions["mean_rev"]
        assert "GOOGL" not in result.strategy_contributions["momentum"]

    def test_merge_backward_compatibility_without_contributions(self, merger: PortfolioMerger) -> None:
        """Test merger handles partials without strategy_contributions (backward compat)."""
        partial_signals = [
            {
                "dsl_file": "legacy_strategy",
                "signal_count": 1,
                "consolidated_portfolio": {
                    "target_allocations": {"AAPL": "0.5"},
                    # No strategy_contributions field
                },
            },
            {
                "dsl_file": "another_legacy",
                "signal_count": 1,
                "consolidated_portfolio": {
                    "target_allocations": {"MSFT": "0.5"},
                },
            },
        ]

        result = merger.merge_portfolios(partial_signals, "test-correlation")

        # Should still work, just with empty strategy_contributions
        assert result.target_allocations["AAPL"] == Decimal("0.5")
        assert result.target_allocations["MSFT"] == Decimal("0.5")
        assert result.strategy_contributions == {}
