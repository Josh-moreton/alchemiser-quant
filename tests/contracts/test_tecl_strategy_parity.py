"""
Parity test for TECL strategy - legacy vs typed implementation with flag switching.

This test compares the output of the legacy TECL strategy implementation
with the new typed TECLStrategyEngine for fixed fixtures under both
TYPES_V2_ENABLED=0 and TYPES_V2_ENABLED=1 to ensure compatibility.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from tests._tolerances import DEFAULT_ATL, DEFAULT_RTL
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.utils.feature_flags import type_system_v2_enabled


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
        df = pd.DataFrame({
            'Open': [p * 0.998 for p in prices],
            'High': [p * 1.005 for p in prices],
            'Low': [p * 0.995 for p in prices],
            'Close': prices,
            'Volume': [1000000 + i * 1000 for i in range(len(prices))]
        })
        result[symbol] = df
    
    return result


@pytest.fixture
def mock_market_data_port(fixed_market_data: dict[str, pd.DataFrame]) -> Mock:
    """Create a mock MarketDataPort that returns fixed data."""
    mock_port = Mock(spec=MarketDataPort)
    
    def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
        return fixed_market_data.get(symbol, pd.DataFrame())
    
    mock_port.get_data = mock_get_data
    mock_port.get_current_price.return_value = 103.0
    mock_port.get_latest_quote.return_value = (102.5, 103.5)
    
    return mock_port


@pytest.fixture 
def mock_legacy_data_provider(fixed_market_data: dict[str, pd.DataFrame]) -> Mock:
    """Create a mock legacy data provider that returns fixed data."""
    mock_provider = Mock()
    
    def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
        return fixed_market_data.get(symbol, pd.DataFrame())
    
    mock_provider.get_data = mock_get_data
    return mock_provider


class TestTECLStrategyParity:
    """Test parity between legacy and typed TECL strategy implementations."""

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
        # Actions should be identical  
        assert legacy_action == typed_action

        # Symbol handling - if legacy returns portfolio allocation, 
        # typed should pick the primary symbol
        if isinstance(legacy_symbol_or_allocation, dict):
            # Portfolio allocation case
            primary_symbol = max(legacy_symbol_or_allocation.keys(), 
                               key=lambda s: legacy_symbol_or_allocation[s])
            assert typed_symbol == primary_symbol
            
            # Allocation should match total or primary allocation
            total_allocation = sum(legacy_symbol_or_allocation.values())
            expected_allocation = Decimal(str(total_allocation))
            assert abs(typed_allocation - expected_allocation) <= Decimal(str(DEFAULT_ATL))
        else:
            # Single symbol case
            assert typed_symbol == legacy_symbol_or_allocation
            # Single symbol allocation should be 1.0 or match specific allocation
            assert typed_allocation >= Decimal("0.0")

        # Reasoning should be equivalent
        assert legacy_reasoning == typed_reasoning

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
            legacy_engine = TECLStrategyEngine(data_provider=mock_legacy_data_provider)
            market_data = legacy_engine.get_market_data()
            indicators = legacy_engine.calculate_indicators(market_data)
            legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                legacy_engine.evaluate_tecl_strategy(indicators, market_data)
            )

            # Typed interface should also work
            typed_engine = TECLStrategyEngine(data_provider=mock_market_data_port)
            typed_signals = typed_engine.generate_signals()

            # Verify basic structure
            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Should produce equivalent signals
            self._assert_signal_equivalence(
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning,
                typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning,
                typed_signal.target_allocation.value
            )

            # Typed signal should have valid confidence and allocation
            assert Decimal("0") <= typed_signal.confidence.value <= Decimal("1")
            assert typed_signal.target_allocation.value >= Decimal("0")

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
        """Test that with feature flag on, both implementations work and produce similar results."""
        # Temporarily enable types v2 flag
        original_flag = os.environ.get("TYPES_V2_ENABLED")
        os.environ["TYPES_V2_ENABLED"] = "1"

        try:
            # Legacy should still work
            legacy_engine = TECLStrategyEngine(data_provider=mock_legacy_data_provider)
            market_data = legacy_engine.get_market_data()
            indicators = legacy_engine.calculate_indicators(market_data)
            legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                legacy_engine.evaluate_tecl_strategy(indicators, market_data)
            )

            # Typed interface with flag on
            typed_engine = TECLStrategyEngine(data_provider=mock_market_data_port)
            now = datetime.now(UTC)
            typed_signals = typed_engine.generate_signals()

            assert len(typed_signals) == 1
            typed_signal = typed_signals[0]

            # Should produce equivalent signals
            self._assert_signal_equivalence(
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning,
                typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning,
                typed_signal.target_allocation.value
            )

            # Typed signal should have valid confidence and allocation
            assert Decimal("0") <= typed_signal.confidence.value <= Decimal("1")
            assert typed_signal.target_allocation.value >= Decimal("0")

        finally:
            # Restore original flag value
            if original_flag is not None:
                os.environ["TYPES_V2_ENABLED"] = original_flag
            else:
                os.environ.pop("TYPES_V2_ENABLED", None)

    def test_bull_market_scenario_parity(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test parity in bull market conditions with both flag states."""
        for flag_state in ["0", "1"]:
            original_flag = os.environ.get("TYPES_V2_ENABLED") 
            os.environ["TYPES_V2_ENABLED"] = flag_state

            try:
                # Create engines
                legacy_engine = TECLStrategyEngine(data_provider=mock_legacy_data_provider)
                typed_engine = TECLStrategyEngine(data_provider=mock_market_data_port)

                # Get legacy result
                market_data = legacy_engine.get_market_data()
                indicators = legacy_engine.calculate_indicators(market_data)
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                    legacy_engine.evaluate_tecl_strategy(indicators, market_data)
                )

                # Get typed result
                typed_signals = typed_engine.generate_signals()
                assert len(typed_signals) == 1
                typed_signal = typed_signals[0]

                # Assert equivalence
                self._assert_signal_equivalence(
                    legacy_symbol_or_allocation, legacy_action, legacy_reasoning,
                    typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning,
                    typed_signal.target_allocation.value
                )

            finally:
                if original_flag is not None:
                    os.environ["TYPES_V2_ENABLED"] = original_flag
                else:
                    os.environ.pop("TYPES_V2_ENABLED", None)

    def test_portfolio_allocation_scenario_parity(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test parity when strategy returns portfolio allocation in both flag states."""
        for flag_state in ["0", "1"]:
            original_flag = os.environ.get("TYPES_V2_ENABLED")
            os.environ["TYPES_V2_ENABLED"] = flag_state

            try:
                # Create engines
                legacy_engine = TECLStrategyEngine(data_provider=mock_legacy_data_provider)
                typed_engine = TECLStrategyEngine(data_provider=mock_market_data_port)
                
                # Get baseline results from both engines
                market_data = legacy_engine.get_market_data()
                indicators = legacy_engine.calculate_indicators(market_data)
                legacy_symbol_or_allocation, legacy_action, legacy_reasoning = (
                    legacy_engine.evaluate_tecl_strategy(indicators, market_data)
                )
                
                typed_signals = typed_engine.generate_signals()
                
                # If we have results from both, compare them
                if typed_signals:
                    typed_signal = typed_signals[0]
                    
                    # Use our standard equivalence check
                    self._assert_signal_equivalence(
                        legacy_symbol_or_allocation, legacy_action, legacy_reasoning,
                        typed_signal.symbol.value, typed_signal.action, typed_signal.reasoning,
                        typed_signal.target_allocation.value
                    )
                    
                    # Additional checks for portfolio case
                    if isinstance(legacy_symbol_or_allocation, dict):
                        # Primary symbol should be the one with highest allocation
                        primary_symbol = max(legacy_symbol_or_allocation.keys(),
                                           key=lambda s: legacy_symbol_or_allocation[s])
                        assert typed_signal.symbol.value == primary_symbol
                    else:
                        # Single symbol case
                        assert typed_signal.symbol.value == legacy_symbol_or_allocation

            finally:
                if original_flag is not None:
                    os.environ["TYPES_V2_ENABLED"] = original_flag
                else:
                    os.environ.pop("TYPES_V2_ENABLED", None)

    def test_numerical_precision_with_decimals(
        self,
        mock_legacy_data_provider: Mock,
        mock_market_data_port: Mock,
    ) -> None:
        """Test that financial values use proper Decimal precision."""
        original_flag = os.environ.get("TYPES_V2_ENABLED")
        
        for flag_state in ["0", "1"]:
            os.environ["TYPES_V2_ENABLED"] = flag_state
            
            try:
                typed_engine = TECLStrategyEngine(data_provider=mock_market_data_port)
                typed_signals = typed_engine.generate_signals()
                
                if typed_signals:
                    typed_signal = typed_signals[0]
                    
                    # Ensure Decimal types are used for financial values
                    assert isinstance(typed_signal.confidence.value, Decimal)
                    assert isinstance(typed_signal.target_allocation.value, Decimal)
                    
                    # Values should be within reasonable ranges
                    assert Decimal("0") <= typed_signal.confidence.value <= Decimal("1")
                    assert typed_signal.target_allocation.value >= Decimal("0")
                    
                    # Should not use float equality - this is what we're testing
                    confidence_float = float(typed_signal.confidence.value)
                    # Use tolerance for any float comparisons in assertions
                    assert abs(confidence_float - 0.5) <= DEFAULT_RTL or \
                           abs(confidence_float - 0.3) <= DEFAULT_RTL or \
                           abs(confidence_float - 0.8) <= DEFAULT_RTL  # Common confidence levels
            
            finally:
                if original_flag is not None:
                    os.environ["TYPES_V2_ENABLED"] = original_flag
                else:
                    os.environ.pop("TYPES_V2_ENABLED", None)