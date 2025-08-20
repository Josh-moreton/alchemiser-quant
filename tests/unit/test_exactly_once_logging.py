#!/usr/bin/env python3
"""
Test exactly-once logging behavior in CLI and main.

Verifies that each error is logged exactly once by the TradingSystemErrorHandler
and that Rich console output is separate from logging.
"""

import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError, 
    StrategyExecutionError,
    TradingClientError
)


class TestMainExactlyOnceLogging:
    """Test main.py error handling produces exactly one log entry per error."""
    
    def test_main_configuration_error_single_log(self, caplog):
        """Test that main() configuration error is logged exactly once."""
        from the_alchemiser.main import main
        
        # Mock the argument parser to return controlled args
        mock_args = Mock()
        mock_args.mode = "signal"
        mock_args.live = False
        mock_args.ignore_market_hours = False
        
        with patch('the_alchemiser.main.create_argument_parser') as mock_parser:
            mock_parser.return_value.parse_args.return_value = mock_args
            
            # Mock the TradingSystem to raise ConfigurationError at initialization
            with patch('the_alchemiser.main.TradingSystem') as mock_system_class:
                mock_system_class.side_effect = ConfigurationError("Test config error")
                
                # Mock the render functions - they're imported inside main()
                with patch('the_alchemiser.interface.cli.cli_formatter.render_header'), \
                     patch('the_alchemiser.interface.cli.cli_formatter.render_footer'), \
                     patch('the_alchemiser.main.configure_application_logging'), \
                     patch('the_alchemiser.main.generate_request_id'), \
                     patch('the_alchemiser.main.set_request_id'):
                    
                    # Clear caplog before test
                    caplog.clear()
                    
                    # Execute main and expect False
                    result = main(argv=["signal"])
                    
                    assert result is False
                    
                    # Verify exactly one error log was generated
                    error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
                    assert len(error_logs) == 1, f"Expected exactly 1 error log, got {len(error_logs)}"
                    
                    # Verify the log content
                    error_log = error_logs[0]
                    assert "Test config error" in error_log.message
                    assert "main" in error_log.message

    def test_trading_system_analyze_signals_error_single_log(self, caplog):
        """Test that TradingSystem.analyze_signals error is logged exactly once."""
        from the_alchemiser.main import TradingSystem
        
        # Mock the SignalAnalyzer to raise StrategyExecutionError
        with patch('the_alchemiser.main.load_settings') as mock_load_settings, \
             patch('the_alchemiser.main.get_logger') as mock_get_logger, \
             patch('the_alchemiser.interface.cli.signal_analyzer.SignalAnalyzer') as mock_analyzer_class, \
             patch('the_alchemiser.main.TradingSystemErrorHandler') as mock_handler_class:
            
            # Mock settings and logger
            mock_settings = Mock()
            mock_load_settings.return_value = mock_settings
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Mock error handler
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler
            
            # Mock analyzer to raise error
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.run.side_effect = StrategyExecutionError("Test strategy error")
            
            # Clear caplog before test
            caplog.clear()
            
            # Create system and call analyze_signals
            system = TradingSystem()
            result = system.analyze_signals()
            
            assert result is False
            
            # Verify error handler was called exactly once
            assert mock_handler.handle_error.call_count == 1, f"Expected exactly 1 call to handle_error, got {mock_handler.handle_error.call_count}"
            
            # Verify call arguments
            call_args = mock_handler.handle_error.call_args
            assert call_args[1]['context'] == "signal analysis operation"
            assert call_args[1]['component'] == "TradingSystem.analyze_signals"

    def test_trading_system_execute_trading_error_single_log(self, caplog):
        """Test that TradingSystem.execute_trading error is logged exactly once."""
        from the_alchemiser.main import TradingSystem
        
        # Mock the TradingExecutor to raise TradingClientError
        with patch('the_alchemiser.main.load_settings'), \
             patch('the_alchemiser.main.get_logger'), \
             patch('the_alchemiser.interface.cli.trading_executor.TradingExecutor') as mock_executor_class:
            
            mock_executor = Mock()
            mock_executor_class.return_value = mock_executor
            mock_executor.run.side_effect = TradingClientError("Test trading error")
            
            # Clear caplog before test
            caplog.clear()
            
            # Create system and call execute_trading
            system = TradingSystem()
            result = system.execute_trading(live_trading=False, ignore_market_hours=True)
            
            assert result is False
            
            # Verify exactly one error log was generated
            error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
            assert len(error_logs) == 1, f"Expected exactly 1 error log, got {len(error_logs)}"
            
            # Verify the log content
            error_log = error_logs[0]
            assert "Test trading error" in error_log.message
            assert "TradingSystem.execute_trading" in error_log.message


