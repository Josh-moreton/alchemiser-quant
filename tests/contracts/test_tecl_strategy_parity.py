"""
Parity test for TECL strategy - legacy vs typed implementation with flag switching.

This test compares the output of the legacy TECL strategy implementation
with the new typed TECLStrategyEngine for fixed fixtures under both
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
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine


@pytest.fixture
def fixed_market_data() -> dict[str, pd.DataFrame]:
    """Fixed market data fixture for consistent testing across flag states."""
    # Create consistent test data that should produce deterministic signals
    base_data = {
        "SPY": [450.0, 452.0, 454.0, 456.0, 458.0] * 50,  # 250 periods
        "XLK": [180.0, 182.0, 184.0, 186.0, 188.0] * 50,
        "KMLM": [40.0, 40.5, 41.0, 41.5, 42.0] * 50,
        "TECL": [45.0, 46.0, 47.0, 48.0, 49.0] * 50,
        "TQQQ": [35.0, 36.0, 37.0, 38.0, 39.0] * 50,
        "BIL": [91.5, 91.6, 91.7, 91.8, 91.9] * 50,
        "UVXY": [12.0, 11.8, 11.6, 11.4, 11.2] * 50,
        "SPXL": [85.0, 86.0, 87.0, 88.0, 89.0] * 50,
        "SQQQ": [15.0, 14.8, 14.6, 14.4, 14.2] * 50,
        "BSV": [77.0, 77.1, 77.2, 77.3, 77.4] * 50,
    }

    # Convert to DataFrames with OHLCV structure
    result = {}
    for symbol, prices in base_data.items():
        df = pd.DataFrame(
            {
                "Open": [p * 0.998 for p in prices],
                "High": [p * 1.005 for p in prices],
                "Low": [p * 0.995 for p in prices],
                "Close": prices,
                "Volume": [1000000 + i * 1000 for i in range(len(prices))],
            }
        )
        result[symbol] = df

    return result


# Use shared fixtures from base class
mock_market_data_port = StrategyParityFixtures.mock_market_data_port
mock_legacy_data_provider = StrategyParityFixtures.mock_legacy_data_provider


class TestTECLStrategyParity(StrategyParityTestBase):
    """Test parity between legacy and typed TECL strategy implementations."""

    def get_strategy_name(self) -> str:
        """Return the name of the strategy being tested."""
        return "TECL"

    def create_legacy_engine(self, data_provider: Mock) -> TECLStrategyEngine:
        """Create the legacy TECL strategy engine."""
        return TECLStrategyEngine(market_data_port=data_provider)

    def create_typed_engine(self, **kwargs) -> TECLStrategyEngine:
        """Create the typed TECL strategy engine."""
        market_data_port = kwargs.get("market_data_port")
        if market_data_port is None:
            raise ValueError("market_data_port is required for TECLStrategyEngine")
        return TECLStrategyEngine(market_data_port=market_data_port)

    def get_legacy_signals(self, engine: TECLStrategyEngine) -> tuple:
        """Get signals from the legacy TECL engine."""
        market_data = engine.get_market_data()
        indicators = engine.calculate_indicators(market_data)
        return engine.evaluate_tecl_strategy(indicators, market_data)

    def get_typed_signals(
        self, engine: TECLStrategyEngine, market_data_port: Mock, **kwargs
    ) -> list:
        """Get signals from the typed TECL engine."""
        # For TECL, we need to provide the data provider
        engine_with_port = TECLStrategyEngine(market_data_port=market_data_port)
        test_timestamp = kwargs.get("test_timestamp", datetime.now(UTC))
        return engine_with_port.generate_signals(test_timestamp)

    def _assert_signal_equivalence(
        self,
        legacy_symbol_or_allocation: str | dict[str, float],
        legacy_action: str,
        legacy_reasoning: str,
        typed_symbol: str,
        typed_action: str,
        typed_reasoning: str,
        typed_allocation: Decimal,
    ) -> None:
        """Assert that legacy and typed signals are equivalent."""
        # Use shared comparator for basic equivalence
        StrategySignalComparator.assert_basic_signal_equivalence(
            (
                str(legacy_symbol_or_allocation)
                if not isinstance(legacy_symbol_or_allocation, dict)
                else "portfolio"
            ),
            legacy_action,
            legacy_reasoning,
            typed_symbol,
            typed_action,
            typed_reasoning,
        )

        # TECL-specific portfolio allocation handling
        StrategySignalComparator.assert_portfolio_allocation_equivalence(
            legacy_symbol_or_allocation, typed_symbol, typed_allocation
        )

        # Actions and reasoning should match for TECL
        assert legacy_action == typed_action
        assert legacy_reasoning == typed_reasoning

    def test_signal_parity_with_feature_flag_off(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test that with feature flag off, we can still run both implementations."""
        self.set_feature_flag(False)

        try:
            # Legacy should work regardless of flag
            legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
            legacy_symbol_or_allocation, legacy_action, legacy_reasoning = self.get_legacy_signals(
                legacy_engine
            )

            # Typed interface should also work
            typed_signals = self.get_typed_signals(None, mock_market_data_port)

            # Verify basic structure
            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Should produce equivalent signals
            self._assert_signal_equivalence(
                legacy_symbol_or_allocation,
                legacy_action,
                legacy_reasoning,
                typed_signal.symbol.value,
                typed_signal.action,
                typed_signal.reasoning,
                typed_signal.target_allocation.value,
            )

            # Typed signal should have valid confidence and allocation
            self.assert_signal_structure_valid(typed_signal)

        finally:
            self.restore_feature_flag()

    def test_signal_parity_with_feature_flag_on(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test that with feature flag on, both implementations work and produce similar results."""
        self.set_feature_flag(True)

        try:
            # Legacy should still work
            legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
            legacy_symbol_or_allocation, legacy_action, legacy_reasoning = self.get_legacy_signals(
                legacy_engine
            )

            # Typed interface with flag on
            typed_signals = self.get_typed_signals(None, mock_market_data_port)

            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Should produce equivalent signals
            self._assert_signal_equivalence(
                legacy_symbol_or_allocation,
                legacy_action,
                legacy_reasoning,
                typed_signal.symbol.value,
                typed_signal.action,
                typed_signal.reasoning,
                typed_signal.target_allocation.value,
            )

            # Typed signal should have valid confidence and allocation
            self.assert_signal_structure_valid(typed_signal)

        finally:
            self.restore_feature_flag()

    def test_bull_market_scenario_parity(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test parity in bull market conditions with both flag states."""
        for flag_enabled in [False, True]:
            self.set_feature_flag(flag_enabled)

            try:
                # Create engines
                legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)

                # Get legacy result
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                    self.get_legacy_signals(legacy_engine)
                )

                # Get typed result
                typed_signals = self.get_typed_signals(None, mock_market_data_port)
                assert len(typed_signals) == 1
                typed_signal = typed_signals[0]

                # Assert equivalence
                self._assert_signal_equivalence(
                    legacy_symbol_or_allocation,
                    legacy_action,
                    legacy_reasoning,
                    typed_signal.symbol.value,
                    typed_signal.action,
                    typed_signal.reasoning,
                    typed_signal.target_allocation.value,
                )

            finally:
                self.restore_feature_flag()

    def test_portfolio_allocation_scenario_parity(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test parity when strategy returns portfolio allocation in both flag states."""
        for flag_enabled in [False, True]:
            self.set_feature_flag(flag_enabled)

            try:
                # Create engines
                legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)

                # Get baseline results from both engines
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                    self.get_legacy_signals(legacy_engine)
                )

                typed_signals = self.get_typed_signals(None, mock_market_data_port)

                # If we have results from both, compare them
                if typed_signals:
                    typed_signal = typed_signals[0]

                    # Use our standard equivalence check
                    self._assert_signal_equivalence(
                        legacy_symbol_or_allocation,
                        legacy_action,
                        legacy_reasoning,
                        typed_signal.symbol.value,
                        typed_signal.action,
                        typed_signal.reasoning,
                        typed_signal.target_allocation.value,
                    )

                    # Additional checks for portfolio case
                    if isinstance(legacy_symbol_or_allocation, dict):
                        # Primary symbol should be the one with highest allocation
                        primary_symbol = max(
                            legacy_symbol_or_allocation.keys(),
                            key=lambda s: legacy_symbol_or_allocation[s],
                        )
                        assert typed_signal.symbol.value == primary_symbol
                    else:
                        # Single symbol case
                        assert typed_signal.symbol.value == legacy_symbol_or_allocation

            finally:
                self.restore_feature_flag()

    # Inherit the shared numerical precision test from base class
    # test_numerical_precision_with_decimals is already provided by StrategyParityTestBase
