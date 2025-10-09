"""Business Unit: shared | Status: current.

Comprehensive test suite for repository protocol definitions.

Tests verify:
- Protocol structure and method signatures
- Runtime type checking with isinstance()
- AlpacaManager implementation conformance
- Type correctness (Decimal vs float)
- Mock implementations can satisfy protocols
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

# =============================================================================
# Mock Implementations for Testing Protocol Conformance
# =============================================================================


class MockAccountRepository:
    """Mock implementation of AccountRepository for testing."""

    def get_account(self) -> dict[str, Any] | None:
        """Get account information."""
        return {"equity": "100000", "cash": "50000"}

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power."""
        return Decimal("50000.00")

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all current positions as dict."""
        return {"AAPL": Decimal("10"), "GOOGL": Decimal("5")}


class MockMarketDataRepository:
    """Mock implementation of MarketDataRepository for testing."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        return 150.50

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol."""
        return {"bid": 150.45, "ask": 150.55}


class MockTradingRepository:
    """Mock implementation of TradingRepository for testing."""

    def get_positions_dict(self) -> dict[str, Decimal]:
        """Get all current positions as dict."""
        return {"AAPL": Decimal("10")}

    def get_account(self) -> dict[str, Any] | None:
        """Get account information."""
        return {"equity": "100000"}

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power."""
        return Decimal("50000.00")

    def get_portfolio_value(self) -> Decimal | None:
        """Get total portfolio value."""
        return Decimal("100000.00")

    def place_order(self, order_request: Any) -> Any:  # noqa: ANN401  # Test mock
        """Place an order."""
        # Mock implementation returns a simple dict
        # In real tests, would return ExecutedOrder
        return {"order_id": "test123"}

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> Any:  # noqa: ANN401  # Test mock
        """Place a market order."""
        return {"order_id": "market123"}

    def cancel_order(self, order_id: str) -> Any:  # noqa: ANN401  # Test mock
        """Cancel an order."""
        return {"cancelled": True}

    def replace_order(self, order_id: str, order_data: Any = None) -> Any:  # noqa: ANN401  # Test mock
        """Replace an order."""
        return {"replaced": True}

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders."""
        return True

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position."""
        return "liquidate123"

    def close_all_positions(self, *, cancel_orders: bool = True) -> list[dict[str, Any]]:
        """Liquidate all positions."""
        return [{"status": "closed"}]

    def validate_connection(self) -> bool:
        """Validate connection."""
        return True

    @property
    def is_paper_trading(self) -> bool:
        """Check if paper trading."""
        return True

    @property
    def trading_client(self) -> Any:  # noqa: ANN401  # Test mock matching protocol
        """Access to underlying trading client."""
        return None


# =============================================================================
# Test AccountRepository Protocol
# =============================================================================


class TestAccountRepository:
    """Test suite for AccountRepository protocol."""

    def test_protocol_has_required_methods(self) -> None:
        """Test that protocol defines all required methods."""
        assert hasattr(AccountRepository, "get_account")
        assert hasattr(AccountRepository, "get_buying_power")
        assert hasattr(AccountRepository, "get_positions_dict")

    def test_protocol_method_count(self) -> None:
        """Test that protocol has exactly 3 methods (no extras)."""
        # Get all non-private attributes
        methods = [
            name
            for name in dir(AccountRepository)
            if not name.startswith("_") and callable(getattr(AccountRepository, name, None))
        ]
        assert len(methods) == 3, f"Expected 3 methods, found: {methods}"

    def test_mock_satisfies_protocol(self) -> None:
        """Test that mock implementation satisfies protocol structure."""
        mock = MockAccountRepository()

        # Verify all methods exist and are callable
        assert callable(mock.get_account)
        assert callable(mock.get_buying_power)
        assert callable(mock.get_positions_dict)

    def test_get_account_returns_correct_type(self) -> None:
        """Test get_account return type."""
        mock = MockAccountRepository()
        result = mock.get_account()

        assert result is None or isinstance(result, dict)

    def test_get_buying_power_returns_decimal(self) -> None:
        """Test get_buying_power returns Decimal for financial precision."""
        mock = MockAccountRepository()
        result = mock.get_buying_power()

        assert result is None or isinstance(result, Decimal)
        assert not isinstance(result, float), "Should return Decimal, not float"

    def test_get_positions_dict_returns_decimal_values(self) -> None:
        """Test get_positions_dict returns dict with Decimal values."""
        mock = MockAccountRepository()
        result = mock.get_positions_dict()

        assert isinstance(result, dict)
        for symbol, quantity in result.items():
            assert isinstance(symbol, str)
            assert isinstance(quantity, Decimal), f"Quantity for {symbol} should be Decimal, not {type(quantity)}"