class TestTradingExecutorExactlyOnceLogging:
    """Test TradingExecutor error handling produces exactly one log entry per error."""
    
    def test_trading_executor_no_duplicate_logging(self, caplog):
        """Test that TradingExecutor.run() doesn't produce duplicate logs."""
        from the_alchemiser.interface.cli.trading_executor import TradingExecutor
        
        # Create a properly structured mock settings object
        mock_settings = Mock()
        mock_strategy = Mock()
        mock_strategy.default_strategy_allocations = {
            "nuclear": 0.3, "tecl": 0.5, "klm": 0.2
        }
        mock_settings.strategy = mock_strategy
        
        executor = TradingExecutor(
            settings=mock_settings, 
            live_trading=False, 
            ignore_market_hours=True
        )
        
        # Mock the _create_trading_engine to raise TradingClientError
        with patch.object(executor, '_create_trading_engine') as mock_create:
            mock_create.side_effect = TradingClientError("Test executor error")
            
            # Mock the _handle_trading_error to track calls
            with patch.object(executor, '_handle_trading_error') as mock_handle:
                # Clear caplog before test
                caplog.clear()
                
                # Execute run and expect False
                result = executor.run()
                
                assert result is False
                
                # Verify _handle_trading_error was called exactly once
                assert mock_handle.call_count == 1, f"Expected exactly 1 call to _handle_trading_error, got {mock_handle.call_count}"
                
                # Verify no inline error logs were generated (should be 0 since we removed them)
                error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
                # The _handle_trading_error mock won't actually log, so should be 0
                assert len(error_logs) == 0, f"Expected 0 inline error logs, got {len(error_logs)}"


class TestTradingSystemErrorHandlerLogging:
    """Test that TradingSystemErrorHandler handles logging correctly."""
    
    def test_error_handler_single_log_per_error(self, caplog):
        """Test that ErrorHandler.handle_error logs exactly once per error.""" 
        # Clear caplog before test
        caplog.clear()
        
        handler = TradingSystemErrorHandler()
        test_error = ConfigurationError("Test configuration error")
        
        # Handle the error
        details = handler.handle_error(
            error=test_error,
            context="test context",
            component="test.component",
            additional_data={"test": "data"}
        )
        
        # Verify exactly one error log was generated
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 1, f"Expected exactly 1 error log, got {len(error_logs)}"
        
        # Verify the log content
        error_log = error_logs[0]
        assert "CONFIGURATION ERROR in test.component" in error_log.message
        assert "Test configuration error" in error_log.message
        
        # Verify error details were recorded
        assert len(handler.errors) == 1
        assert handler.errors[0] == details
        
    def test_multiple_errors_separate_logs(self, caplog):
        """Test that multiple errors each get their own log entry."""
        # Clear caplog before test
        caplog.clear()
        
        handler = TradingSystemErrorHandler()
        
        # Handle first error
        error1 = ConfigurationError("First error")
        handler.handle_error(error1, "context1", "component1")
        
        # Handle second error  
        error2 = StrategyExecutionError("Second error")
        handler.handle_error(error2, "context2", "component2")
        
        # Verify exactly two error logs were generated
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 2, f"Expected exactly 2 error logs, got {len(error_logs)}"
        
        # Verify both errors are in the handler
        assert len(handler.errors) == 2
        assert str(handler.errors[0].error) == "First error"
        assert str(handler.errors[1].error) == "Second error"