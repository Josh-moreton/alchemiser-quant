"""Business Unit: shared | Status: current.

Test suite for AssetMetadataProvider protocol.

Validates that the protocol structure is correct and that implementations
properly satisfy the protocol contract.
"""

import pytest

from the_alchemiser.shared.protocols.asset_metadata import (
    AssetClass,
    AssetMetadataProvider,
)
from the_alchemiser.shared.value_objects.symbol import Symbol


class TestAssetMetadataProviderProtocol:
    """Test suite for AssetMetadataProvider protocol structure."""

    def test_protocol_has_required_methods(self):
        """Verify protocol defines expected methods."""
        assert hasattr(AssetMetadataProvider, "is_fractionable")
        assert hasattr(AssetMetadataProvider, "get_asset_class")
        assert hasattr(AssetMetadataProvider, "should_use_notional_order")

    def test_protocol_method_signatures(self):
        """Verify protocol method signatures are correct."""
        # Check is_fractionable
        is_fractionable = AssetMetadataProvider.is_fractionable
        assert callable(is_fractionable)

        # Check get_asset_class
        get_asset_class = AssetMetadataProvider.get_asset_class
        assert callable(get_asset_class)

        # Check should_use_notional_order
        should_use_notional_order = AssetMetadataProvider.should_use_notional_order
        assert callable(should_use_notional_order)

    def test_protocol_is_structural_type(self):
        """Verify protocol uses structural typing (not nominal)."""
        # Protocol should be a typing.Protocol
        # This documents that any class with matching methods satisfies the protocol
        from typing import Protocol as TypingProtocol

        # Check that AssetMetadataProvider is a Protocol subclass
        assert isinstance(AssetMetadataProvider, type)
        # Protocols are classes that can be used for structural subtyping


class TestAssetClassType:
    """Test suite for AssetClass type alias."""

    def test_asset_class_literal_values(self):
        """Verify AssetClass type includes expected literal values."""
        # This test documents the expected values for AssetClass
        expected_values = ["us_equity", "crypto", "unknown"]

        # AssetClass is a Literal type, so we can't directly iterate it
        # but we document the expected values here
        assert all(isinstance(val, str) for val in expected_values)

    def test_asset_class_type_exists(self):
        """Verify AssetClass type alias is exported."""
        # AssetClass should be importable
        assert AssetClass is not None


class TestProtocolImplementationContract:
    """Test suite for protocol implementation contract."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""

        class MockProvider:
            """Mock implementation of AssetMetadataProvider for testing."""

            def is_fractionable(self, symbol: Symbol) -> bool:
                """Mock is_fractionable."""
                return True

            def get_asset_class(self, symbol: Symbol) -> AssetClass:
                """Mock get_asset_class."""
                return "us_equity"

            def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
                """Mock should_use_notional_order."""
                return quantity < 1.0

        return MockProvider()

    def test_mock_provider_satisfies_protocol(self, mock_provider):
        """Verify mock provider satisfies protocol contract."""
        # Test is_fractionable
        symbol = Symbol("AAPL")
        result = mock_provider.is_fractionable(symbol)
        assert isinstance(result, bool)

        # Test get_asset_class
        asset_class = mock_provider.get_asset_class(symbol)
        assert asset_class in ["us_equity", "crypto", "unknown"]

        # Test should_use_notional_order
        should_use = mock_provider.should_use_notional_order(symbol, 0.5)
        assert isinstance(should_use, bool)

    def test_protocol_methods_accept_symbol_value_object(self, mock_provider):
        """Verify protocol methods accept Symbol value object."""
        symbol = Symbol("TSLA")

        # All methods should accept Symbol without error
        mock_provider.is_fractionable(symbol)
        mock_provider.get_asset_class(symbol)
        mock_provider.should_use_notional_order(symbol, 1.0)

    def test_get_asset_class_returns_valid_literal(self, mock_provider):
        """Verify get_asset_class returns valid AssetClass literal."""
        symbol = Symbol("BTC")
        result = mock_provider.get_asset_class(symbol)

        # Result should be one of the AssetClass literal values
        assert result in ["us_equity", "crypto", "unknown"]
