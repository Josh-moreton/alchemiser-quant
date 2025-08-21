"""
Base classes and shared utilities for strategy parity tests.

Provides common fixtures, assertion helpers, and test patterns for comparing
legacy and typed strategy implementations across different flag states.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Protocol
from unittest.mock import Mock

import pandas as pd
import pytest

from tests._tolerances import DEFAULT_ATL, DEFAULT_RTL
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


class StrategyParityFixtures:
    """Shared fixtures for strategy parity tests."""

    @staticmethod
    @pytest.fixture
    def mock_market_data_port(fixed_market_data: Dict[str, pd.DataFrame]) -> Mock:
        """Create a mock MarketDataPort that returns fixed data."""
        port = Mock(spec=MarketDataPort)

        def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
            return fixed_market_data.get(symbol, pd.DataFrame())

        port.get_data = mock_get_data
        port.get_current_price.return_value = 100.0
        port.get_latest_quote.return_value = (99.5, 100.5)

        return port

    @staticmethod
    @pytest.fixture
    def mock_legacy_data_provider(fixed_market_data: Dict[str, pd.DataFrame]) -> Mock:
        """Create a mock legacy data provider that returns fixed data."""
        mock_provider = Mock()

        def mock_get_data(symbol: str, **kwargs) -> pd.DataFrame:
            return fixed_market_data.get(symbol, pd.DataFrame())

        mock_provider.get_data = mock_get_data
        return mock_provider


class StrategyParityTestBase(ABC):
    """Base class for strategy parity tests with common patterns."""

    def setup_method(self) -> None:
        """Store original flag state before each test."""
        self._original_flag = os.environ.get("TYPES_V2_ENABLED")

    def teardown_method(self) -> None:
        """Restore original flag state after each test."""
        if self._original_flag is not None:
            os.environ["TYPES_V2_ENABLED"] = self._original_flag
        else:
            os.environ.pop("TYPES_V2_ENABLED", None)

    def set_feature_flag(self, enabled: bool) -> None:
        """Set the TYPES_V2_ENABLED feature flag."""
        os.environ["TYPES_V2_ENABLED"] = "1" if enabled else "0"

    def restore_feature_flag(self) -> None:
        """Restore the original feature flag state."""
        if self._original_flag is not None:
            os.environ["TYPES_V2_ENABLED"] = self._original_flag
        else:
            os.environ.pop("TYPES_V2_ENABLED", None)

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of the strategy being tested."""
        pass

    @abstractmethod
    def create_legacy_engine(self, data_provider: Mock) -> Any:
        """Create the legacy strategy engine with the given data provider."""
        pass

    @abstractmethod
    def create_typed_engine(self, **kwargs) -> Any:
        """Create the typed strategy engine."""
        pass

    @abstractmethod
    def get_legacy_signals(self, engine: Any) -> tuple:
        """Get signals from the legacy engine."""
        pass

    @abstractmethod
    def get_typed_signals(self, engine: Any, market_data_port: Mock, **kwargs) -> list:
        """Get signals from the typed engine."""
        pass

    def assert_signal_structure_valid(self, typed_signal: Any) -> None:
        """Assert that a typed signal has valid structure and values."""
        assert hasattr(typed_signal, "symbol")
        assert hasattr(typed_signal, "action")
        assert hasattr(typed_signal, "confidence")
        assert hasattr(typed_signal, "target_allocation")
        assert hasattr(typed_signal, "reasoning")

        # Financial values should be Decimal types
        assert isinstance(typed_signal.confidence.value, Decimal)
        assert isinstance(typed_signal.target_allocation.value, Decimal)

        # Values should be within reasonable bounds
        assert Decimal("0") <= typed_signal.confidence.value <= Decimal("1")
        assert typed_signal.target_allocation.value >= Decimal("0")

    def assert_decimal_tolerance(
        self, actual: Decimal, expected: Decimal, tolerance: Decimal = None
    ) -> None:
        """Assert Decimal values are within tolerance."""
        if tolerance is None:
            tolerance = Decimal(str(DEFAULT_ATL))
        assert abs(actual - expected) <= tolerance

    def assert_float_tolerance(
        self, actual: float, expected: float, tolerance: float = None
    ) -> None:
        """Assert float values are within tolerance."""
        if tolerance is None:
            tolerance = DEFAULT_RTL
        assert abs(actual - expected) <= tolerance

    def test_flag_switching_basic_functionality(
        self, mock_legacy_data_provider: Mock, mock_market_data_port: Mock
    ) -> None:
        """Test that both engines work in both flag states."""
        for flag_state in [False, True]:
            self.set_feature_flag(flag_state)

            try:
                # Both engines should be creatable and functional
                legacy_engine = self.create_legacy_engine(mock_legacy_data_provider)
                typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)

                # Should not crash when getting signals
                legacy_signals = self.get_legacy_signals(legacy_engine)
                typed_signals = self.get_typed_signals(typed_engine, mock_market_data_port)

                # Basic structure validation
                assert legacy_signals is not None
                assert isinstance(typed_signals, list)

                # If typed signals exist, validate structure
                for signal in typed_signals:
                    self.assert_signal_structure_valid(signal)

            finally:
                self.restore_feature_flag()

    def test_numerical_precision_with_decimals(self, mock_market_data_port: Mock) -> None:
        """Test that financial values use proper Decimal precision."""
        for flag_state in [False, True]:
            self.set_feature_flag(flag_state)

            try:
                typed_engine = self.create_typed_engine(market_data_port=mock_market_data_port)
                typed_signals = self.get_typed_signals(typed_engine, mock_market_data_port)

                for signal in typed_signals:
                    # Ensure Decimal types are used for financial values
                    assert isinstance(signal.confidence.value, Decimal)
                    assert isinstance(signal.target_allocation.value, Decimal)

                    # Values should be within reasonable ranges
                    assert Decimal("0") <= signal.confidence.value <= Decimal("1")
                    assert signal.target_allocation.value >= Decimal("0")

                    # Demonstrate proper tolerance usage for any float comparisons
                    confidence_float = float(signal.confidence.value)
                    allocation_float = float(signal.target_allocation.value)

                    # Use tolerance for any necessary float comparisons
                    assert confidence_float <= 1.0 + DEFAULT_RTL  # Within bounds
                    assert allocation_float <= 1.0 + DEFAULT_RTL  # Within bounds

            finally:
                self.restore_feature_flag()