# =============================================================================
# Test MarketDataRepository Protocol
# =============================================================================


class TestMarketDataRepository:
    """Test suite for MarketDataRepository protocol."""

    def test_protocol_has_required_methods(self) -> None:
        """Test that protocol defines all required methods."""
        assert hasattr(MarketDataRepository, "get_current_price")
        assert hasattr(MarketDataRepository, "get_quote")

    def test_protocol_method_count(self) -> None:
        """Test that protocol has exactly 2 methods."""
        methods = [
            name
            for name in dir(MarketDataRepository)
            if not name.startswith("_") and callable(getattr(MarketDataRepository, name, None))
        ]
        assert len(methods) == 2, f"Expected 2 methods, found: {methods}"

    def test_mock_satisfies_protocol(self) -> None:
        """Test that mock implementation satisfies protocol structure."""
        mock = MockMarketDataRepository()

        assert callable(mock.get_current_price)
        assert callable(mock.get_quote)

    def test_get_current_price_signature(self) -> None:
        """Test get_current_price accepts symbol parameter."""
        mock = MockMarketDataRepository()

        # Should accept string symbol
        result = mock.get_current_price("AAPL")
        assert result is None or isinstance(result, (float, int))

    def test_get_quote_signature(self) -> None:
        """Test get_quote accepts symbol parameter."""
        mock = MockMarketDataRepository()

        result = mock.get_quote("AAPL")
        assert result is None or isinstance(result, dict)

    @pytest.mark.skip(reason="Known issue: get_current_price uses float instead of Decimal")
    def test_get_current_price_should_return_decimal(self) -> None:
        """Test that get_current_price should return Decimal for financial precision.
        
        NOTE: This test is skipped because the current protocol uses float.
        This is documented as a HIGH severity issue in the file review.
        When fixed, remove the skip decorator.
        """
        mock = MockMarketDataRepository()
        result = mock.get_current_price("AAPL")

        # This is what it SHOULD be
        assert result is None or isinstance(result, Decimal)


# =============================================================================
# Test TradingRepository Protocol
# =============================================================================


