#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for main.py entry point.

Tests cover:
- Argument parsing for trade and pnl commands
- Main function execution with mocked dependencies
- Error handling and notification flows
- Exit code generation
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock, patch

from the_alchemiser.main import (
    _execute_pnl_analysis,
    _handle_error_with_notification,
    _parse_arguments,
    main,
)
from the_alchemiser.shared.errors.exceptions import ConfigurationError


class TestArgumentParsing:
    """Test argument parsing functionality."""

    def test_parse_empty_arguments(self) -> None:
        """Test parsing with no arguments defaults to trade mode."""
        args = _parse_arguments(None)
        assert args.mode == "trade"
        assert args.show_tracking is False
        assert args.export_tracking_json is None
        assert args.pnl_type is None
        assert args.pnl_periods == 1
        assert args.pnl_detailed is False
        assert args.pnl_period is None

    def test_parse_trade_command(self) -> None:
        """Test parsing trade command."""
        args = _parse_arguments(["trade"])
        assert args.mode == "trade"
        assert args.show_tracking is False

    def test_parse_trade_with_tracking(self) -> None:
        """Test parsing trade command with tracking options."""
        args = _parse_arguments(["trade", "--show-tracking"])
        assert args.mode == "trade"
        assert args.show_tracking is True

    def test_parse_trade_with_export_json(self) -> None:
        """Test parsing trade command with export JSON option."""
        args = _parse_arguments(["trade", "--export-tracking-json", "/tmp/output.json"])
        assert args.mode == "trade"
        assert args.export_tracking_json == "/tmp/output.json"

    def test_parse_pnl_weekly(self) -> None:
        """Test parsing pnl weekly command."""
        args = _parse_arguments(["pnl", "--weekly"])
        assert args.mode == "pnl"
        assert args.pnl_type == "weekly"
        assert args.pnl_periods == 1

    def test_parse_pnl_monthly(self) -> None:
        """Test parsing pnl monthly command."""
        args = _parse_arguments(["pnl", "--monthly"])
        assert args.mode == "pnl"
        assert args.pnl_type == "monthly"

    def test_parse_pnl_with_periods(self) -> None:
        """Test parsing pnl command with periods option."""
        args = _parse_arguments(["pnl", "--weekly", "--periods", "3"])
        assert args.mode == "pnl"
        assert args.pnl_type == "weekly"
        assert args.pnl_periods == 3

    def test_parse_pnl_with_detailed(self) -> None:
        """Test parsing pnl command with detailed flag."""
        args = _parse_arguments(["pnl", "--monthly", "--detailed"])
        assert args.mode == "pnl"
        assert args.pnl_type == "monthly"
        assert args.pnl_detailed is True

    def test_parse_pnl_with_period(self) -> None:
        """Test parsing pnl command with specific period."""
        args = _parse_arguments(["pnl", "--period", "3M"])
        assert args.mode == "pnl"
        assert args.pnl_period == "3M"

    def test_parse_pnl_invalid_periods_value(self) -> None:
        """Test parsing pnl command with invalid periods value."""
        args = _parse_arguments(["pnl", "--periods", "invalid"])
        assert args.pnl_periods == 1  # Should default to 1

    def test_parse_unknown_mode(self) -> None:
        """Test parsing unknown mode."""
        args = _parse_arguments(["unknown"])
        assert args.mode == "unknown"


