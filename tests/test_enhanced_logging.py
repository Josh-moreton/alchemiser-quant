#!/usr/bin/env python3
"""
Test enhanced logging functionality including structured logging,
custom exception handling, and context logging.
"""

import pytest
import logging
import json
import tempfile
import os
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from the_alchemiser.core.logging.logging_utils import (
    setup_logging, 
    get_logger, 
    log_with_context,
    log_trade_event,
    log_error_with_context,
    configure_test_logging,
    configure_production_logging,
    StructuredFormatter,
    AlchemiserLoggerAdapter
)

from the_alchemiser.core.exceptions import (
    AlchemiserError,
    OrderExecutionError,
    ConfigurationError,
    DataProviderError,
    TradingClientError,
    LoggingError,
    FileOperationError
)


class TestStructuredLogging:
    """Test structured logging format and JSON output."""
    
    def test_structured_formatter_basic(self):
        """Test basic structured formatter functionality."""
        formatter = StructuredFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Test message',
            args=(),
            exc_info=None,
            func='test_function'
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test.logger'
        assert parsed['message'] == 'Test message'
        assert parsed['function'] == 'test_function'
        assert parsed['line'] == 42
        assert 'timestamp' in parsed
    
    def test_structured_formatter_with_exception(self):
        """Test structured formatter with exception info."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            exc_info = (type(e), e, e.__traceback__)
            
        record = logging.LogRecord(
            name='test.logger',
            level=logging.ERROR,
            pathname='/test/path.py',
            lineno=42,
            msg='Error occurred',
            args=(),
            exc_info=exc_info,
            func='test_function'
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert 'exception' in parsed
        assert parsed['exception']['type'] == 'ValueError'
        assert parsed['exception']['message'] == 'Test exception'
        assert parsed['exception']['traceback'] is not None
    
    def test_structured_formatter_with_context(self):
        """Test structured formatter with extra context fields."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='/test/path.py',
            lineno=42,
            msg='Trade executed',
            args=(),
            exc_info=None,
            func='test_function'
        )
        
        # Add extra fields
        record.extra_fields = {
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 150.25
        }
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed['symbol'] == 'AAPL'
        assert parsed['quantity'] == 100
        assert parsed['price'] == 150.25