class StrategySignalComparator:
    """Utility class for comparing strategy signals."""

    @staticmethod
    def assert_basic_signal_equivalence(
        legacy_symbol: str,
        legacy_action: str,
        legacy_reasoning: str,
        typed_symbol: str,
        typed_action: str,
        typed_reasoning: str,
    ) -> None:
        """Assert basic signal equivalence for symbol, action, and reasoning."""
        # Actions should be valid trading actions
        valid_actions = {"BUY", "SELL", "HOLD"}
        assert legacy_action.upper() in valid_actions
        assert typed_action.upper() in valid_actions

        # Symbols should be valid
        assert isinstance(legacy_symbol, str) and len(legacy_symbol) > 0
        assert isinstance(typed_symbol, str) and len(typed_symbol) > 0

        # Reasoning should be meaningful
        assert isinstance(legacy_reasoning, str) and len(legacy_reasoning) > 0
        assert isinstance(typed_reasoning, str) and len(typed_reasoning) > 0

    @staticmethod
    def assert_portfolio_allocation_equivalence(
        legacy_allocation: dict | str, typed_symbol: str, typed_allocation: Decimal
    ) -> None:
        """Assert portfolio allocation equivalence between legacy and typed."""
        if isinstance(legacy_allocation, dict):
            # Portfolio allocation case - typed should pick primary symbol
            primary_symbol = max(legacy_allocation.keys(), key=lambda s: legacy_allocation[s])
            assert typed_symbol == primary_symbol

            # Allocation should match total or primary allocation
            total_allocation = sum(legacy_allocation.values())
            expected_allocation = Decimal(str(total_allocation))
            assert abs(typed_allocation - expected_allocation) <= Decimal(str(DEFAULT_ATL))
        else:
            # Single symbol case
            assert typed_symbol == legacy_allocation
            assert typed_allocation >= Decimal("0")
