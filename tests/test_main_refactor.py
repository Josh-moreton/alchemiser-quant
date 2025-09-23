#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Test for main.py entry point functionality.

Tests that the refactored main.py correctly handles programmatic calls
and delegates to appropriate orchestration modules.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from the_alchemiser.main import main


class TestMainEntryPoint:
    """Test the main entry point functionality."""

    def test_main_imports_successfully(self) -> None:
        """Test that main module imports without errors."""
        # This test passes if imports work
        assert main is not None

    @patch('the_alchemiser.main.TradingSystem')
    @patch('the_alchemiser.main.configure_application_logging')
    @patch('the_alchemiser.main.generate_request_id')
    @patch('the_alchemiser.main.set_request_id')
    def test_main_trading_success_flow(
        self, 
        mock_set_request_id: Mock, 
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system: Mock
    ) -> None:
        """Test successful trading execution through main entry point."""
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_system_instance = Mock()
        mock_trading_system.return_value = mock_system_instance
        
        # Mock successful trading result
        mock_result = Mock()
        mock_result.success = True
        mock_system_instance.execute_trading.return_value = mock_result
        
        # Test main entry point with trade command
        result = main(["trade"])
        
        # Verify calls
        mock_configure_logging.assert_called_once()
        mock_generate_request_id.assert_called_once()
        mock_set_request_id.assert_called_once_with("test-request-id")
        mock_trading_system.assert_called_once()
        mock_system_instance.execute_trading.assert_called_once_with(
            show_tracking=False,
            export_tracking_json=None
        )
        
        # Verify result
        assert result == mock_result

    @patch('the_alchemiser.main.TradingSystem')
    @patch('the_alchemiser.main.configure_application_logging')
    @patch('the_alchemiser.main.generate_request_id')
    @patch('the_alchemiser.main.set_request_id')
    def test_main_with_tracking_options(
        self, 
        mock_set_request_id: Mock, 
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system: Mock
    ) -> None:
        """Test main with tracking options."""
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_system_instance = Mock()
        mock_trading_system.return_value = mock_system_instance
        
        # Mock successful trading result
        mock_result = Mock()
        mock_result.success = True
        mock_system_instance.execute_trading.return_value = mock_result
        
        # Test main with tracking options
        result = main(["trade", "--show-tracking", "--export-tracking-json", "/tmp/test.json"])
        
        # Verify calls
        mock_system_instance.execute_trading.assert_called_once_with(
            show_tracking=True,
            export_tracking_json="/tmp/test.json"
        )

    def test_main_defaults_to_trade_mode(self) -> None:
        """Test that main defaults to trade mode when no arguments provided."""
        with patch('the_alchemiser.main.TradingSystem') as mock_trading_system, \
             patch('the_alchemiser.main.configure_application_logging'), \
             patch('the_alchemiser.main.generate_request_id'), \
             patch('the_alchemiser.main.set_request_id'):
            
            mock_system_instance = Mock()
            mock_trading_system.return_value = mock_system_instance
            mock_result = Mock()
            mock_result.success = True
            mock_system_instance.execute_trading.return_value = mock_result
            
            # Test with empty arguments
            result = main([])
            
            # Should still call execute_trading
            mock_system_instance.execute_trading.assert_called_once_with(
                show_tracking=False,
                export_tracking_json=None
            )

    def test_main_unknown_mode_returns_false(self) -> None:
        """Test that unknown modes return False."""
        with patch('the_alchemiser.main.TradingSystem') as mock_trading_system, \
             patch('the_alchemiser.main.configure_application_logging'), \
             patch('the_alchemiser.main.generate_request_id'), \
             patch('the_alchemiser.main.set_request_id'):
            
            mock_system_instance = Mock()
            mock_trading_system.return_value = mock_system_instance
            
            # Test with unknown mode
            result = main(["unknown"])
            
            # Should not call execute_trading and should return False
            mock_system_instance.execute_trading.assert_not_called()
            assert result is False

    @patch('the_alchemiser.main.TradingSystemErrorHandler')
    @patch('the_alchemiser.main.TradingSystem')
    @patch('the_alchemiser.main.configure_application_logging')
    @patch('the_alchemiser.main.generate_request_id')
    @patch('the_alchemiser.main.set_request_id')
    def test_main_configuration_error_handling(
        self, 
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system: Mock,
        mock_error_handler_class: Mock
    ) -> None:
        """Test main function handles configuration errors properly."""
        from the_alchemiser.shared.types.exceptions import ConfigurationError
        
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Mock TradingSystem to raise ConfigurationError
        mock_trading_system.side_effect = ConfigurationError("Test config error")
        
        # Call main
        result = main(["trade"])
        
        # Assertions
        assert result is False
        mock_error_handler.handle_error.assert_called_once()


class TestModuleEntryPoint:
    """Test the __main__.py module entry point."""

    def test_module_entry_point_imports(self) -> None:
        """Test that __main__ module imports successfully."""
        # This should not raise an exception
        from the_alchemiser import __main__
        assert __main__ is not None

    @patch('the_alchemiser.__main__.main')
    @patch('sys.exit')
    def test_module_run_success(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test successful module run."""
        from the_alchemiser.__main__ import run
        
        # Mock successful trading result
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result
        
        # Test run function
        run()
        
        # Verify calls
        mock_main.assert_called_once_with(["trade"])
        mock_exit.assert_called_once_with(0)

    @patch('the_alchemiser.__main__.main')
    @patch('sys.exit')
    def test_module_run_failure(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test module run with failure."""
        from the_alchemiser.__main__ import run
        
        # Mock failed trading result
        mock_result = Mock()
        mock_result.success = False
        mock_main.return_value = mock_result
        
        # Test run function
        run()
        
        # Verify calls
        mock_main.assert_called_once_with(["trade"])
        mock_exit.assert_called_once_with(1)

    @patch('the_alchemiser.__main__.main')
    @patch('sys.exit')
    def test_module_run_boolean_result(self, mock_exit: Mock, mock_main: Mock) -> None:
        """Test module run with boolean result."""
        from the_alchemiser.__main__ import run
        
        # Mock boolean result
        mock_main.return_value = False
        
        # Test run function
        run()
        
        # Verify calls
        mock_main.assert_called_once_with(["trade"])
        mock_exit.assert_called_once_with(1)


class TestDisplayUtils:
    """Test display utility functions."""

    def test_display_functions_import(self) -> None:
        """Test that display functions import correctly."""
        from the_alchemiser.orchestration.display_utils import (
            display_signals_summary,
            display_rebalance_plan,
            display_stale_order_info,
            display_post_execution_tracking,
            export_tracking_summary,
        )
        
        # Check that functions are callable
        assert callable(display_signals_summary)
        assert callable(display_rebalance_plan)
        assert callable(display_stale_order_info)
        assert callable(display_post_execution_tracking)
        assert callable(export_tracking_summary)

    def test_display_signals_summary_empty_input(self) -> None:
        """Test display_signals_summary handles empty input gracefully."""
        from the_alchemiser.orchestration.display_utils import display_signals_summary
        
        # Should not raise exception with empty input
        display_signals_summary({})
        display_signals_summary({"strategy_signals": {}})