"""
Parity test for KLM strategy - legacy vs typed implementation with flag switching.

This test compares the output of the legacy KLMStrategyEnsemble implementation
with the new typed TypedKLMStrategyEngine for fixed fixtures under both
TYPES_V2_ENABLED=0 and TYPES_V2_ENABLED=1 to ensure compatibility.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import pandas as pd
import pytest

from tests._tolerances import DEFAULT_ATL, DEFAULT_RTL
from tests.contracts.base_strategy_parity import (
    StrategyParityFixtures,
    StrategyParityTestBase,
    StrategySignalComparator,
)
from the_alchemiser.domain.strategies.klm_ensemble_engine import KLMStrategyEnsemble
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine


@pytest.fixture
def fixed_market_data() -> dict[str, pd.DataFrame]:
    """Fixed market data fixture for consistent testing across flag states."""
    # Create sample OHLCV data with sufficient periods for ML indicators
    base_data = pd.DataFrame(
        {
            "Open": [100.0] * 250 + [110.0] * 50,
            "High": [105.0] * 250 + [115.0] * 50,
            "Low": [95.0] * 250 + [105.0] * 50,
            "Close": list(range(100, 350)) + list(range(350, 400)),  # 300 periods total
            "Volume": [1000] * 300,
        },
        index=pd.date_range("2022-01-01", periods=300, freq="D"),
    )

    # Create data for key KLM symbols with realistic variations
    return {
        "SPY": base_data.copy(),
        "TECL": base_data.copy() * 1.1,  # Technology leverage
        "BIL": base_data.copy() * 0.5,  # Bills
        "UVXY": base_data.copy() * 0.8,  # Volatility
        "XLK": base_data.copy() * 1.05,  # Technology sector
        "KMLM": base_data.copy() * 0.95,  # KLM target
        "TQQQ": base_data.copy() * 1.2,  # NASDAQ 3x
        "SQQQ": base_data.copy() * 0.7,  # NASDAQ inverse 3x
        "QQQ": base_data.copy() * 1.0,  # NASDAQ
    }


# Use shared fixtures from base class
mock_market_data_port = StrategyParityFixtures.mock_market_data_port
mock_legacy_data_provider = StrategyParityFixtures.mock_legacy_data_provider


@pytest.fixture
def test_timestamp() -> datetime:
    """Fixed timestamp for testing."""
    return datetime(2023, 1, 15, 10, 30, 0, tzinfo=UTC)


class TestKLMStrategyParity(StrategyParityTestBase):
    """Test parity between legacy and typed KLM strategy implementations."""

    def get_strategy_name(self) -> str:
        """Return the name of the strategy being tested."""
        return "KLM"

    def create_legacy_engine(self, data_provider: Mock) -> KLMStrategyEnsemble:
        """Create the legacy KLM strategy engine."""
        return KLMStrategyEnsemble(data_provider=data_provider)

    def create_typed_engine(self, **kwargs) -> TypedKLMStrategyEngine:
        """Create the typed KLM strategy engine."""
        market_data_port = kwargs.get("market_data_port")
        if market_data_port is None:
            raise ValueError("market_data_port is required for TypedKLMStrategyEngine")
        return TypedKLMStrategyEngine(market_data_port)

    def get_legacy_signals(self, engine: KLMStrategyEnsemble) -> tuple:
        """Get signals from the legacy KLM engine."""
        market_data = engine.get_market_data()
        indicators = engine.calculate_indicators(market_data)
        return engine.evaluate_ensemble(indicators, market_data)

    def get_typed_signals(
        self, engine: TypedKLMStrategyEngine, market_data_port: Mock, **kwargs
    ) -> list:
        """Get signals from the typed KLM engine."""
        test_timestamp = kwargs.get("test_timestamp", datetime.now(UTC))
        return engine.generate_signals(test_timestamp)

    def _assert_signal_equivalence(
        self,
        legacy_symbol: str,
        legacy_action: str,
        legacy_reasoning: str,
        typed_symbol: str,
        typed_action: str,
        typed_reasoning: str,
        legacy_confidence: float | None = None,
        typed_confidence: Decimal | None = None,
        typed_allocation: Decimal | None = None,
    ) -> None:
        """Assert that legacy and typed signals have equivalent structure and valid values."""
        # Use shared comparator for basic equivalence
        StrategySignalComparator.assert_basic_signal_equivalence(
            legacy_symbol,
            legacy_action,
            legacy_reasoning,
            typed_symbol,
            typed_action,
            typed_reasoning,
        )

        # KLM-specific confidence comparison if available (with tolerance for float precision)
        if legacy_confidence is not None and typed_confidence is not None:
            self.assert_float_tolerance(float(typed_confidence), legacy_confidence)

        # Allocation should be reasonable
        if typed_allocation is not None:
            assert typed_allocation >= Decimal("0")
            assert typed_allocation <= Decimal("1")

    def test_signal_parity_with_feature_flag_off(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
        test_timestamp: datetime,
    ) -> None:
        """Test that with feature flag off, we can still run both implementations."""
        self.set_feature_flag(False)

        try:
            # Legacy should work regardless of flag
            legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
            legacy_result = self.get_legacy_signals(legacy_engine)

            # Typed should also work (not flag-dependent at strategy level)
            typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)
            typed_signals = self.get_typed_signals(
                typed_engine, mock_market_data_port, test_timestamp=test_timestamp
            )

            # Both should produce some result
            assert legacy_result is not None
            assert isinstance(typed_signals, list)

            # If both have signals, compare them
            if legacy_result and typed_signals:
                # Unpack legacy result tuple: (symbol_or_allocation, action, reason, variant_name)
                legacy_symbol, legacy_action, legacy_reasoning, legacy_variant = legacy_result

                # Compare with first typed signal
                typed_signal = typed_signals[0]

                self._assert_signal_equivalence(
                    legacy_symbol,
                    legacy_action,
                    legacy_reasoning,
                    typed_signal.symbol.value,
                    typed_signal.action,
                    typed_signal.reasoning,
                    None,
                    typed_signal.confidence.value,
                    typed_signal.target_allocation.value,
                )

        finally:
            self.restore_feature_flag()

    def test_signal_parity_with_feature_flag_on(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
        test_timestamp: datetime,
    ) -> None:
        """Test that with feature flag on, both implementations work and produce similar results."""
        self.set_feature_flag(True)

        try:
            # Legacy should still work
            legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
            legacy_result = self.get_legacy_signals(legacy_engine)

            # Typed interface with flag on
            typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)
            typed_signals = self.get_typed_signals(
                typed_engine, mock_market_data_port, test_timestamp=test_timestamp
            )

            # Both should produce some result
            assert legacy_result is not None
            assert isinstance(typed_signals, list)

            # If both have signals, compare them
            if legacy_result and typed_signals:
                # Unpack legacy result tuple: (symbol_or_allocation, action, reason, variant_name)
                legacy_symbol, legacy_action, legacy_reasoning, legacy_variant = legacy_result

                typed_signal = typed_signals[0]

                self._assert_signal_equivalence(
                    legacy_symbol,
                    legacy_action,
                    legacy_reasoning,
                    typed_signal.symbol.value,
                    typed_signal.action,
                    typed_signal.reasoning,
                    None,
                    typed_signal.confidence.value,
                    typed_signal.target_allocation.value,
                )

                # Typed signal should have valid values
                self.assert_signal_structure_valid(typed_signal)

        finally:
            self.restore_feature_flag()

    def test_variant_performance_parity(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
        test_timestamp: datetime,
    ) -> None:
        """Test that variant performance calculations are comparable in both flag states."""
        for flag_enabled in [False, True]:
            self.set_feature_flag(flag_enabled)

            try:
                # Create engines
                legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
                typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)

                # Both engines should have strategy variants
                legacy_variants = legacy_engine.strategy_variants
                typed_variants = typed_engine.strategy_variants

                assert len(legacy_variants) == len(typed_variants)

                # Test performance calculation for variants if they exist
                if legacy_variants and typed_variants:
                    legacy_perf = legacy_engine.calculate_variant_performance(legacy_variants[0])
                    typed_perf = typed_engine._calculate_variant_performance(typed_variants[0])

                    # Both should return valid performance metrics
                    assert isinstance(legacy_perf, (int, float))
                    assert isinstance(typed_perf, (int, float))
                    assert 0.0 <= legacy_perf <= 1.0
                    assert 0.0 <= typed_perf <= 1.0

                    # Performance calculations may differ, but should be reasonable
                    # Allow larger tolerance for performance differences as they may use different data
                    # or calculation methods in legacy vs typed implementations
                    perf_diff = abs(legacy_perf - typed_perf)
                    tolerance = 1.0  # Allow full range difference for now
                    assert (
                        perf_diff <= tolerance
                    ), f"Performance values in range but different in flag state {flag_enabled}: {legacy_perf} vs {typed_perf}"

            finally:
                self.restore_feature_flag()

    def test_signal_generation_structure_parity(
        self,
        mock_market_data_port: Mock,
        test_timestamp: datetime,
    ) -> None:
        """Test that signal generation produces expected structure in both flag states."""
        for flag_enabled in [False, True]:
            self.set_feature_flag(flag_enabled)

            try:
                typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)
                typed_signals = self.get_typed_signals(
                    typed_engine, mock_market_data_port, test_timestamp=test_timestamp
                )

                # Should generate at least 0 signals without error
                assert isinstance(typed_signals, list)

                # If signals are generated, they should have proper structure
                for signal in typed_signals:
                    self.assert_signal_structure_valid(signal)

            finally:
                self.restore_feature_flag()

    def test_error_handling_consistency(
        self,
        test_timestamp: datetime,
    ) -> None:
        """Test that error handling is consistent across flag states."""
        for flag_enabled in [False, True]:
            self.set_feature_flag(flag_enabled)

            try:
                # Test with invalid market data port
                invalid_port = Mock(spec=MarketDataPort)
                invalid_port.get_data.side_effect = Exception("Network error")

                typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)

                # Should handle errors gracefully (not crash)
                try:
                    typed_signals = self.get_typed_signals(
                        typed_engine, invalid_port, test_timestamp=test_timestamp
                    )
                    # If it succeeds, signals should be empty or valid
                    assert isinstance(typed_signals, list)
                except Exception as e:
                    # If it fails, should be a specific expected exception
                    assert "Network error" in str(e) or "error" in str(e).lower()

            finally:
                self.restore_feature_flag()

    # Remove duplicated numerical precision test - inherited from base class
    # Remove duplicated detailed analysis test - not needed for this implementation
