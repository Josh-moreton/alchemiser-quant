#!/usr/bin/env python3
"""
Unit tests for the consolidated error handling package.

Tests the new error core v2 structure with:
- ErrorContextData (frozen dataclass)
- TradingSystemErrorHandler as single facade  
- Exception translation decorators (no logging)
- ErrorScope context manager
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from dataclasses import FrozenInstanceError

from the_alchemiser.services.errors import (
    ErrorContextData,
    create_error_context,
    TradingSystemErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorScope,
    translate_service_errors,
    translate_market_data_errors,
)
from the_alchemiser.services.errors.exceptions import (
    MarketDataError,
    OrderExecutionError,
    DataProviderError,
    ConfigurationError,
)


class TestErrorContextData:
    """Test ErrorContextData frozen dataclass."""
    
    def test_creation_with_required_fields(self) -> None:
        """Test creating context with only required fields."""
        context = ErrorContextData(
            operation="test_operation",
            component="test_component"
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.function_name is None
        assert context.request_id is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.additional_data == {}
    
    def test_creation_with_all_fields(self) -> None:
        """Test creating context with all fields."""
        additional_data = {"key": "value", "count": 42}
        context = ErrorContextData(
            operation="test_operation",
            component="test_component",
            function_name="test_function",
            request_id="req_123",
            user_id="user_456",
            session_id="session_789",
            additional_data=additional_data
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.function_name == "test_function"
        assert context.request_id == "req_123"
        assert context.user_id == "user_456"
        assert context.session_id == "session_789"
        assert context.additional_data == additional_data
    
    def test_immutability(self) -> None:
        """Test that ErrorContextData is frozen/immutable."""
        context = ErrorContextData(
            operation="test_operation",
            component="test_component"
        )
        
        with pytest.raises((AttributeError, FrozenInstanceError), match="cannot assign to field|can't set attribute"):
            context.operation = "new_operation"
    
    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        context = ErrorContextData(
            operation="test_operation",
            component="test_component",
            function_name="test_function"
        )
        
        result = context.to_dict()
        
        assert result["operation"] == "test_operation"
        assert result["component"] == "test_component"
        assert result["function_name"] == "test_function"
        assert result["request_id"] is None
        assert result["user_id"] is None
        assert result["session_id"] is None
        assert result["additional_data"] == {}
        assert "timestamp" in result
        
        # Validate timestamp format
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert isinstance(timestamp, datetime)
    
    def test_factory_function(self) -> None:
        """Test the create_error_context factory function."""
        context = create_error_context(
            operation="test_operation",
            component="test_component",
            function_name="test_function",
            request_id="req_123"
        )
        
        assert isinstance(context, ErrorContextData)
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.function_name == "test_function"
        assert context.request_id == "req_123"


class TestTradingSystemErrorHandler:
    """Test TradingSystemErrorHandler functionality."""
    
    def test_categorize_error_trading(self) -> None:
        """Test error categorization for trading errors."""
        handler = TradingSystemErrorHandler()
        
        error = OrderExecutionError("Order failed")
        category = handler.categorize_error(error)
        
        assert category == ErrorCategory.TRADING
    
    def test_categorize_error_data(self) -> None:
        """Test error categorization for data errors."""
        handler = TradingSystemErrorHandler()
        
        error = MarketDataError("Data fetch failed")
        category = handler.categorize_error(error)
        
        assert category == ErrorCategory.DATA
    
    def test_categorize_error_configuration(self) -> None:
        """Test error categorization for configuration errors."""
        handler = TradingSystemErrorHandler()
        
        error = ConfigurationError("Config invalid")
        category = handler.categorize_error(error)
        
        assert category == ErrorCategory.CONFIGURATION
    
    def test_categorize_error_by_context(self) -> None:
        """Test error categorization based on context."""
        handler = TradingSystemErrorHandler()
        
        # Generic ValueError categorized by context
        error = ValueError("Something went wrong")
        
        # Trading context
        category = handler.categorize_error(error, "order execution failed")
        assert category == ErrorCategory.TRADING
        
        # Data context
        category = handler.categorize_error(error, "price data invalid")
        assert category == ErrorCategory.DATA
        
        # Strategy context
        category = handler.categorize_error(error, "signal calculation error")
        assert category == ErrorCategory.STRATEGY
        
        # Default to critical
        category = handler.categorize_error(error, "unknown context")
        assert category == ErrorCategory.CRITICAL
    
    def test_handle_error(self) -> None:
        """Test error handling creates proper ErrorDetails."""
        handler = TradingSystemErrorHandler()
        
        error = OrderExecutionError("Order failed")
        additional_data = {"symbol": "AAPL", "quantity": 100}
        
        with patch.object(handler.logger, 'error') as mock_logger:
            error_details = handler.handle_error(
                error=error,
                context="order_execution",
                component="trading_service",
                additional_data=additional_data
            )
        
        assert error_details.error == error
        assert error_details.category == ErrorCategory.TRADING
        assert error_details.context == "order_execution"
        assert error_details.component == "trading_service"
        assert error_details.additional_data == additional_data
        assert error_details.suggested_action is not None
        
        # Check that error was logged
        mock_logger.assert_called_once()
        
        # Check error was stored
        assert len(handler.errors) == 1
        assert handler.errors[0] == error_details
    
    def test_handle_error_with_context(self) -> None:
        """Test handling error with ErrorContextData."""
        handler = TradingSystemErrorHandler()
        
        context = ErrorContextData(
            operation="place_order",
            component="trading_service",
            function_name="execute_order",
            additional_data={"symbol": "AAPL"}
        )
        
        error = OrderExecutionError("Order failed")
        
        with patch.object(handler.logger, 'error') as mock_logger:
            error_details = handler.handle_error_with_context(
                error=error,
                context=context
            )
        
        assert error_details.context == "place_order"
        assert error_details.component == "trading_service"
        assert "symbol" in error_details.additional_data["additional_data"]
        
        mock_logger.assert_called_once()
    
    def test_get_error_summary(self) -> None:
        """Test error summary generation."""
        handler = TradingSystemErrorHandler()
        
        # Add errors of different categories
        handler.handle_error(
            OrderExecutionError("Order 1 failed"),
            "order_execution",
            "trading_service"
        )
        handler.handle_error(
            MarketDataError("Data fetch failed"),
            "data_fetch",
            "data_service"
        )
        handler.handle_error(
            OrderExecutionError("Order 2 failed"),
            "order_execution",
            "trading_service"
        )
        
        summary = handler.get_error_summary()
        
        # Should have trading and data errors
        assert summary["trading"] is not None
        assert summary["trading"]["count"] == 2
        assert len(summary["trading"]["errors"]) == 2
        
        assert summary["data"] is not None
        assert summary["data"]["count"] == 1
        assert len(summary["data"]["errors"]) == 1
        
        # Should not have other categories
        assert summary["critical"] is None
        assert summary["strategy"] is None
        assert summary["configuration"] is None
        assert summary["notification"] is None
        assert summary["warning"] is None
    
    def test_has_critical_errors(self) -> None:
        """Test critical error detection."""
        handler = TradingSystemErrorHandler()
        
        assert not handler.has_critical_errors()
        
        # Add non-critical error
        handler.handle_error(
            OrderExecutionError("Order failed"),
            "order_execution", 
            "trading_service"
        )
        assert not handler.has_critical_errors()
        
        # Add critical error
        handler.handle_error(
            Exception("System failure"),
            "system_startup",
            "core_system"
        )
        assert handler.has_critical_errors()
    
    def test_has_trading_errors(self) -> None:
        """Test trading error detection."""
        handler = TradingSystemErrorHandler()
        
        assert not handler.has_trading_errors()
        
        # Add non-trading error
        handler.handle_error(
            MarketDataError("Data failed"),
            "data_fetch",
            "data_service"
        )
        assert not handler.has_trading_errors()
        
        # Add trading error
        handler.handle_error(
            OrderExecutionError("Order failed"),
            "order_execution",
            "trading_service"
        )
        assert handler.has_trading_errors()
    
    def test_clear_errors(self) -> None:
        """Test clearing errors."""
        handler = TradingSystemErrorHandler()
        
        # Add some errors
        handler.handle_error(
            OrderExecutionError("Order failed"),
            "order_execution",
            "trading_service"
        )
        
        assert len(handler.errors) == 1
        
        handler.clear_errors()
        
        assert len(handler.errors) == 0
        assert not handler.has_trading_errors()
        assert not handler.has_critical_errors()


class TestTranslationDecorators:
    """Test exception translation decorators."""
    
    def test_translate_service_errors_success(self) -> None:
        """Test decorator passes through successful calls."""
        @translate_service_errors()
        def success_function() -> str:
            return "success"
        
        result = success_function()
        assert result == "success"
    
    def test_translate_service_errors_mapped_exception(self) -> None:
        """Test decorator translates mapped exceptions."""
        @translate_service_errors()
        def failing_function() -> None:
            raise ConnectionError("Connection failed")
        
        with pytest.raises(DataProviderError) as exc_info:
            failing_function()
        
        assert "Service error in failing_function" in str(exc_info.value)
        assert exc_info.value.__cause__.__class__ == ConnectionError
    
    def test_translate_service_errors_unmapped_exception(self) -> None:
        """Test decorator translates unmapped exceptions to default."""
        @translate_service_errors()
        def failing_function() -> None:
            raise RuntimeError("Runtime error")
        
        with pytest.raises(DataProviderError) as exc_info:
            failing_function()
        
        assert "Unexpected error in failing_function" in str(exc_info.value)
        assert exc_info.value.__cause__.__class__ == RuntimeError
    
    def test_translate_service_errors_with_default_return(self) -> None:
        """Test decorator returns default value instead of raising."""
        @translate_service_errors(default_return="default")
        def failing_function() -> str:
            raise ConnectionError("Connection failed")
        
        result = failing_function()
        assert result == "default"
    
    def test_translate_market_data_errors(self) -> None:
        """Test market data specific error translation."""
        @translate_market_data_errors()
        def failing_function() -> None:
            raise TimeoutError("Timeout")
        
        with pytest.raises(MarketDataError) as exc_info:
            failing_function()
        
        assert "Service error in failing_function" in str(exc_info.value)
        assert exc_info.value.__cause__.__class__ == TimeoutError
    
    def test_decorators_do_not_log(self) -> None:
        """Test that decorators do not perform logging."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            @translate_service_errors()
            def failing_function() -> None:
                raise ConnectionError("Connection failed")
            
            with pytest.raises(DataProviderError):
                failing_function()
            
            # Decorators should not log - logging is handled by handlers
            mock_logger.error.assert_not_called()
            mock_logger.warning.assert_not_called()
            mock_logger.info.assert_not_called()


