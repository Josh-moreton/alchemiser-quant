#!/usr/bin/env python3
"""
Unit tests for TradingEngine error handling standardization.

Tests that TradingEngine uses TradingSystemErrorHandler with proper context,
categories, and re-throws typed exceptions as required.
"""

import pytest
from unittest.mock import Mock, patch

from the_alchemiser.application.trading.engine_service import TradingEngine, StrategyManagerAdapter
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    StrategyExecutionError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler
from the_alchemiser.domain.registry import StrategyType


class TestTradingEngineErrorHandling:
    """Test standardized error handling in TradingEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_trading_service_manager = Mock()
        self.mock_alpaca_manager = Mock()
        self.mock_trading_service_manager.alpaca_manager = self.mock_alpaca_manager
        self.mock_alpaca_manager.is_paper_trading = True
        self.mock_alpaca_manager.trading_client = Mock()

    @patch('the_alchemiser.application.trading.engine_service.TradingSystemErrorHandler')
    @patch('the_alchemiser.application.trading.engine_service.MarketDataService')
    def test_configuration_error_with_handler_invocation(self, mock_market_data_service, mock_error_handler_class):
        """Test that configuration errors invoke TradingSystemErrorHandler with proper context."""
        # Arrange
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Make MarketDataService raise AttributeError during initialization
        mock_market_data_service.side_effect = AttributeError("missing alpaca_manager attribute")

        # Act & Assert
        with pytest.raises(ConfigurationError, match="TradingServiceManager missing AlpacaManager for market data"):
            TradingEngine._init_with_service_manager(
                TradingEngine.__new__(TradingEngine),
                self.mock_trading_service_manager,
                {StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
                False
            )

        # Verify error handler was called with proper context
        mock_error_handler_class.assert_called_once()
        mock_error_handler.handle_error_with_context.assert_called_once()
        
        call_args = mock_error_handler.handle_error_with_context.call_args
        assert call_args[1]['should_continue'] is False
        
        context = call_args[1]['context']
        assert context.operation == "initialize_data_provider"
        assert context.component == "TradingEngine._init_with_service_manager"
        assert context.function_name == "_init_with_service_manager"

    @patch('the_alchemiser.application.trading.engine_service.TradingSystemErrorHandler')
    def test_strategy_performance_summary_error_handling(self, mock_error_handler_class):
        """Test that StrategyManagerAdapter handles errors properly and re-raises typed exceptions."""
        # Arrange
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        mock_typed_strategy_manager = Mock()
        mock_typed_strategy_manager.strategy_allocations = {
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
        # Make the method raise a generic exception
        mock_typed_strategy_manager.get_strategy_performance_summary.side_effect = RuntimeError("Performance calculation failed")
        
        adapter = StrategyManagerAdapter.__new__(StrategyManagerAdapter)
        adapter._typed = mock_typed_strategy_manager

        # Act & Assert
        with pytest.raises(StrategyExecutionError, match="Failed to retrieve strategy performance summary"):
            adapter.get_strategy_performance_summary()

        # Verify error handler was called
        mock_error_handler_class.assert_called_once()
        mock_error_handler.handle_error_with_context.assert_called_once()
        
        call_args = mock_error_handler.handle_error_with_context.call_args
        assert call_args[1]['should_continue'] is False
        
        context = call_args[1]['context']
        assert context.operation == "get_strategy_performance_summary"
        assert context.component == "StrategyManagerAdapter.get_strategy_performance_summary"

    @patch('the_alchemiser.application.trading.engine_service.TradingSystemErrorHandler')
    def test_strategy_performance_summary_attribute_error_handling(self, mock_error_handler_class):
        """Test that StrategyManagerAdapter handles AttributeError gracefully without error handler."""
        # Arrange - don't mock the error handler for this test
        mock_typed_strategy_manager = Mock()
        mock_typed_strategy_manager.strategy_allocations = {
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
        # Make the method raise AttributeError (method doesn't exist)
        del mock_typed_strategy_manager.get_strategy_performance_summary
        
        adapter = StrategyManagerAdapter.__new__(StrategyManagerAdapter)
        adapter._typed = mock_typed_strategy_manager

        # Act
        result = adapter.get_strategy_performance_summary()

        # Assert - should return default structure without calling error handler
        expected_result = {
            StrategyType.NUCLEAR.name: {"pnl": 0.0, "trades": 0},
            StrategyType.TECL.name: {"pnl": 0.0, "trades": 0}
        }
        assert result == expected_result
        
        # Error handler should not be called for AttributeError
        mock_error_handler_class.assert_not_called()

    @patch('the_alchemiser.application.trading.engine_service.TradingSystemErrorHandler')
    def test_performance_report_error_with_re_raise(self, mock_error_handler_class):
        """Test that performance report errors use error handler and re-raise typed exceptions."""
        # Arrange
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        engine = TradingEngine.__new__(TradingEngine)
        # Mock the methods that are called inside the try block
        engine.get_positions = Mock(side_effect=RuntimeError("Position fetch failed"))
        mock_strategy_manager = Mock()
        mock_strategy_manager.strategy_allocations = {StrategyType.NUCLEAR: 0.5}
        mock_strategy_manager.get_strategy_performance_summary = Mock()
        engine.strategy_manager = mock_strategy_manager
        
        # Act & Assert
        with pytest.raises(StrategyExecutionError, match="Failed to generate performance report"):
            engine.get_multi_strategy_performance_report()

        # Verify error handler was called with proper context
        mock_error_handler_class.assert_called_once()
        mock_error_handler.handle_error_with_context.assert_called_once()
        
        call_args = mock_error_handler.handle_error_with_context.call_args
        assert call_args[1]['should_continue'] is False
        
        context = call_args[1]['context']
        assert context.operation == "generate_multi_strategy_performance_report"
        assert context.component == "TradingEngine.get_multi_strategy_performance_report"

    @patch('the_alchemiser.application.trading.engine_service.TradingSystemErrorHandler')
    @patch('the_alchemiser.application.trading.engine_service.logging')
    def test_post_trade_validation_error_non_critical(self, mock_logging, mock_error_handler_class):
        """Test that post-trade validation errors use error handler but don't re-raise (non-critical).""" 
        # Arrange
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        engine = TradingEngine.__new__(TradingEngine)
        
        # Create valid orders that will pass validation
        orders_executed = [{"symbol": "AAPL"}]
        
        # Create strategy signals with invalid structure that will cause AttributeError
        # when trying to call .get() on a non-dict in the iteration loop
        strategy_signals = {StrategyType.NUCLEAR: "invalid_string_instead_of_dict"}

        # Act - should not raise exception, but should call error handler
        engine._trigger_post_trade_validation(strategy_signals, orders_executed)

        # Verify error handler was called with proper context
        mock_error_handler_class.assert_called_once()
        mock_error_handler.handle_error_with_context.assert_called_once()
        
        call_args = mock_error_handler.handle_error_with_context.call_args
        assert call_args[1]['should_continue'] is True  # Non-critical error
        
        context = call_args[1]['context']
        assert context.operation == "post_trade_validation"
        assert context.component == "TradingEngine._trigger_post_trade_validation"
        
        # Should still log the error
        mock_logging.error.assert_called_once()