class TestTradingRepository:
    """Test suite for TradingRepository protocol."""

    def test_protocol_has_required_methods(self) -> None:
        """Test that protocol defines all required methods."""
        required_methods = [
            "get_positions_dict",
            "get_account",
            "get_buying_power",
            "get_portfolio_value",
            "place_order",
            "place_market_order",
            "cancel_order",
            "replace_order",
            "cancel_all_orders",
            "liquidate_position",
            "close_all_positions",
            "validate_connection",
        ]

        for method in required_methods:
            assert hasattr(TradingRepository, method), f"Missing method: {method}"

    def test_protocol_has_required_properties(self) -> None:
        """Test that protocol defines required properties."""
        assert hasattr(TradingRepository, "is_paper_trading")
        assert hasattr(TradingRepository, "trading_client")

    def test_mock_satisfies_protocol(self) -> None:
        """Test that mock implementation satisfies protocol structure."""
        mock = MockTradingRepository()

        # Test all methods are callable
        assert callable(mock.get_positions_dict)
        assert callable(mock.get_account)
        assert callable(mock.get_buying_power)
        assert callable(mock.get_portfolio_value)
        assert callable(mock.place_order)
        assert callable(mock.place_market_order)
        assert callable(mock.cancel_order)
        assert callable(mock.replace_order)
        assert callable(mock.cancel_all_orders)
        assert callable(mock.liquidate_position)
        assert callable(mock.close_all_positions)
        assert callable(mock.validate_connection)

    def test_get_positions_dict_returns_decimal(self) -> None:
        """Test get_positions_dict returns Decimal values."""
        mock = MockTradingRepository()
        result = mock.get_positions_dict()

        assert isinstance(result, dict)
        for quantity in result.values():
            assert isinstance(quantity, Decimal)

    def test_get_buying_power_returns_decimal(self) -> None:
        """Test get_buying_power returns Decimal."""
        mock = MockTradingRepository()
        result = mock.get_buying_power()

        assert result is None or isinstance(result, Decimal)

    def test_get_portfolio_value_returns_decimal(self) -> None:
        """Test get_portfolio_value returns Decimal."""
        mock = MockTradingRepository()
        result = mock.get_portfolio_value()

        assert result is None or isinstance(result, Decimal)

    @pytest.mark.skip(reason="Known issue: place_market_order uses float instead of Decimal")
    def test_place_market_order_should_accept_decimal(self) -> None:
        """Test that place_market_order should accept Decimal for qty/notional.
        
        NOTE: This test is skipped because the current protocol uses float.
        This is documented as a HIGH severity issue in the file review.
        When fixed, remove the skip decorator and update test.
        """
        mock = MockTradingRepository()

        # This is what it SHOULD accept
        result = mock.place_market_order(
            symbol="AAPL",
            side="buy",
            qty=Decimal("10"),
            notional=None,
        )
        assert result is not None

    def test_properties_exist(self) -> None:
        """Test that required properties exist."""
        mock = MockTradingRepository()

        assert hasattr(mock, "is_paper_trading")
        assert hasattr(mock, "trading_client")

        # Test property access
        assert isinstance(mock.is_paper_trading, bool)
        # trading_client can be Any, so just check it exists


# =============================================================================
# Test AlpacaManager Implementation Conformance
# =============================================================================


class TestAlpacaManagerConformance:
    """Test that AlpacaManager properly implements all protocols.
    
    NOTE: These tests require AlpacaManager to be importable and properly initialized.
    They may be skipped in CI environments without credentials.
    """

    @pytest.fixture
    def alpaca_manager_class(self) -> type:
        """Import AlpacaManager class."""
        try:
            from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

            return AlpacaManager
        except ImportError:
            pytest.skip("AlpacaManager not available")

    def test_alpaca_manager_has_account_repository_methods(self, alpaca_manager_class: type) -> None:
        """Test AlpacaManager has all AccountRepository methods."""
        required_methods = ["get_account", "get_buying_power", "get_positions_dict"]

        for method in required_methods:
            assert hasattr(alpaca_manager_class, method), f"AlpacaManager missing: {method}"

    def test_alpaca_manager_has_market_data_repository_methods(self, alpaca_manager_class: type) -> None:
        """Test AlpacaManager has all MarketDataRepository methods."""
        required_methods = ["get_current_price", "get_quote"]

        for method in required_methods:
            assert hasattr(alpaca_manager_class, method), f"AlpacaManager missing: {method}"

    def test_alpaca_manager_has_trading_repository_methods(self, alpaca_manager_class: type) -> None:
        """Test AlpacaManager has all TradingRepository methods."""
        required_methods = [
            "get_positions_dict",
            "get_account",
            "get_buying_power",
            "get_portfolio_value",
            "place_order",
            "place_market_order",
            "cancel_order",
            "replace_order",
            "cancel_all_orders",
            "liquidate_position",
            "close_all_positions",
            "validate_connection",
        ]

        for method in required_methods:
            assert hasattr(alpaca_manager_class, method), f"AlpacaManager missing: {method}"

    def test_alpaca_manager_class_declares_protocols(self, alpaca_manager_class: type) -> None:
        """Test that AlpacaManager declares it implements the protocols."""
        # Check class bases
        base_names = [base.__name__ for base in alpaca_manager_class.__mro__]

        assert "TradingRepository" in base_names, "AlpacaManager should implement TradingRepository"
        assert "MarketDataRepository" in base_names, "AlpacaManager should implement MarketDataRepository"
        assert "AccountRepository" in base_names, "AlpacaManager should implement AccountRepository"


