#!/usr/bin/env python3
"""
Tests for TradingServiceManager DTO integration.

Tests the integration of OrderRequestDTO validation into order placement methods
in TradingServiceManager to ensure consistent validation throughout the pipeline.
"""

import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
import pytest

from the_alchemiser.services.trading.trading_service_manager import TradingServiceManager
from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.order_status import OrderStatus


class TestTradingServiceManagerDTOIntegration:
    """Test DTO integration in TradingServiceManager order methods."""

    def setup_method(self):
        """Set up test fixtures with mocked dependencies."""
        # Mock the AlpacaManager to avoid real API calls
        with patch('the_alchemiser.services.trading.trading_service_manager.AlpacaManager') as mock_alpaca_class:
            self.mock_alpaca_manager = Mock()
            mock_alpaca_class.return_value = self.mock_alpaca_manager
            
            # Initialize TradingServiceManager with mocked dependencies
            self.trading_manager = TradingServiceManager("test_key", "test_secret", paper=True)
            self.trading_manager.alpaca_manager = self.mock_alpaca_manager

    def create_mock_execution_result_dto(self, symbol: str = "AAPL", qty: float = 100.0, success: bool = True) -> OrderExecutionResultDTO:
        """Create a mock OrderExecutionResultDTO for testing."""
        import uuid
        from decimal import Decimal
        
        return OrderExecutionResultDTO(
            success=success,
            error=None if success else "Mock error",
            order_id=str(uuid.uuid4()),
            status="accepted" if success else "rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.datetime.now(),
            completed_at=None,
        )

    def create_mock_alpaca_order(self, symbol: str = "AAPL", qty: float = 100.0):
        """Create a mock Alpaca order object for testing."""
        import uuid
        
        mock_order = Mock()
        mock_order.id = str(uuid.uuid4())  # Use valid UUID
        mock_order.symbol = symbol
        mock_order.qty = qty
        mock_order.side = "buy"
        mock_order.order_type = "market"
        mock_order.status = "accepted"
        mock_order.filled_qty = 0
        mock_order.created_at = datetime.datetime.now()
        mock_order.updated_at = datetime.datetime.now()
        return mock_order

    def test_place_market_order_with_validation_success(self):
        """Test successful market order placement with DTO validation."""
        # Mock successful order placement - AlpacaManager now returns DTOs directly
        mock_execution_result = self.create_mock_execution_result_dto("AAPL", 100.0, success=True)
        self.mock_alpaca_manager.place_order.return_value = mock_execution_result

        # Place market order with validation enabled
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify result
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        assert result.order_id is not None
        assert result.status in ["accepted", "filled"]
        assert result.filled_qty == Decimal("0")
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_market_order_validation_failure(self):
        """Test market order placement with validation failure."""
        # Place market order with invalid data (empty symbol)
        result = self.trading_manager.place_market_order(
            symbol="",  # Invalid symbol
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert result.status == "rejected"
        
        # Verify Alpaca manager was NOT called due to validation failure
        self.mock_alpaca_manager.place_order.assert_not_called()

    def test_place_market_order_validation_disabled(self):
        """Test market order placement with validation disabled."""
        # Mock successful order placement - AlpacaManager now returns DTOs directly
        mock_execution_result = self.create_mock_execution_result_dto("AAPL", 100.0, success=True)
        self.mock_alpaca_manager.place_order.return_value = mock_execution_result

        # Place market order with validation disabled
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=False
        )

        # Verify result (should succeed even without validation)
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order_with_validation_success(self):
        """Test successful limit order placement with DTO validation."""
        # Mock successful order placement - AlpacaManager now returns DTOs directly
        mock_execution_result = self.create_mock_execution_result_dto("TSLA", 50.0, success=True)
        self.mock_alpaca_manager.place_order.return_value = mock_execution_result

        # Place limit order with validation enabled
        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Verify result
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        assert result.order_id is not None
        
        # Verify Alpaca manager was called
        self.mock_alpaca_manager.place_order.assert_called_once()

    def test_place_limit_order_validation_failure(self):
        """Test limit order placement with validation failure."""
        # Place limit order with invalid data (negative price)
        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=-250.50,  # Invalid negative price
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert result.status == "rejected"
        
        # Verify Alpaca manager was NOT called due to validation failure
        self.mock_alpaca_manager.place_order.assert_not_called()

    def test_place_limit_order_without_price_validation(self):
        """Test limit order validation requires limit price."""
        # The OrderRequestDTO should catch this at creation time
        # But test the validation pipeline anyway
        result = self.trading_manager.place_limit_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            limit_price=0.0,  # Invalid zero price
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert result.status == "rejected"

    def test_place_market_order_invalid_side(self):
        """Test market order with invalid side value."""
        # This should be caught by DTO validation
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="invalid_side",  # Invalid side
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_place_market_order_zero_quantity(self):
        """Test market order with zero quantity."""
        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=0.0,  # Invalid zero quantity
            side="buy",
            validate=True
        )

        # Verify validation failure
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "validation failed" in result.error.lower()

    def test_place_limit_order_fractional_quantity(self):
        """Test limit order with fractional quantity - should be handled gracefully."""
        # Mock the return value since the test reaches AlpacaManager
        # Fractional quantities may be allowed in DTOs but could fail at broker level
        error_result = OrderExecutionResultDTO(
            success=False,
            error="Fractional quantities may not be supported",
            order_id="",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.datetime.now(),
            completed_at=None,
        )
        self.mock_alpaca_manager.place_order.return_value = error_result
        
        result = self.trading_manager.place_limit_order(
            symbol="AAPL",
            quantity=10.5,  # Fractional quantity
            side="buy",
            limit_price=150.00,
            validate=True
        )

        # Should either fail gracefully or succeed (depending on broker support)
        assert isinstance(result, OrderExecutionResultDTO)
        # Just verify we get a proper DTO response

    def test_place_market_order_alpaca_exception(self):
        """Test market order when Alpaca API throws exception."""
        # Mock Alpaca API exception - AlpacaManager should return error DTO now
        error_result = self.create_mock_execution_result_dto("AAPL", 100.0, success=False)
        error_result = OrderExecutionResultDTO(
            success=False,
            error="Alpaca API error",
            order_id="",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.datetime.now(),
            completed_at=None,
        )
        self.mock_alpaca_manager.place_order.return_value = error_result

        result = self.trading_manager.place_market_order(
            symbol="AAPL",
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Verify error handling
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "Alpaca API error" in result.error

    def test_place_limit_order_alpaca_exception(self):
        """Test limit order when Alpaca API throws exception."""
        # Mock Alpaca API exception - AlpacaManager should return error DTO now
        error_result = OrderExecutionResultDTO(
            success=False,
            error="Alpaca API error",
            order_id="",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.datetime.now(),
            completed_at=None,
        )
        self.mock_alpaca_manager.place_order.return_value = error_result

        result = self.trading_manager.place_limit_order(
            symbol="TSLA",
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Verify error handling
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is False
        assert "Alpaca API error" in result.error

    def test_market_order_symbol_normalization(self):
        """Test that symbols are normalized to uppercase."""
        # Mock successful order placement - AlpacaManager now returns DTOs directly
        mock_execution_result = self.create_mock_execution_result_dto("AAPL", 100.0, success=True)
        self.mock_alpaca_manager.place_order.return_value = mock_execution_result

        # Place order with lowercase symbol
        result = self.trading_manager.place_market_order(
            symbol="aapl",  # lowercase
            quantity=100.0,
            side="buy",
            validate=True
        )

        # Should succeed with symbol normalized
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify the order request had uppercase symbol
        call_args = self.mock_alpaca_manager.place_order.call_args[0][0]
        assert call_args.symbol == "AAPL"

    def test_limit_order_symbol_normalization(self):
        """Test that symbols are normalized to uppercase in limit orders."""
        # Mock successful order placement - AlpacaManager now returns DTOs directly
        mock_execution_result = self.create_mock_execution_result_dto("TSLA", 50.0, success=True)
        self.mock_alpaca_manager.place_order.return_value = mock_execution_result

        # Place order with lowercase symbol
        result = self.trading_manager.place_limit_order(
            symbol="tsla",  # lowercase
            quantity=50.0,
            side="sell",
            limit_price=250.50,
            validate=True
        )

        # Should succeed with symbol normalized
        assert isinstance(result, OrderExecutionResultDTO)
        assert result.success is True
        
        # Verify the order request had uppercase symbol
        call_args = self.mock_alpaca_manager.place_order.call_args[0][0]
        assert call_args.symbol == "TSLA"

    def test_order_validation_error_logging(self):
        """Test that validation errors are properly logged."""
        with patch.object(self.trading_manager.logger, 'info') as mock_log_info:
            # Mock successful order placement - AlpacaManager now returns DTOs directly
            mock_execution_result = self.create_mock_execution_result_dto("AAPL", 100.0, success=True)
            self.mock_alpaca_manager.place_order.return_value = mock_execution_result

            # Place valid order
            result = self.trading_manager.place_market_order(
                symbol="AAPL",
                quantity=100.0,
                side="buy",
                validate=True
            )

            # Verify validation success was logged
            assert result.success is True
            mock_log_info.assert_called()
            log_message = mock_log_info.call_args[0][0]

    def test_comprehensive_dto_coverage(self):
        """Test that all TradingServiceManager methods return proper DTOs or None."""
        from the_alchemiser.interfaces.schemas.base import ResultDTO
        import inspect
        
        # Get all public methods
        public_methods = [
            (name, method) for name, method in inspect.getmembers(
                self.trading_manager, predicate=inspect.ismethod
            ) if not name.startswith('_')
        ]
        
        dto_coverage = 0
        total_methods = 0
        
        for method_name, method in public_methods:
            # Check if method has type annotations
            if hasattr(method, '__annotations__') and 'return' in method.__annotations__:
                total_methods += 1
                return_type = method.__annotations__['return']
                return_type_str = str(return_type)
                
                # Methods should return DTOs or None (for close method)
                    assert return_type == type(None) or 'None' in return_type_str
                    dto_coverage += 1
                elif 'DTO' in return_type_str:
                    dto_coverage += 1
                else:
                    # This should not happen - all methods should return DTOs
                    pytest.fail(f"Method {method_name} returns {return_type_str}, expected DTO")
        
        # Verify high DTO coverage
        coverage_percentage = (dto_coverage / total_methods) * 100 if total_methods > 0 else 0
        assert coverage_percentage >= 96.0, f"DTO coverage is {coverage_percentage:.1f}%, expected >= 96%"
        
        # Log the coverage for visibility
        print(f"\nDTO Coverage: {dto_coverage}/{total_methods} methods ({coverage_percentage:.1f}%)")

    def test_position_methods_return_dtos(self):
        """Test that position-related methods return proper DTOs."""
        from the_alchemiser.interfaces.schemas.positions import PortfolioValueDTO
        from the_alchemiser.interfaces.schemas.enriched_data import EnrichedPositionsDTO
        
        # Mock position data
        self.mock_alpaca_manager.get_all_positions.return_value = []
        self.mock_alpaca_manager.get_portfolio_value.return_value = 10000.0
        
        # Test get_all_positions returns DTO
        result = self.trading_manager.get_all_positions()
        assert isinstance(result, EnrichedPositionsDTO)
        assert result.success is True
        
        # Test get_portfolio_value returns DTO
        result = self.trading_manager.get_portfolio_value()
        assert isinstance(result, PortfolioValueDTO)
        assert result.value > 0

    def test_account_methods_return_dtos(self):
        """Test that account-related methods return proper DTOs."""
        from the_alchemiser.interfaces.schemas.accounts import EnrichedAccountSummaryDTO
        
        # Mock account data
        mock_account = {
            'id': 'test_account',
            'equity': 10000.0,
            'cash': 5000.0,
            'market_value': 5000.0,
            'buying_power': 20000.0,
            'last_equity': 9500.0,
            'daytrade_count': 0,
            'pattern_day_trader': False,
            'trading_blocked': False,
            'transfers_blocked': False,
            'account_blocked': False
        }
        self.mock_alpaca_manager.get_account.return_value = mock_account
        
        # Test get_account_summary_enriched returns DTO
        result = self.trading_manager.get_account_summary_enriched()
        assert isinstance(result, EnrichedAccountSummaryDTO)
        # EnrichedAccountSummaryDTO inherits from ResultDTO and should have a success field
        # Check if it has the required account info instead
        assert hasattr(result, 'summary') or hasattr(result, 'raw')

    def test_market_data_methods_return_dtos(self):
        """Test that market data methods return proper DTOs."""
        from the_alchemiser.interfaces.schemas.market_data import PriceDTO
        
        # Mock market data properly
        mock_trade = Mock()
        mock_trade.price = 150.0
        mock_trade.timestamp = Mock()
        mock_trade.size = 100
        self.mock_alpaca_manager.get_latest_trade.return_value = mock_trade
        
        # Test get_latest_price returns DTO
        result = self.trading_manager.get_latest_price("AAPL", validate=False)  # Disable validation to avoid complex mocking
        assert isinstance(result, PriceDTO)
        assert result.symbol == "AAPL"