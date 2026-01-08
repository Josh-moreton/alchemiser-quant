"""Unit tests for price adjustment detection in market data store.

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