class TestErrorScope:
    """Test ErrorScope context manager."""
    
    def test_error_scope_success(self) -> None:
        """Test error scope with successful operation."""
        mock_handler = Mock()
        
        with ErrorScope(mock_handler) as scope:
            result = "success"
        
        assert isinstance(scope, ErrorScope)
        mock_handler.log_and_handle.assert_not_called()
    
    def test_error_scope_with_exception_reraise(self) -> None:
        """Test error scope with exception and reraise=True."""
        mock_handler = Mock()
        test_error = ValueError("Test error")
        
        with pytest.raises(ValueError):
            with ErrorScope(mock_handler, reraise=True):
                raise test_error
        
        mock_handler.log_and_handle.assert_called_once_with(test_error, {})
    
    def test_error_scope_with_exception_suppress(self) -> None:
        """Test error scope with exception and reraise=False."""
        mock_handler = Mock()
        test_error = ValueError("Test error")
        
        with ErrorScope(mock_handler, reraise=False):
            raise test_error
        
        mock_handler.log_and_handle.assert_called_once_with(test_error, {})
    
    def test_error_scope_with_context(self) -> None:
        """Test error scope with logging context."""
        mock_handler = Mock()
        test_error = ValueError("Test error")
        context = {"operation": "test_op", "component": "test_comp"}
        
        with pytest.raises(ValueError):
            with ErrorScope(mock_handler, context=context, reraise=True):
                raise test_error
        
        mock_handler.log_and_handle.assert_called_once_with(test_error, context)


