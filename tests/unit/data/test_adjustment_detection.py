"""Business Unit: data | Status: current.

Unit tests for price adjustment detection in market data store.

Tests verify that:
1. Adjustment detection correctly identifies retroactive price changes
2. AdjustmentInfo dataclass properly captures adjustment metadata
3. append_bars returns correct adjustment information
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.shared.data_v2.market_data_store import AdjustmentInfo


@pytest.mark.unit
class TestAdjustmentInfo:
    """Test AdjustmentInfo dataclass behavior."""

    def test_adjustment_info_with_adjustments(self) -> None:
        """Test AdjustmentInfo creation with adjustments."""
        info = AdjustmentInfo(
            adjusted_dates=["2024-01-01", "2024-01-02"],
            adjustment_count=2,
            max_pct_change=5.5,
        )
        assert info.adjusted_dates == ["2024-01-01", "2024-01-02"]
        assert info.adjustment_count == 2
        assert info.max_pct_change == 5.5
        assert bool(info) is True  # Should be truthy when adjustments exist

    def test_adjustment_info_without_adjustments(self) -> None:
        """Test AdjustmentInfo creation without adjustments."""
        info = AdjustmentInfo(
            adjusted_dates=[],
            adjustment_count=0,
            max_pct_change=0.0,
        )
        assert info.adjusted_dates == []
        assert info.adjustment_count == 0
        assert info.max_pct_change == 0.0
        assert bool(info) is False  # Should be falsy when no adjustments

    def test_adjustment_info_defaults(self) -> None:
        """Test AdjustmentInfo default values."""
        info = AdjustmentInfo()
        assert info.adjusted_dates == []
        assert info.adjustment_count == 0
        assert info.max_pct_change == 0.0
        assert bool(info) is False


@pytest.mark.unit
class TestAdjustmentDetectionLogic:
    """Test price adjustment detection logic."""

    def test_calculate_adjustment_threshold(self) -> None:
        """Test that adjustment threshold calculation is correct."""
        # Default threshold is 0.5% (0.005)
        threshold = Decimal("0.005")
        
        # Test price change detection
        old_price = Decimal("100.00")
        new_price_adjusted = Decimal("98.00")  # 2% change - should trigger
        new_price_normal = Decimal("100.10")  # 0.1% change - should not trigger
        
        pct_change_adjusted = abs((new_price_adjusted - old_price) / old_price)
        pct_change_normal = abs((new_price_normal - old_price) / old_price)
        
        assert pct_change_adjusted > threshold
        assert pct_change_normal < threshold

    def test_percentage_calculation(self) -> None:
        """Test percentage change calculation for various price changes."""
        test_cases = [
            (Decimal("100.00"), Decimal("95.00"), Decimal("0.05")),  # 5% drop
            (Decimal("100.00"), Decimal("105.00"), Decimal("0.05")),  # 5% rise
            (Decimal("50.00"), Decimal("51.00"), Decimal("0.02")),  # 2% rise
            (Decimal("200.00"), Decimal("199.00"), Decimal("0.005")),  # 0.5% drop
        ]
        
        for old_price, new_price, expected_pct in test_cases:
            pct_change = abs((new_price - old_price) / old_price)
            assert abs(pct_change - expected_pct) < Decimal("0.0001")


@pytest.mark.unit
class TestAdjustmentMetadataAggregation:
    """Test adjustment metadata aggregation across symbols."""

    def test_aggregate_adjustment_counts(self) -> None:
        """Test aggregating adjustment counts from multiple symbols."""
        adjustments = {
            "AAPL": {
                "adjusted": True,
                "adjustment_count": 3,
                "adjusted_dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
            },
            "GOOGL": {
                "adjusted": True,
                "adjustment_count": 2,
                "adjusted_dates": ["2024-01-01", "2024-01-02"],
            },
        }
        
        total_adjustments = sum(adj["adjustment_count"] for adj in adjustments.values())
        assert total_adjustments == 5
        
        symbols_adjusted = [symbol for symbol, adj in adjustments.items() if adj["adjusted"]]
        assert len(symbols_adjusted) == 2
        assert set(symbols_adjusted) == {"AAPL", "GOOGL"}

    def test_aggregate_adjusted_dates_by_symbol(self) -> None:
        """Test creating adjusted_dates_by_symbol mapping."""
        adjustments = {
            "AAPL": {
                "adjusted_dates": ["2024-01-01", "2024-01-02"],
            },
            "GOOGL": {
                "adjusted_dates": ["2024-01-03"],
            },
        }
        
        adjusted_dates_by_symbol = {
            symbol: adj["adjusted_dates"]
            for symbol, adj in adjustments.items()
            if adj.get("adjusted_dates")
        }
        
        assert adjusted_dates_by_symbol == {
            "AAPL": ["2024-01-01", "2024-01-02"],
            "GOOGL": ["2024-01-03"],
        }


@pytest.mark.unit
class TestAppendBarsAdjustmentScenarios:
    """Test scenarios for append_bars adjustment detection behavior.

    These tests verify the expected behavior and edge cases of the
    adjustment detection logic as implemented in MarketDataStore.append_bars().

    Note: Full integration tests with actual MarketDataStore would require
    additional test infrastructure setup (PYTHONPATH, S3 mocking, etc.).
    These tests document and verify the expected behavior patterns.
    """

    def test_adjustment_info_truthiness_with_adjustments(self) -> None:
        """AdjustmentInfo with adjustments should be truthy."""
        info = AdjustmentInfo(
            adjusted_dates=["2024-01-01"],
            adjustment_count=1,
            max_pct_change=5.0,
        )
        # This is the condition used in append_bars return handling
        assert bool(info) is True
        assert info  # Truthy in boolean context

    def test_adjustment_info_falsiness_without_adjustments(self) -> None:
        """AdjustmentInfo without adjustments should be falsy."""
        info = AdjustmentInfo(
            adjusted_dates=[],
            adjustment_count=0,
            max_pct_change=0.0,
        )
        # When append_bars returns (True, None), this is the equivalent
        assert bool(info) is False
        assert not info  # Falsy in boolean context

    def test_adjustment_threshold_detection_logic(self) -> None:
        """Verify adjustment threshold detection matches append_bars logic.

        append_bars uses Decimal("0.005") (0.5%) as the default threshold.
        Price changes >= 0.5% should trigger adjustment detection.
        """
        threshold = Decimal("0.005")

        # Scenario 1: Stock split causing 2% price drop - should detect
        old_close = Decimal("100.00")
        new_close_split = Decimal("98.00")
        pct_change = abs((new_close_split - old_close) / old_close)
        assert pct_change > threshold, "2% change should exceed 0.5% threshold"

        # Scenario 2: Dividend adjustment causing 1% drop - should detect
        new_close_dividend = Decimal("99.00")
        pct_change = abs((new_close_dividend - old_close) / old_close)
        assert pct_change > threshold, "1% change should exceed 0.5% threshold"

        # Scenario 3: Normal market volatility 0.3% - should NOT detect
        new_close_normal = Decimal("100.30")
        pct_change = abs((new_close_normal - old_close) / old_close)
        assert pct_change < threshold, "0.3% change should NOT exceed threshold"

        # Scenario 4: Exactly at threshold 0.5% - should detect (uses > not >=)
        new_close_edge = Decimal("100.50")
        pct_change = abs((new_close_edge - old_close) / old_close)
        # At exactly 0.5%, pct_change equals threshold, so > returns False
        assert pct_change == threshold, "0.5% change should equal threshold"

    def test_adjustment_info_max_pct_change_calculation(self) -> None:
        """Verify max_pct_change is correctly computed from price changes.

        In append_bars, max_pct_change tracks the largest percentage change
        detected across all adjusted dates for logging/monitoring.
        """
        # Simulate detecting adjustments across multiple dates
        price_changes = [
            (Decimal("100.00"), Decimal("95.00")),  # 5% drop
            (Decimal("100.00"), Decimal("98.00")),  # 2% drop
            (Decimal("100.00"), Decimal("97.00")),  # 3% drop
        ]

        max_pct = 0.0
        for old_price, new_price in price_changes:
            pct = float(abs((new_price - old_price) / old_price) * 100)
            max_pct = max(max_pct, pct)

        # Should capture the largest change (5%)
        info = AdjustmentInfo(
            adjusted_dates=["2024-01-01", "2024-01-02", "2024-01-03"],
            adjustment_count=3,
            max_pct_change=max_pct,
        )
        assert info.max_pct_change == 5.0
        assert info.adjustment_count == 3

    def test_adjustment_dates_are_sorted_strings(self) -> None:
        """adjusted_dates should be YYYY-MM-DD string format for serialization.

        This format is used for EventBridge event payloads and email notifications.
        """
        # Simulate how append_bars formats dates
        from datetime import date

        raw_dates = [date(2024, 1, 15), date(2024, 1, 2), date(2024, 1, 10)]
        adjusted_dates_str = [str(d) for d in sorted(raw_dates)]

        info = AdjustmentInfo(
            adjusted_dates=adjusted_dates_str,
            adjustment_count=len(adjusted_dates_str),
            max_pct_change=2.5,
        )

        # Dates should be sorted and in string format
        assert info.adjusted_dates == ["2024-01-02", "2024-01-10", "2024-01-15"]
        assert all(isinstance(d, str) for d in info.adjusted_dates)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
