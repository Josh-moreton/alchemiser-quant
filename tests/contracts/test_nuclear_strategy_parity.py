"""
Parity test for Nuclear strategy - legacy vs typed implementation.

This test compares the output of the legacy nuclear_signals.py implementation
with the new typed NuclearTypedEngine for a fixed fixture to ensure compatibility.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.domain.strategies.nuclear_signals import (
    NuclearStrategyEngine as LegacyNuclearEngine,
)
from the_alchemiser.domain.strategies.nuclear_typed_engine import NuclearTypedEngine
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.utils.feature_flags import type_system_v2_enabled


@pytest.fixture
def fixed_market_data() -> dict[str, pd.DataFrame]:
    """Fixed market data fixture for consistent testing."""
    # Create consistent test data that should produce deterministic signals
    base_prices = {
        "SPY": [95.0, 96.0, 97.0, 98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0],
        "IOO": [45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0],
        "TQQQ": [25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0],
        "VTV": [75.0, 76.0, 77.0, 78.0, 79.0, 80.0, 81.0, 82.0, 83.0, 84.0],
        "XLF": [35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0],
        "VOX": [85.0, 86.0, 87.0, 88.0, 89.0, 90.0, 91.0, 92.0, 93.0, 94.0],
        "UVXY": [15.0, 14.5, 14.0, 13.5, 13.0, 12.5, 12.0, 11.5, 11.0, 10.5],
        "BTAL": [20.0, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9],
        "QQQ": [300.0, 305.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0, 340.0, 345.0],
        "SQQQ": [15.0, 14.5, 14.0, 13.5, 13.0, 12.5, 12.0, 11.5, 11.0, 10.5],
        "PSQ": [18.0, 17.8, 17.6, 17.4, 17.2, 17.0, 16.8, 16.6, 16.4, 16.2],
        "UPRO": [65.0, 66.0, 67.0, 68.0, 69.0, 70.0, 71.0, 72.0, 73.0, 74.0],
        "TLT": [120.0, 121.0, 122.0, 123.0, 124.0, 125.0, 124.0, 123.0, 122.0, 121.0],
        "IEF": [110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 114.0, 113.0, 112.0, 111.0],
        "SMR": [12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5],
        "BWXT": [45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0],
        "LEU": [8.0, 8.2, 8.4, 8.6, 8.8, 9.0, 9.2, 9.4, 9.6, 9.8],
        "EXC": [40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0],
        "NLR": [55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 61.0, 62.0, 63.0, 64.0],
        "OKLO": [22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0],
    }

    # Extend to 250 days for sufficient technical indicator history
    market_data = {}
    for symbol, prices in base_prices.items():
        # Repeat and extend the pattern to get 250 data points
        extended_prices = (prices * 25)[:250]
        market_data[symbol] = pd.DataFrame(
            {
                "Open": extended_prices,
                "High": [p * 1.02 for p in extended_prices],
                "Low": [p * 0.98 for p in extended_prices],
                "Close": extended_prices,
                "Volume": [1000000] * 250,
            },
            index=pd.date_range("2023-01-01", periods=250, freq="D"),
        )

    return market_data


@pytest.fixture
def mock_legacy_data_provider(fixed_market_data: dict[str, pd.DataFrame]) -> Mock:
    """Mock data provider for legacy Nuclear engine."""
    provider = Mock()
    provider.get_data.side_effect = lambda symbol: fixed_market_data.get(symbol, pd.DataFrame())
    return provider


@pytest.fixture
def mock_market_data_port(fixed_market_data: dict[str, pd.DataFrame]) -> Mock:
    """Mock MarketDataPort for typed Nuclear engine."""
    port = Mock(spec=MarketDataPort)
    port.get_data.side_effect = lambda symbol, **kwargs: fixed_market_data.get(symbol, pd.DataFrame())
    port.get_current_price.side_effect = lambda symbol: (
        fixed_market_data[symbol]["Close"].iloc[-1] if symbol in fixed_market_data else None
    )
    return port


class TestNuclearStrategyParity:
    """Test parity between legacy and typed Nuclear strategy implementations."""

    def test_signal_parity_bull_market(
        self,
        fixed_market_data: dict[str, pd.DataFrame],
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test signal parity in bull market conditions."""
        # Legacy implementation
        legacy_engine = LegacyNuclearEngine(data_provider=mock_legacy_data_provider)
        market_data = legacy_engine.get_market_data()
        indicators = legacy_engine.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_engine.evaluate_nuclear_strategy(
            indicators, market_data
        )

        # Typed implementation
        typed_engine = NuclearTypedEngine(mock_market_data_port)
        now = datetime.now(UTC)
        typed_signals = typed_engine.generate_signals(now)

        assert len(typed_signals) == 1
        typed_signal = typed_signals[0]

        # Check signal equivalence (allowing for symbol normalization)
        self._assert_signal_equivalence(
            legacy_symbol, legacy_action, legacy_reason,
            typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning
        )

    def test_signal_parity_with_feature_flag_off(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test that with feature flag off, we can still run both implementations."""
        # Temporarily disable types v2 flag
        original_flag = os.environ.get("TYPES_V2_ENABLED")
        os.environ["TYPES_V2_ENABLED"] = "0"

        try:
            # Legacy should work regardless of flag
            legacy_engine = LegacyNuclearEngine(data_provider=mock_legacy_data_provider)
            market_data = legacy_engine.get_market_data()
            indicators = legacy_engine.calculate_indicators(market_data)
            legacy_symbol, legacy_action, legacy_reason = legacy_engine.evaluate_nuclear_strategy(
                indicators, market_data
            )

            # Typed should also work (not flag-dependent at strategy level)
            typed_engine = NuclearTypedEngine(mock_market_data_port)
            now = datetime.now(UTC)
            typed_signals = typed_engine.generate_signals(now)

            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Both should produce valid signals
            assert legacy_action in ["BUY", "SELL", "HOLD"]
            assert typed_signal.action in ["BUY", "SELL", "HOLD"]

        finally:
            # Restore original flag value
            if original_flag is not None:
                os.environ["TYPES_V2_ENABLED"] = original_flag
            else:
                os.environ.pop("TYPES_V2_ENABLED", None)

    def test_signal_parity_with_feature_flag_on(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test that with feature flag on, both implementations work and should produce similar results."""
        # Enable types v2 flag
        original_flag = os.environ.get("TYPES_V2_ENABLED")
        os.environ["TYPES_V2_ENABLED"] = "1"

        try:
            assert type_system_v2_enabled()  # Verify flag is working

            # Legacy implementation
            legacy_engine = LegacyNuclearEngine(data_provider=mock_legacy_data_provider)
            market_data = legacy_engine.get_market_data()
            indicators = legacy_engine.calculate_indicators(market_data)
            legacy_symbol, legacy_action, legacy_reason = legacy_engine.evaluate_nuclear_strategy(
                indicators, market_data
            )

            # Typed implementation
            typed_engine = NuclearTypedEngine(mock_market_data_port)
            now = datetime.now(UTC)
            typed_signals = typed_engine.generate_signals(now)

            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Should produce equivalent signals
            self._assert_signal_equivalence(
                legacy_symbol, legacy_action, legacy_reason,
                typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning
            )

            # Typed signal should have valid confidence and allocation
            assert 0 <= typed_signal.confidence.value <= 1
            assert typed_signal.target_allocation.value >= 0

        finally:
            # Restore original flag value
            if original_flag is not None:
                os.environ["TYPES_V2_ENABLED"] = original_flag
            else:
                os.environ.pop("TYPES_V2_ENABLED", None)

    def test_edge_case_parity_no_spy_data(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test parity when SPY data is missing."""
        # Mock empty SPY data
        mock_legacy_data_provider.get_data.side_effect = lambda symbol: (
            pd.DataFrame() if symbol == "SPY" else pd.DataFrame({
                "Open": [100.0] * 50,
                "High": [101.0] * 50,
                "Low": [99.0] * 50,
                "Close": [100.0] * 50,
                "Volume": [1000000] * 50,
            }, index=pd.date_range("2023-01-01", periods=50, freq="D"))
        )

        mock_market_data_port.get_data.side_effect = lambda symbol, **kwargs: (
            pd.DataFrame() if symbol == "SPY" else pd.DataFrame({
                "Open": [100.0] * 50,
                "High": [101.0] * 50,
                "Low": [99.0] * 50,
                "Close": [100.0] * 50,
                "Volume": [1000000] * 50,
            }, index=pd.date_range("2023-01-01", periods=50, freq="D"))
        )

        # Legacy implementation
        legacy_engine = LegacyNuclearEngine(data_provider=mock_legacy_data_provider)
        market_data = legacy_engine.get_market_data()
        indicators = legacy_engine.calculate_indicators(market_data)
        legacy_symbol, legacy_action, legacy_reason = legacy_engine.evaluate_nuclear_strategy(
            indicators, market_data
        )

        # Typed implementation
        typed_engine = NuclearTypedEngine(mock_market_data_port)
        now = datetime.now(UTC)
        typed_signals = typed_engine.generate_signals(now)

        # Both should handle missing SPY gracefully
        assert legacy_action == "HOLD"
        assert len(typed_signals) == 1
        assert typed_signals[0].action == "HOLD"

    def _assert_signal_equivalence(
        self,
        legacy_symbol: str,
        legacy_action: str,
        legacy_reason: str,
        typed_symbol: str,
        typed_action: str,
        typed_reason: str,
    ) -> None:
        """Assert that legacy and typed signals are equivalent."""
        # Actions should be identical
        assert legacy_action == typed_action

        # Symbols should be equivalent (accounting for portfolio normalization)
        if legacy_symbol in ["UVXY_BTAL_PORTFOLIO", "NUCLEAR_PORTFOLIO"]:
            # Typed engine normalizes portfolio symbols to primary symbol
            assert typed_symbol in ["UVXY", "SMR"]
        elif "_" in legacy_symbol:
            # Other portfolio symbols should be normalized
            assert typed_symbol.isalpha() and len(typed_symbol) <= 5
        else:
            # Direct symbols should match
            assert legacy_symbol == typed_symbol

        # Reasoning should contain similar key information
        # (Not exact match due to potential formatting differences)
        assert len(typed_reason) > 0
        assert len(legacy_reason) > 0