class TestMainFunction:
    """Test main function execution."""

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_trade_success(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with successful trade execution."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_system = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_system.execute_trading.return_value = mock_result
        mock_trading_system_cls.return_value = mock_system

        result = main(["trade"])

        assert hasattr(result, "success")
        assert result.success is True
        mock_system.execute_trading.assert_called_once_with(
            show_tracking=False,
            export_tracking_json=None,
        )

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_trade_with_tracking(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with trade execution and tracking enabled."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_system = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_system.execute_trading.return_value = mock_result
        mock_trading_system_cls.return_value = mock_system

        result = main(["trade", "--show-tracking"])

        mock_system.execute_trading.assert_called_once_with(
            show_tracking=True,
            export_tracking_json=None,
        )

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_trade_with_export_json(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with trade execution and JSON export."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_system = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_system.execute_trading.return_value = mock_result
        mock_trading_system_cls.return_value = mock_system

        result = main(["trade", "--export-tracking-json", "/tmp/test.json"])

        mock_system.execute_trading.assert_called_once_with(
            show_tracking=False,
            export_tracking_json="/tmp/test.json",
        )

    @patch("the_alchemiser.main._execute_pnl_analysis")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_pnl_success(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_execute_pnl: Mock,
    ) -> None:
        """Test main function with successful pnl execution."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_execute_pnl.return_value = True

        result = main(["pnl", "--weekly"])

        assert result is True
        mock_execute_pnl.assert_called_once()

    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_unknown_mode(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
    ) -> None:
        """Test main function with unknown mode."""
        mock_generate_request_id.return_value = "test-request-id"

        result = main(["unknown"])

        assert result is False

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main._handle_error_with_notification")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_configuration_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_handle_error: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with configuration error."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_trading_system_cls.side_effect = ConfigurationError("Test config error")

        result = main(["trade"])

        assert result is False
        mock_handle_error.assert_called_once()
        call_args = mock_handle_error.call_args
        assert isinstance(call_args[1]["error"], ConfigurationError)
        assert call_args[1]["context"] == "application initialization and execution"

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main._handle_error_with_notification")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_value_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_handle_error: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with value error."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_trading_system_cls.side_effect = ValueError("Test value error")

        result = main(["trade"])

        assert result is False
        mock_handle_error.assert_called_once()

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main._handle_error_with_notification")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_import_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_handle_error: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with import error."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_trading_system_cls.side_effect = ImportError("Test import error")

        result = main(["trade"])

        assert result is False
        mock_handle_error.assert_called_once()

    @patch("the_alchemiser.main.TradingSystem")
    @patch("the_alchemiser.main._handle_error_with_notification")
    @patch("the_alchemiser.main.configure_application_logging")
    @patch("the_alchemiser.main.generate_request_id")
    @patch("the_alchemiser.main.set_request_id")
    def test_main_unexpected_exception(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_configure_logging: Mock,
        mock_handle_error: Mock,
        mock_trading_system_cls: Mock,
    ) -> None:
        """Test main function with unexpected exception."""
        mock_generate_request_id.return_value = "test-request-id"
        mock_trading_system_cls.side_effect = RuntimeError("Unexpected error")

        result = main(["trade"])

        assert result is False
        mock_handle_error.assert_called_once()
        call_args = mock_handle_error.call_args
        assert call_args[1]["context"] == "application execution - unhandled exception"


class TestPnLAnalysis:
    """Test P&L analysis execution."""

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_weekly(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis with weekly type."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_weekly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--weekly"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.get_weekly_pnl.assert_called_once_with(1)
        mock_service.format_pnl_report.assert_called_once_with(mock_pnl_data, detailed=False)

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_monthly(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis with monthly type."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_monthly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--monthly"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.get_monthly_pnl.assert_called_once_with(1)

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_with_period(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis with specific period."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_period_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--period", "3M"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.get_period_pnl.assert_called_once_with("3M")

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_with_periods_count(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis with periods count."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_weekly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--weekly", "--periods", "3"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.get_weekly_pnl.assert_called_once_with(3)

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_detailed(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis with detailed flag."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_weekly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test detailed report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--weekly", "--detailed"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.format_pnl_report.assert_called_once_with(mock_pnl_data, detailed=True)

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_default_to_weekly(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis defaults to weekly when no type specified."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = Decimal("10000.00")
        mock_service.get_weekly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "Test report"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl"])
        result = _execute_pnl_analysis(args)

        assert result is True
        mock_service.get_weekly_pnl.assert_called_once_with(1)

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    def test_execute_pnl_no_data(self, mock_pnl_service_cls: Mock) -> None:
        """Test P&L analysis returns False when no data available."""
        mock_service = Mock()
        mock_pnl_data = Mock()
        mock_pnl_data.start_value = None
        mock_service.get_weekly_pnl.return_value = mock_pnl_data
        mock_service.format_pnl_report.return_value = "No data"
        mock_pnl_service_cls.return_value = mock_service

        args = _parse_arguments(["pnl", "--weekly"])
        result = _execute_pnl_analysis(args)

        assert result is False

    @patch("the_alchemiser.shared.services.pnl_service.PnLService")
    @patch("the_alchemiser.main.get_logger")
    def test_execute_pnl_exception(
        self, mock_get_logger: Mock, mock_pnl_service_cls: Mock
    ) -> None:
        """Test P&L analysis handles exceptions."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_pnl_service_cls.side_effect = Exception("Test error")

        args = _parse_arguments(["pnl", "--weekly"])
        result = _execute_pnl_analysis(args)

        assert result is False
        mock_logger.error.assert_called_once()


class TestErrorHandling:
    """Test error handling and notification."""

    @patch("the_alchemiser.main.TradingSystemErrorHandler")
    @patch("the_alchemiser.main._send_error_notification")
    def test_handle_error_with_notification(
        self, mock_send_notification: Mock, mock_error_handler_cls: Mock
    ) -> None:
        """Test error handling with notification."""
        mock_handler = Mock()
        mock_error_handler_cls.return_value = mock_handler

        error = ValueError("Test error")
        context = "test context"
        additional_data: dict[str, str | list[str] | None] = {"key": "value"}

        _handle_error_with_notification(error, context, additional_data)

        mock_handler.handle_error.assert_called_once_with(
            error=error,
            context=context,
            component="main",
            additional_data=additional_data,
        )
        mock_send_notification.assert_called_once()

    @patch("the_alchemiser.main.TradingSystemErrorHandler")
    @patch("the_alchemiser.main._send_error_notification")
    def test_handle_error_without_additional_data(
        self, mock_send_notification: Mock, mock_error_handler_cls: Mock
    ) -> None:
        """Test error handling without additional data."""
        mock_handler = Mock()
        mock_error_handler_cls.return_value = mock_handler

        error = ValueError("Test error")
        context = "test context"

        _handle_error_with_notification(error, context)

        mock_handler.handle_error.assert_called_once_with(
            error=error,
            context=context,
            component="main",
            additional_data={},
        )