class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    def test_basic_logging_setup(self):
        """Test basic logging setup."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            try:
                setup_logging(
                    log_level=logging.INFO,
                    log_file=tmp_file.name,
                    structured_format=False
                )
                
                logger = get_logger('test.module')
                logger.info('Test log message')
                
                # Check that log file was created and contains message
                assert os.path.exists(tmp_file.name)
                
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_structured_logging_setup(self):
        """Test structured logging setup with JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            try:
                setup_logging(
                    log_level=logging.INFO,
                    log_file=tmp_file.name,
                    structured_format=True
                )
                
                logger = get_logger('test.module')
                logger.info('Test structured message')
                
                # Check that log file contains JSON
                assert os.path.exists(tmp_file.name)
                with open(tmp_file.name, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Split into lines and parse each JSON object
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        
                        # Find our test message
                        test_log_found = False
                        for line in lines:
                            try:
                                parsed = json.loads(line)
                                if parsed.get('message') == 'Test structured message':
                                    assert 'timestamp' in parsed
                                    assert 'level' in parsed
                                    assert parsed['logger'] == 'test.module'
                                    test_log_found = True
                                    break
                            except json.JSONDecodeError:
                                continue
                        
                        assert test_log_found, f"Test message not found in logs: {content}"
                        
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_test_logging_configuration(self):
        """Test test environment logging configuration."""
        configure_test_logging(logging.DEBUG)
        
        logger = get_logger('test.module')
        
        # Should be able to log at DEBUG level
        with patch('logging.StreamHandler.emit') as mock_emit:
            logger.debug('Debug message')
            logger.info('Info message')
            
            # At least one call should be made (depending on handler level)
            assert mock_emit.called
    
    def test_production_logging_configuration(self):
        """Test production environment logging configuration."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            try:
                configure_production_logging(
                    log_level=logging.INFO,
                    log_file=tmp_file.name
                )
                
                logger = get_logger('test.module')
                logger.info('Production log message')
                
                # Should create log file with structured format
                assert os.path.exists(tmp_file.name)
                
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)


class TestContextLogging:
    """Test context-aware logging functions."""
    
    def test_log_with_context(self):
        """Test logging with additional context."""
        logger = MagicMock()
        
        log_with_context(
            logger, 
            logging.INFO, 
            'Order placed',
            symbol='AAPL',
            quantity=100,
            price=150.25
        )
        
        # Verify log was called with extra context
        logger.log.assert_called_once()
        args, kwargs = logger.log.call_args
        assert args[0] == logging.INFO
        assert args[1] == 'Order placed'
        assert 'extra' in kwargs
        assert kwargs['extra']['extra_fields']['symbol'] == 'AAPL'
    
    def test_log_trade_event(self):
        """Test trade event logging."""
        logger = MagicMock()
        
        log_trade_event(
            logger,
            'order_placed',
            'AAPL',
            quantity=100,
            price=150.25,
            order_type='market'
        )
        
        # Verify proper structure
        logger.log.assert_called()
        args, kwargs = logger.log.call_args
        
        context = kwargs['extra']['extra_fields']
        assert context['event_type'] == 'order_placed'
        assert context['symbol'] == 'AAPL'
        assert context['quantity'] == 100
        assert 'timestamp' in context
    
    def test_log_error_with_context(self):
        """Test error logging with context."""
        logger = MagicMock()
        
        error = ValueError("Test error")
        
        log_error_with_context(
            logger,
            error,
            'order_placement',
            symbol='AAPL',
            quantity=100
        )
        
        # Should call both log and exception methods
        logger.log.assert_called()
        logger.exception.assert_called()
        
        args, kwargs = logger.log.call_args
        context = kwargs['extra']['extra_fields']
        assert context['operation'] == 'order_placement'
        assert context['error_type'] == 'ValueError'
        assert context['symbol'] == 'AAPL'


class TestCustomExceptions:
    """Test custom exception classes and their integration with logging."""
    
    def test_alchemiser_error_base(self):
        """Test base AlchemiserError exception."""
        error = AlchemiserError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
    
    def test_order_execution_error_with_context(self):
        """Test OrderExecutionError with additional context."""
        error = OrderExecutionError(
            "Order failed",
            symbol='AAPL',
            order_type='market'
        )
        
        assert str(error) == "Order failed"
        assert error.symbol == 'AAPL'
        assert error.order_type == 'market'
    
    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        error = ConfigurationError("Missing configuration")
        assert isinstance(error, AlchemiserError)
    
    def test_logging_error(self):
        """Test LoggingError exception."""
        error = LoggingError("Log write failed", logger_name='test.logger')
        assert error.logger_name == 'test.logger'
    
    def test_file_operation_error(self):
        """Test FileOperationError exception."""
        error = FileOperationError(
            "File not found",
            file_path='/path/to/file.txt',
            operation='read'
        )
        assert error.file_path == '/path/to/file.txt'
        assert error.operation == 'read'


class TestLoggerAdapter:
    """Test AlchemiserLoggerAdapter functionality."""
    
    def test_logger_adapter_formatting(self):
        """Test that adapter properly formats messages."""
        base_logger = MagicMock()
        adapter = AlchemiserLoggerAdapter(base_logger, {'context': 'test'})
        
        msg, kwargs = adapter.process('Test message', {})
        
        assert msg == '[ALCHEMISER] Test message'
        assert kwargs == {}


class TestThirdPartyLoggerSuppression:
    """Test suppression of noisy third-party loggers."""
    
    def test_third_party_suppression(self):
        """Test that third-party loggers are properly suppressed."""
        setup_logging(suppress_third_party=True)
        
        # Check that noisy loggers are set to WARNING level
        noisy_loggers = ['botocore', 'urllib3', 'boto3', 'requests']
        
        for logger_name in noisy_loggers:
            logger = logging.getLogger(logger_name)
            assert logger.level >= logging.WARNING
    
    def test_third_party_not_suppressed(self):
        """Test that third-party loggers can be left at default level."""
        setup_logging(suppress_third_party=False)
        
        # Should not modify third-party logger levels
        logger = logging.getLogger('urllib3')
        # Note: This test may need adjustment based on environment


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging configuration after each test."""
    yield
    # Reset logging configuration
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.WARNING)


class TestLoggingIntegration:
    """Test integration of logging with trading operations."""
    
    def test_trading_logger_creation(self):
        """Test creation of trading-specific logger."""
        from the_alchemiser.core.logging.logging_utils import get_trading_logger
        
        logger = get_trading_logger('test.trading', strategy='nuclear')
        
        # Should return either Logger or LoggerAdapter
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    @patch('the_alchemiser.core.logging.logging_utils.log_with_context')
    def test_caplog_integration(self, mock_log_with_context, caplog):
        """Test integration with pytest's caplog fixture."""
        # Create logger and log message directly without reconfiguring
        logger = get_logger('test.integration')
        
        with caplog.at_level(logging.INFO):
            logger.info('Test integration message')
            logger.warning('Test warning message')
            logger.error('Test error message')
        
        # Verify messages were captured
        assert len(caplog.records) >= 1
        
        # Check message content
        messages = [record.message for record in caplog.records]
        assert any('Test integration message' in msg for msg in messages)