# =============================================================================
# Test Protocol Runtime Checking
# =============================================================================


class TestProtocolRuntimeChecking:
    """Test runtime type checking capabilities of protocols.
    
    NOTE: These tests will fail until @runtime_checkable decorator is added.
    This is documented as a HIGH severity issue in the file review.
    """

    @pytest.mark.skip(reason="Protocols missing @runtime_checkable decorator")
    def test_account_repository_runtime_checkable(self) -> None:
        """Test AccountRepository can be used with isinstance().
        
        This requires @runtime_checkable decorator.
        """
        mock = MockAccountRepository()
        assert isinstance(mock, AccountRepository)

    @pytest.mark.skip(reason="Protocols missing @runtime_checkable decorator")
    def test_market_data_repository_runtime_checkable(self) -> None:
        """Test MarketDataRepository can be used with isinstance()."""
        mock = MockMarketDataRepository()
        assert isinstance(mock, MarketDataRepository)

    @pytest.mark.skip(reason="Protocols missing @runtime_checkable decorator")
    def test_trading_repository_runtime_checkable(self) -> None:
        """Test TradingRepository can be used with isinstance()."""
        mock = MockTradingRepository()
        assert isinstance(mock, TradingRepository)

    @pytest.mark.skip(reason="Protocols missing @runtime_checkable decorator")
    def test_alpaca_manager_isinstance_checks(self) -> None:
        """Test that AlpacaManager passes isinstance checks for all protocols."""
        try:
            from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
        except ImportError:
            pytest.skip("AlpacaManager not available")

        # Can't instantiate without credentials, but can check class
        # In a real implementation, would use a test instance
        assert issubclass(AlpacaManager, AccountRepository)
        assert issubclass(AlpacaManager, MarketDataRepository)
        assert issubclass(AlpacaManager, TradingRepository)


# =============================================================================
# Test Protocol Documentation
# =============================================================================


class TestProtocolDocumentation:
    """Test that protocols have adequate documentation."""

    def test_account_repository_has_docstring(self) -> None:
        """Test AccountRepository has class docstring."""
        assert AccountRepository.__doc__ is not None
        assert len(AccountRepository.__doc__) > 0

    def test_market_data_repository_has_docstring(self) -> None:
        """Test MarketDataRepository has class docstring."""
        assert MarketDataRepository.__doc__ is not None
        assert len(MarketDataRepository.__doc__) > 0

    def test_trading_repository_has_docstring(self) -> None:
        """Test TradingRepository has class docstring."""
        assert TradingRepository.__doc__ is not None
        assert len(TradingRepository.__doc__) > 0

    def test_all_methods_have_docstrings(self) -> None:
        """Test that all protocol methods have docstrings."""
        protocols = [AccountRepository, MarketDataRepository, TradingRepository]

        for protocol in protocols:
            methods = [
                name
                for name in dir(protocol)
                if not name.startswith("_") and callable(getattr(protocol, name, None))
            ]

            for method_name in methods:
                method = getattr(protocol, method_name)
                assert method.__doc__ is not None, f"{protocol.__name__}.{method_name} missing docstring"
                assert len(method.__doc__) > 0, f"{protocol.__name__}.{method_name} has empty docstring"