class TestBackwardCompatibility:
    """Test backward compatibility features."""
    
    def test_error_context_alias(self) -> None:
        """Test that ErrorContext alias still works."""
        from the_alchemiser.services.errors import ErrorContext
        
        # ErrorContext should be an alias for ErrorScope
        assert ErrorContext is ErrorScope
    
    def test_imports_work(self) -> None:
        """Test that all expected imports work."""
        from the_alchemiser.services.errors import (
            TradingSystemErrorHandler,
            ErrorContextData,
            ErrorScope,
            ErrorCategory,
            ErrorSeverity,
            translate_service_errors,
            create_service_logger,  # Only remaining legacy import
        )
        
        # Should be able to create instances
        handler = TradingSystemErrorHandler()
        context = ErrorContextData("test_op", "test_comp")
        logger = create_service_logger("test_service")
        
        assert isinstance(handler, TradingSystemErrorHandler)
        assert isinstance(context, ErrorContextData)
        assert logger is not None

    def test_deprecated_apis_raise_warnings(self) -> None:
        """Test that deprecated APIs raise proper warnings/errors."""
        import warnings
        import importlib
        import sys
        
        # Remove the module if it's already imported to test fresh import
        module_name = "the_alchemiser.services.errors.error_handling"
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Test that importing error_handling module issues deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import the module directly to trigger warning
            import the_alchemiser.services.errors.error_handling as error_handling
            
            # Should have at least one deprecation warning
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "deprecated" in str(deprecation_warnings[0].message)
        
        # Test that using deprecated classes raises errors
        with pytest.raises(DeprecationWarning):
            error_handling.ErrorHandler()
        
        with pytest.raises(DeprecationWarning):
            error_handling.ServiceMetrics()
        
        with pytest.raises(DeprecationWarning):
            error_handling.handle_service_errors()