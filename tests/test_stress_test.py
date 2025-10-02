"""Business Unit: utilities | Status: current.

Unit tests for stress test script functionality.

Tests the core components of the stress test script including:
- Market condition generation
- Mock indicator service
- Scenario execution planning
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from stress_test import MarketCondition, MockIndicatorService, StressTestRunner

from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest


class TestMarketConditionGeneration:
    """Test market condition generation."""

    def test_generate_full_scenarios(self):
        """Test that full scenario generation produces expected count."""
        runner = StressTestRunner(quick_mode=False, dry_run=True)
        conditions = runner.generate_market_conditions()

        # Should have 30 regular scenarios (6 RSI regimes * 5 price scenarios)
        # Plus 4 edge cases = 34 total
        assert len(conditions) == 34

    def test_generate_quick_scenarios(self):
        """Test that quick mode generates fewer scenarios."""
        runner = StressTestRunner(quick_mode=True, dry_run=True)
        conditions = runner.generate_market_conditions()

        # Quick mode samples every 3rd + all edge cases
        # 30 regular / 3 = 10, plus 4 edge = 14
        assert len(conditions) == 14

    def test_edge_cases_included(self):
        """Test that edge cases are always included."""
        runner = StressTestRunner(quick_mode=True, dry_run=True)
        conditions = runner.generate_market_conditions()

        edge_cases = [c for c in conditions if c.metadata.get("edge_case")]
        assert len(edge_cases) == 4

        edge_ids = {c.scenario_id for c in edge_cases}
        assert "edge_all_oversold_crash" in edge_ids
        assert "edge_all_overbought_boom" in edge_ids
        assert "edge_threshold_79" in edge_ids
        assert "edge_threshold_75" in edge_ids

    def test_market_condition_structure(self):
        """Test that market conditions have required fields."""
        runner = StressTestRunner(quick_mode=False, dry_run=True)
        conditions = runner.generate_market_conditions()

        for condition in conditions:
            assert condition.scenario_id
            assert condition.description
            assert isinstance(condition.rsi_range, tuple)
            assert len(condition.rsi_range) == 2
            assert 0 <= condition.rsi_range[0] <= 100
            assert 0 <= condition.rsi_range[1] <= 100
            assert condition.rsi_range[0] <= condition.rsi_range[1]
            assert condition.price_multiplier > 0
            assert condition.volatility_regime in ["low", "medium", "high", "extreme"]


class TestMockIndicatorService:
    """Test mock indicator service."""

    def test_mock_rsi_indicator(self):
        """Test that mock service returns RSI indicators."""
        condition = MarketCondition(
            scenario_id="test_001",
            description="Test scenario",
            rsi_range=(40, 60),
            price_multiplier=1.0,
            volatility_regime="medium",
        )

        mock_service = MockIndicatorService(condition)

        request = IndicatorRequest.rsi_request(
            request_id="test_req_1",
            correlation_id="test_corr_1",
            symbol="QQQ",
            window=10,
        )

        indicator = mock_service.get_indicator(request)

        assert indicator.symbol == "QQQ"
        assert indicator.data_source == "stress_test_mock"
        assert indicator.rsi_10 is not None
        # RSI should be within range (with some variation)
        assert 30 <= indicator.rsi_10 <= 70  # Allow for symbol-based variation

    def test_mock_current_price_indicator(self):
        """Test that mock service returns current price indicators."""
        condition = MarketCondition(
            scenario_id="test_002",
            description="Test scenario",
            rsi_range=(40, 60),
            price_multiplier=1.5,
            volatility_regime="high",
        )

        mock_service = MockIndicatorService(condition)

        request = IndicatorRequest(
            request_id="test_req_2",
            correlation_id="test_corr_2",
            symbol="SPY",
            indicator_type="current_price",
            parameters={},
        )

        indicator = mock_service.get_indicator(request)

        assert indicator.symbol == "SPY"
        assert indicator.current_price is not None
        assert isinstance(indicator.current_price, Decimal)
        # Price should reflect multiplier
        assert float(indicator.current_price) > 100  # Base + multiplier

    def test_mock_service_deterministic(self):
        """Test that mock service returns deterministic values for same symbol."""
        condition = MarketCondition(
            scenario_id="test_003",
            description="Test scenario",
            rsi_range=(50, 70),
            price_multiplier=1.0,
            volatility_regime="low",
        )

        mock_service1 = MockIndicatorService(condition)
        mock_service2 = MockIndicatorService(condition)

        request1 = IndicatorRequest.rsi_request(
            request_id="req1", correlation_id="corr1", symbol="TECL", window=14
        )

        request2 = IndicatorRequest.rsi_request(
            request_id="req2", correlation_id="corr2", symbol="TECL", window=14
        )

        indicator1 = mock_service1.get_indicator(request1)
        indicator2 = mock_service2.get_indicator(request2)

        # Same symbol in same condition should give same RSI
        assert indicator1.rsi_14 == indicator2.rsi_14

    def test_mock_service_call_count(self):
        """Test that mock service tracks call count."""
        condition = MarketCondition(
            scenario_id="test_004",
            description="Test scenario",
            rsi_range=(40, 60),
            price_multiplier=1.0,
            volatility_regime="medium",
        )

        mock_service = MockIndicatorService(condition)
        assert mock_service.call_count == 0

        for i in range(5):
            request = IndicatorRequest.rsi_request(
                request_id=f"req_{i}",
                correlation_id=f"corr_{i}",
                symbol=f"SYM{i}",
                window=10,
            )
            mock_service.get_indicator(request)

        assert mock_service.call_count == 5


class TestStressTestRunner:
    """Test stress test runner functionality."""

    def test_runner_initialization(self):
        """Test that runner initializes correctly."""
        runner = StressTestRunner(quick_mode=True, dry_run=True)

        assert runner.quick_mode is True
        assert runner.dry_run is True
        assert runner.results == []

    def test_generate_report_with_no_results(self):
        """Test that report generation handles no results."""
        runner = StressTestRunner(quick_mode=True, dry_run=True)
        report = runner.generate_report()

        assert "error" in report
        assert report["error"] == "No results available"

    def test_all_symbols_defined(self):
        """Test that ALL_SYMBOLS list is properly defined."""
        runner = StressTestRunner()

        # Should have symbols from CLJ files
        assert len(runner.ALL_SYMBOLS) > 50
        assert "QQQ" in runner.ALL_SYMBOLS
        assert "SPY" in runner.ALL_SYMBOLS
        assert "TECL" in runner.ALL_SYMBOLS
        assert "TQQQ" in runner.ALL_SYMBOLS
        assert "UVXY" in runner.ALL_SYMBOLS
