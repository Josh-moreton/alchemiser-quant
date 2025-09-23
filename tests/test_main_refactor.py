#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Test for main.py entry point functionality.

Tests that the refactored main.py correctly handles argument parsing
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

    def test_argument_parser_creation(self) -> None:
        """Test that argument parser is created correctly."""
        from the_alchemiser.orchestration.cli.argument_parser import create_argument_parser
        
        parser = create_argument_parser()
        assert parser is not None
        
        # Test valid trade command
        args = parser.parse_args(["trade"])
        assert args.mode == "trade"
        
        # Test with optional flags
        args = parser.parse_args(["trade", "--show-tracking"])
        assert args.show_tracking is True
        
        args = parser.parse_args(["trade", "--export-tracking-json", "/tmp/test.json"])
        assert args.export_tracking_json == "/tmp/test.json"

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
        """Test the main function with successful trading execution."""
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_system_instance = Mock()
        mock_trading_system.return_value = mock_system_instance
        
        # Mock successful result
        mock_result = Mock()
        mock_result.success = True
        mock_system_instance.execute_trading.return_value = mock_result
        
        # Call main
        result = main(["trade"])
        
        # Assertions
        mock_configure_logging.assert_called_once()
        mock_generate_request_id.assert_called_once()
        mock_set_request_id.assert_called_once_with("test-request-id")
        mock_trading_system.assert_called_once()
        mock_system_instance.execute_trading.assert_called_once_with(
            show_tracking=False,
            export_tracking_json=None
        )
        assert result == mock_result

    @patch('the_alchemiser.main.TradingSystem')
    @patch('the_alchemiser.main.configure_application_logging')
    @patch('the_alchemiser.main.generate_request_id')
    @patch('the_alchemiser.main.set_request_id')
    def test_main_trading_with_options(
        self, 
        mock_set_request_id: Mock, 
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system: Mock
    ) -> None:
        """Test the main function with trading options enabled."""
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_system_instance = Mock()
        mock_trading_system.return_value = mock_system_instance
        
        mock_result = Mock()
        mock_result.success = True
        mock_system_instance.execute_trading.return_value = mock_result
        
        # Call main with options
        result = main(["trade", "--show-tracking", "--export-tracking-json", "/tmp/test.json"])
        
        # Assertions
        mock_system_instance.execute_trading.assert_called_once_with(
            show_tracking=True,
            export_tracking_json="/tmp/test.json"
        )
        assert result == mock_result

    @patch('the_alchemiser.main.render_footer')
    @patch('the_alchemiser.main.TradingSystemErrorHandler')
    @patch('the_alchemiser.main.configure_application_logging')
    @patch('the_alchemiser.main.generate_request_id')
    @patch('the_alchemiser.main.set_request_id')
    def test_main_configuration_error_handling(
        self, 
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_error_handler_class: Mock,
        mock_render_footer: Mock
    ) -> None:
        """Test main function handles configuration errors properly."""
        from the_alchemiser.shared.types.exceptions import ConfigurationError
        
        # Setup mocks
        mock_generate_request_id.return_value = "test-request-id"
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        # Mock TradingSystem to raise ConfigurationError
        with patch('the_alchemiser.main.TradingSystem') as mock_trading_system:
            mock_trading_system.side_effect = ConfigurationError("Test config error")
            
            # Call main
            result = main(["trade"])
            
            # Assertions
            assert result is False
            mock_error_handler.handle_error.assert_called_once()
            mock_render_footer.assert_called_once_with("System error occurred!")

    def test_invalid_command_argument(self) -> None:
        """Test that invalid command arguments are rejected."""
        from the_alchemiser.orchestration.cli.argument_parser import create_argument_parser
        
        parser = create_argument_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["invalid"])


class TestTradingDisplay:
    """Test trading display utilities."""

    def test_display_functions_import(self) -> None:
        """Test that display functions import correctly."""
        from the_alchemiser.orchestration.cli.trading_display import (
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
        from the_alchemiser.orchestration.cli.trading_display import display_signals_summary
        
        # Should not raise exception with empty input
        display_signals_summary({})
        display_signals_summary({"strategy_signals": {}})

    def test_display_rebalance_plan_no_plan(self) -> None:
        """Test display_rebalance_plan handles missing plan gracefully."""
        from the_alchemiser.orchestration.cli.trading_display import display_rebalance_plan
        
        # Should not raise exception with no plan
        display_rebalance_plan({})
        display_rebalance_plan({"rebalance_plan": None})


class TestLoggingUtilities:
    """Test logging utility functions."""

    def test_logging_functions_import(self) -> None:
        """Test that new logging functions import correctly."""
        from the_alchemiser.shared.logging.logging_utils import (
            resolve_log_level,
            configure_application_logging,
            configure_quiet_logging,
            restore_logging,
        )
        
        assert callable(resolve_log_level)
        assert callable(configure_application_logging)
        assert callable(configure_quiet_logging)
        assert callable(restore_logging)

    def test_configure_quiet_logging_returns_levels(self) -> None:
        """Test that configure_quiet_logging returns original levels."""
        from the_alchemiser.shared.logging.logging_utils import configure_quiet_logging
        
        original_levels = configure_quiet_logging()
        assert isinstance(original_levels, dict)

    def test_restore_logging_with_levels(self) -> None:
        """Test that restore_logging works with level dict."""
        from the_alchemiser.shared.logging.logging_utils import (
            configure_quiet_logging,
            restore_logging,
        )
        
        original_levels = configure_quiet_logging()
        restore_logging(original_levels)  # Should not raise exception


class TestResultFactory:
    """Test result factory utilities."""

    def test_result_factory_imports(self) -> None:
        """Test that result factory functions import correctly."""
        from the_alchemiser.shared.dto.result_factory import (
            create_failure_result,
            create_success_result,
        )
        
        assert callable(create_failure_result)
        assert callable(create_success_result)

    def test_create_failure_result(self) -> None:
        """Test that create_failure_result creates valid DTO."""
        from datetime import UTC, datetime
        from the_alchemiser.shared.dto.result_factory import create_failure_result
        
        started_at = datetime.now(UTC)
        result = create_failure_result(
            error_message="Test error",
            started_at=started_at,
            correlation_id="test-corr-id",
            warnings=["Test warning"],
        )
        
        assert result.success is False
        assert result.status == "FAILURE"
        assert "Test error" in result.warnings
        assert "Test warning" in result.warnings
        assert result.correlation_id == "test-corr-id"