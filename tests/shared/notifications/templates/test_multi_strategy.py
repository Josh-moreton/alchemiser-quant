"""Business Unit: shared | Status: current.

Tests for MultiStrategyReportBuilder template generation.

Covers:
- Input validation (mode parameter)
- HTML generation for success/failure cases
- Defensive handling of missing attributes
- Edge cases and error conditions
"""

from __future__ import annotations

from typing import Any

import pytest

from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)


class MockExecutionResult:
    """Mock execution result for testing."""

    def __init__(
        self,
        success: bool = True,
        strategy_signals: dict[Any, Any] | None = None,
        orders_executed: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize mock execution result."""
        self.success = success
        self.strategy_signals = strategy_signals or {}
        self.orders_executed = orders_executed or []


class TestMultiStrategyReportBuilder:
    """Test MultiStrategyReportBuilder functionality."""

    def test_build_with_valid_paper_mode(self) -> None:
        """Test building report with valid PAPER mode."""
        result = MockExecutionResult(success=True)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert html is not None
        assert isinstance(html, str)
        assert "PAPER" in html
        assert "Multi-Strategy Execution Report" in html

    def test_build_with_valid_live_mode(self) -> None:
        """Test building report with valid LIVE mode."""
        result = MockExecutionResult(success=True)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "LIVE"
        )

        assert html is not None
        assert isinstance(html, str)
        assert "LIVE" in html
        assert "Multi-Strategy Execution Report" in html

    def test_build_with_lowercase_mode(self) -> None:
        """Test mode parameter is case-insensitive."""
        result = MockExecutionResult(success=True)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "paper"
        )

        assert html is not None
        assert "PAPER" in html

    def test_build_with_invalid_mode_raises_error(self) -> None:
        """Test that invalid mode raises ValueError."""
        result = MockExecutionResult(success=True)

        with pytest.raises(ValueError, match="Invalid mode 'INVALID'"):
            MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                result, "INVALID"
            )

    def test_build_with_empty_mode_raises_error(self) -> None:
        """Test that empty mode raises ValueError."""
        result = MockExecutionResult(success=True)

        with pytest.raises(ValueError, match="Invalid mode ''"):
            MultiStrategyReportBuilder.build_multi_strategy_report_neutral(result, "")

    def test_build_success_case(self) -> None:
        """Test building report for successful execution."""
        result = MockExecutionResult(
            success=True,
            orders_executed=[
                {"side": "BUY", "symbol": "AAPL", "qty": 10, "status": "filled"}
            ],
        )
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert "Completed Successfully" in html
        assert "059669" in html  # Success color

    def test_build_failure_case(self) -> None:
        """Test building report for failed execution."""
        result = MockExecutionResult(success=False)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert "Execution Failed" in html or "Failed" in html
        assert "DC2626" in html  # Error color

    def test_build_with_minimal_data(self) -> None:
        """Test building report with minimal result data."""
        result = MockExecutionResult()
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert html is not None
        assert isinstance(html, str)
        assert len(html) > 0

    def test_build_with_empty_orders(self) -> None:
        """Test building report when no orders executed."""
        result = MockExecutionResult(success=True, orders_executed=[])
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert "No rebalancing orders required" in html

    def test_build_with_strategy_signals(self) -> None:
        """Test building report with strategy signals."""
        result = MockExecutionResult(
            success=True,
            strategy_signals={
                "momentum": {
                    "action": "BUY",
                    "symbol": "SPY",
                    "reason": "Strong uptrend",
                }
            },
        )
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert html is not None
        # Strategy signals should be included via SignalsBuilder

    def test_build_html_structure_valid(self) -> None:
        """Test that generated HTML has valid structure."""
        result = MockExecutionResult(success=True)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        # Check basic HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<body" in html
        assert "</body>" in html
        assert "<table" in html

    def test_build_with_dict_like_result(self) -> None:
        """Test building report with dict-like result object."""
        # Test that function works with dict-like objects
        result_dict = {
            "success": True,
            "strategy_signals": {},
            "orders_executed": [],
        }

        # Create object with dict-like attributes
        class DictLikeResult:
            def __init__(self, data: dict[str, Any]) -> None:
                self._data = data

            def __getattr__(self, name: str) -> Any:
                return self._data.get(name)

        result = DictLikeResult(result_dict)
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert html is not None
        assert isinstance(html, str)


class TestMultiStrategyReportBuilderEdgeCases:
    """Test edge cases and error conditions."""

    def test_result_missing_success_attribute(self) -> None:
        """Test handling when result lacks success attribute."""

        class MinimalResult:
            pass

        result = MinimalResult()
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        # Should default to True per getattr default
        assert html is not None

    def test_result_missing_orders_executed(self) -> None:
        """Test handling when result lacks orders_executed attribute."""

        class ResultWithoutOrders:
            def __init__(self) -> None:
                self.success = True
                self.strategy_signals = {}

        result = ResultWithoutOrders()
        html = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
            result, "PAPER"
        )

        assert html is not None
        assert "No rebalancing orders required" in html

    def test_mode_with_whitespace(self) -> None:
        """Test mode parameter with leading/trailing whitespace."""
        result = MockExecutionResult(success=True)

        # Should handle whitespace after upper()
        with pytest.raises(ValueError):
            MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                result, " PAPER "
            )
