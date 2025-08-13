"""
Comprehensive unit tests for interface layer.

Tests CLI commands, email notifications, dashboard utilities, and user interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
import io
import sys
from typer.testing import CliRunner

from the_alchemiser.interface.cli.main import app as cli_app
from the_alchemiser.interface.cli.signal_analyzer import SignalAnalyzer
from the_alchemiser.interface.cli.trading_executor import TradingExecutor
from the_alchemiser.interface.cli.dashboard_utils import DashboardUtils
from the_alchemiser.interface.cli.signal_display_utils import SignalDisplayUtils
from the_alchemiser.interface.email.email_service import EmailService
from the_alchemiser.interface.email.notification_manager import NotificationManager
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
from the_alchemiser.services.exceptions import TradingClientError, ConfigurationError


class TestCLICommands:
    """Test CLI command functionality."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_trading_manager(self, mocker):
        """Create mocked trading service manager for CLI testing."""
        mock_manager = Mock(spec=TradingServiceManager)
        mock_manager.paper_trading = True

        # Mock typical responses
        mock_manager.get_account_info.return_value = {
            "portfolio_value": "100000.00",
            "cash": "25000.00",
            "buying_power": "50000.00",
            "equity": "100000.00",
        }

        mock_manager.get_all_positions.return_value = [
            {
                "symbol": "AAPL",
                "qty": "100",
                "market_value": "15000.00",
                "unrealized_pl": "500.00",
                "unrealized_plpc": "0.0333",
                "side": "long",
            },
            {
                "symbol": "TSLA",
                "qty": "50",
                "market_value": "12500.00",
                "unrealized_pl": "-250.00",
                "unrealized_plpc": "-0.0196",
                "side": "long",
            },
        ]

        return mock_manager

    def test_signal_command_execution(self, cli_runner, mock_trading_manager):
        """Test signal analysis command."""
        with patch("the_alchemiser.interface.cli.main.TradingServiceManager") as mock_tsm:
            mock_tsm.return_value = mock_trading_manager

            with patch("the_alchemiser.interface.cli.main.MultiStrategyManager") as mock_msm:
                mock_strategy = Mock()
                mock_strategy.generate_combined_signals.return_value = {
                    "AAPL": {
                        "signal": "BUY",
                        "allocation": 0.30,
                        "confidence": 0.85,
                        "reasoning": "Strong technical indicators",
                    },
                    "TSLA": {
                        "signal": "SELL",
                        "allocation": 0.10,
                        "confidence": 0.70,
                        "reasoning": "High volatility",
                    },
                }
                mock_msm.return_value = mock_strategy

                # Execute signal command
                result = cli_runner.invoke(cli_app, ["signal"])

                # Verify command execution
                assert result.exit_code == 0
                assert "Signal Analysis" in result.stdout
                assert "AAPL" in result.stdout
                assert "BUY" in result.stdout

    def test_status_command_execution(self, cli_runner, mock_trading_manager):
        """Test status command execution."""
        with patch("the_alchemiser.interface.cli.main.TradingServiceManager") as mock_tsm:
            mock_tsm.return_value = mock_trading_manager

            # Execute status command
            result = cli_runner.invoke(cli_app, ["status"])

            # Verify command execution
            assert result.exit_code == 0
            assert "Account Status" in result.stdout
            assert "Portfolio Value" in result.stdout
            assert "$100,000.00" in result.stdout

    def test_trade_command_paper_mode(self, cli_runner, mock_trading_manager):
        """Test trade command in paper mode."""
        mock_trading_manager.place_market_order.return_value = {
            "id": "test_order_123",
            "status": "filled",
            "symbol": "AAPL",
            "qty": "10",
            "side": "buy",
        }

        with (
            patch("the_alchemiser.interface.cli.main.TradingServiceManager") as mock_tsm,
            patch("the_alchemiser.interface.cli.main.MultiStrategyManager") as mock_msm,
        ):

            mock_tsm.return_value = mock_trading_manager
            mock_strategy = Mock()
            mock_strategy.generate_combined_signals.return_value = {
                "AAPL": {"signal": "BUY", "allocation": 0.25, "confidence": 0.8}
            }
            mock_msm.return_value = mock_strategy

            # Execute trade command
            result = cli_runner.invoke(cli_app, ["trade"])

            # Verify paper trading execution
            assert result.exit_code == 0
            assert "PAPER TRADING MODE" in result.stdout

    def test_trade_command_live_mode_confirmation(self, cli_runner, mock_trading_manager):
        """Test trade command requires confirmation for live mode."""
        mock_trading_manager.paper_trading = False

        with patch("the_alchemiser.interface.cli.main.TradingServiceManager") as mock_tsm:
            mock_tsm.return_value = mock_trading_manager

            # Execute trade command with live flag, but no confirmation
            result = cli_runner.invoke(cli_app, ["trade", "--live"], input="n\n")

            # Should abort due to lack of confirmation
            assert result.exit_code != 0 or "Aborted" in result.stdout

    def test_validate_indicators_command(self, cli_runner):
        """Test validate-indicators command."""
        with patch("the_alchemiser.interface.cli.main.MultiStrategyManager") as mock_msm:
            mock_strategy = Mock()
            mock_strategy.validate_all_indicators.return_value = {
                "nuclear_strategy": {"valid": True, "errors": []},
                "tecl_strategy": {"valid": True, "errors": []},
                "klm_strategy": {"valid": False, "errors": ["Missing data"]},
            }
            mock_msm.return_value = mock_strategy

            # Execute validate-indicators command
            result = cli_runner.invoke(cli_app, ["validate-indicators"])

            # Verify validation output
            assert result.exit_code == 0
            assert "Indicator Validation" in result.stdout

    def test_cli_error_handling(self, cli_runner):
        """Test CLI error handling."""
        with patch("the_alchemiser.interface.cli.main.TradingServiceManager") as mock_tsm:
            mock_tsm.side_effect = ConfigurationError("Missing API keys")

            # Execute command that should fail
            result = cli_runner.invoke(cli_app, ["status"])

            # Should handle error gracefully
            assert result.exit_code != 0
            assert "Error" in result.stdout or "Configuration" in result.stdout


class TestSignalAnalyzer:
    """Test signal analysis functionality."""

    @pytest.fixture
    def signal_analyzer(self, mocker):
        """Create SignalAnalyzer with mocked dependencies."""
        mock_strategy_manager = Mock()
        analyzer = SignalAnalyzer(mock_strategy_manager)
        return analyzer

    def test_signal_analysis_execution(self, signal_analyzer):
        """Test signal analysis execution."""
        # Mock strategy signals
        mock_signals = {
            "AAPL": {
                "signal": "BUY",
                "allocation": 0.30,
                "confidence": 0.85,
                "reasoning": "Strong momentum indicators",
                "strategy_weights": {"nuclear": 0.4, "tecl": 0.3, "klm": 0.3},
            },
            "TSLA": {
                "signal": "REDUCE",
                "allocation": 0.10,
                "confidence": 0.70,
                "reasoning": "High volatility concerns",
                "strategy_weights": {"nuclear": 0.2, "tecl": 0.5, "klm": 0.3},
            },
        }

        signal_analyzer.strategy_manager.generate_combined_signals.return_value = mock_signals

        # Execute analysis
        analysis_result = signal_analyzer.analyze_signals()

        # Verify analysis results
        assert analysis_result["success"] is True
        assert "signals" in analysis_result
        assert len(analysis_result["signals"]) == 2
        assert "summary" in analysis_result

    def test_signal_validation(self, signal_analyzer):
        """Test signal validation logic."""
        # Test valid signals
        valid_signals = {"AAPL": {"signal": "BUY", "allocation": 0.25, "confidence": 0.8}}

        is_valid = signal_analyzer.validate_signals(valid_signals)
        assert is_valid is True

        # Test invalid signals
        invalid_signals = {
            "AAPL": {"signal": "INVALID", "allocation": 1.5, "confidence": 2.0}  # Invalid values
        }

        is_valid = signal_analyzer.validate_signals(invalid_signals)
        assert is_valid is False

    def test_signal_summary_generation(self, signal_analyzer):
        """Test signal summary generation."""
        signals = {
            "AAPL": {"signal": "BUY", "allocation": 0.30, "confidence": 0.85},
            "TSLA": {"signal": "SELL", "allocation": 0.15, "confidence": 0.70},
            "SPY": {"signal": "HOLD", "allocation": 0.35, "confidence": 0.90},
            "CASH": {"signal": "HOLD", "allocation": 0.20, "confidence": 1.0},
        }

        summary = signal_analyzer.generate_signal_summary(signals)

        # Verify summary content
        assert "total_positions" in summary
        assert "buy_signals" in summary
        assert "sell_signals" in summary
        assert "hold_signals" in summary
        assert summary["total_positions"] == 4
        assert summary["buy_signals"] == 1
        assert summary["sell_signals"] == 1


class TestTradingExecutor:
    """Test trading execution functionality."""

    @pytest.fixture
    def trading_executor(self, mocker):
        """Create TradingExecutor with mocked dependencies."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        mock_trading_manager.paper_trading = True

        executor = TradingExecutor(mock_trading_manager)
        return executor

    def test_trade_execution_paper_mode(self, trading_executor):
        """Test trade execution in paper mode."""
        # Mock successful order
        trading_executor.trading_manager.place_market_order.return_value = {
            "id": "paper_order_123",
            "status": "filled",
            "symbol": "AAPL",
            "qty": "10",
            "side": "buy",
        }

        # Execute trade
        trade_request = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": Decimal("10"),
            "order_type": "market",
        }

        result = trading_executor.execute_trade(trade_request)

        # Verify execution
        assert result["success"] is True
        assert result["order_id"] == "paper_order_123"
        assert result["paper_trading"] is True

    def test_trade_execution_validation(self, trading_executor):
        """Test trade execution validation."""
        # Test invalid trade request
        invalid_trade = {
            "symbol": "",  # Invalid empty symbol
            "side": "invalid_side",
            "quantity": Decimal("-10"),  # Negative quantity
            "order_type": "invalid_type",
        }

        result = trading_executor.execute_trade(invalid_trade)

        # Should fail validation
        assert result["success"] is False
        assert "error" in result

    def test_trade_execution_error_handling(self, trading_executor):
        """Test trade execution error handling."""
        # Mock API error
        trading_executor.trading_manager.place_market_order.side_effect = TradingClientError(
            "Order rejected by broker"
        )

        trade_request = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": Decimal("10"),
            "order_type": "market",
        }

        result = trading_executor.execute_trade(trade_request)

        # Should handle error gracefully
        assert result["success"] is False
        assert "error" in result

    def test_batch_trade_execution(self, trading_executor):
        """Test batch trade execution."""
        # Mock successful orders
        trading_executor.trading_manager.place_market_order.return_value = {
            "id": "batch_order_123",
            "status": "filled",
        }

        trade_requests = [
            {"symbol": "AAPL", "side": "buy", "quantity": Decimal("10")},
            {"symbol": "TSLA", "side": "sell", "quantity": Decimal("5")},
            {"symbol": "SPY", "side": "buy", "quantity": Decimal("20")},
        ]

        results = trading_executor.execute_batch_trades(trade_requests)

        # Verify batch execution
        assert len(results) == 3
        assert all(result["success"] for result in results)

    def test_trade_monitoring(self, trading_executor):
        """Test trade monitoring functionality."""
        # Mock order status tracking
        trading_executor.trading_manager.get_order_status.return_value = {
            "id": "monitor_order_123",
            "status": "filled",
            "filled_qty": "10",
            "filled_avg_price": "150.25",
        }

        order_id = "monitor_order_123"
        status = trading_executor.monitor_trade_execution(order_id)

        # Verify monitoring
        assert status["status"] == "filled"
        assert status["filled_qty"] == "10"


class TestDashboardUtils:
    """Test dashboard utility functions."""

    @pytest.fixture
    def dashboard_utils(self):
        """Create DashboardUtils instance."""
        return DashboardUtils()

    def test_portfolio_summary_formatting(self, dashboard_utils):
        """Test portfolio summary formatting."""
        portfolio_data = {
            "portfolio_value": "125000.50",
            "cash": "25000.00",
            "equity": "125000.50",
            "buying_power": "62500.25",
            "day_change": "2500.50",
            "day_change_percent": "0.0204",
        }

        formatted_summary = dashboard_utils.format_portfolio_summary(portfolio_data)

        # Verify formatting
        assert "$125,000.50" in formatted_summary
        assert "$25,000.00" in formatted_summary
        assert "+$2,500.50" in formatted_summary
        assert "+2.04%" in formatted_summary

    def test_position_table_formatting(self, dashboard_utils):
        """Test position table formatting."""
        positions = [
            {
                "symbol": "AAPL",
                "qty": "100",
                "market_value": "15000.00",
                "unrealized_pl": "500.00",
                "unrealized_plpc": "0.0345",
                "avg_entry_price": "145.00",
            },
            {
                "symbol": "TSLA",
                "qty": "50",
                "market_value": "12500.00",
                "unrealized_pl": "-250.00",
                "unrealized_plpc": "-0.0196",
                "avg_entry_price": "255.00",
            },
        ]

        formatted_table = dashboard_utils.format_positions_table(positions)

        # Verify table formatting
        assert "AAPL" in formatted_table
        assert "TSLA" in formatted_table
        assert "$15,000.00" in formatted_table
        assert "+$500.00" in formatted_table
        assert "-$250.00" in formatted_table

    def test_performance_metrics_formatting(self, dashboard_utils):
        """Test performance metrics formatting."""
        metrics = {
            "total_return": "12500.00",
            "total_return_percent": "0.1429",
            "daily_return": "250.00",
            "daily_return_percent": "0.0020",
            "sharpe_ratio": "1.25",
            "max_drawdown": "-0.0850",
        }

        formatted_metrics = dashboard_utils.format_performance_metrics(metrics)

        # Verify metrics formatting
        assert "+$12,500.00" in formatted_metrics
        assert "+14.29%" in formatted_metrics
        assert "1.25" in formatted_metrics
        assert "-8.50%" in formatted_metrics

    def test_color_coding_for_values(self, dashboard_utils):
        """Test color coding for positive/negative values."""
        # Test positive value
        positive_color = dashboard_utils.get_color_for_value(Decimal("500.00"))
        assert positive_color == "green"

        # Test negative value
        negative_color = dashboard_utils.get_color_for_value(Decimal("-250.00"))
        assert negative_color == "red"

        # Test zero value
        neutral_color = dashboard_utils.get_color_for_value(Decimal("0.00"))
        assert neutral_color == "white"

    def test_alert_formatting(self, dashboard_utils):
        """Test alert message formatting."""
        alert = {
            "type": "warning",
            "message": "Portfolio allocation exceeds risk limits",
            "timestamp": datetime.now(),
            "severity": "medium",
        }

        formatted_alert = dashboard_utils.format_alert(alert)

        # Verify alert formatting
        assert "WARNING" in formatted_alert
        assert "Portfolio allocation" in formatted_alert
        assert "medium" in formatted_alert.lower()


class TestSignalDisplayUtils:
    """Test signal display utility functions."""

    @pytest.fixture
    def signal_display(self):
        """Create SignalDisplayUtils instance."""
        return SignalDisplayUtils()

    def test_signal_table_formatting(self, signal_display):
        """Test signal table formatting."""
        signals = {
            "AAPL": {
                "signal": "BUY",
                "allocation": 0.30,
                "confidence": 0.85,
                "reasoning": "Strong technical indicators",
            },
            "TSLA": {
                "signal": "SELL",
                "allocation": 0.10,
                "confidence": 0.70,
                "reasoning": "High volatility concerns",
            },
            "SPY": {
                "signal": "HOLD",
                "allocation": 0.35,
                "confidence": 0.90,
                "reasoning": "Market neutral position",
            },
        }

        formatted_table = signal_display.format_signals_table(signals)

        # Verify signal table formatting
        assert "AAPL" in formatted_table
        assert "BUY" in formatted_table
        assert "30.0%" in formatted_table
        assert "85%" in formatted_table

    def test_confidence_level_formatting(self, signal_display):
        """Test confidence level formatting."""
        # High confidence
        high_conf = signal_display.format_confidence(0.90)
        assert "90%" in high_conf
        assert "High" in high_conf or "green" in high_conf.lower()

        # Medium confidence
        medium_conf = signal_display.format_confidence(0.70)
        assert "70%" in medium_conf
        assert "Medium" in medium_conf or "yellow" in medium_conf.lower()

        # Low confidence
        low_conf = signal_display.format_confidence(0.40)
        assert "40%" in low_conf
        assert "Low" in low_conf or "red" in low_conf.lower()

    def test_strategy_breakdown_display(self, signal_display):
        """Test strategy breakdown display."""
        strategy_weights = {"nuclear": 0.40, "tecl": 0.35, "klm": 0.25}

        breakdown = signal_display.format_strategy_breakdown(strategy_weights)

        # Verify strategy breakdown
        assert "Nuclear" in breakdown
        assert "TECL" in breakdown
        assert "KLM" in breakdown
        assert "40%" in breakdown
        assert "35%" in breakdown
        assert "25%" in breakdown

    def test_signal_summary_display(self, signal_display):
        """Test signal summary display."""
        summary = {
            "total_signals": 5,
            "buy_signals": 2,
            "sell_signals": 1,
            "hold_signals": 2,
            "average_confidence": 0.75,
            "total_allocation": 0.85,
        }

        formatted_summary = signal_display.format_signal_summary(summary)

        # Verify summary formatting
        assert "5 total signals" in formatted_summary
        assert "2 BUY" in formatted_summary
        assert "1 SELL" in formatted_summary
        assert "75%" in formatted_summary  # Average confidence
        assert "85%" in formatted_summary  # Total allocation


class TestEmailService:
    """Test email notification service."""

    @pytest.fixture
    def email_service(self, mocker):
        """Create EmailService with mocked SMTP."""
        service = EmailService(
            smtp_server="smtp.test.com",
            smtp_port=587,
            username="test@example.com",
            password="test_password",
        )

        # Mock SMTP client
        service.smtp_client = Mock()
        return service

    def test_email_sending(self, email_service):
        """Test basic email sending."""
        result = email_service.send_email(
            to_address="recipient@example.com",
            subject="Test Trading Alert",
            body="Portfolio value has increased by 5%",
            is_html=False,
        )

        assert result is True
        email_service.smtp_client.send_message.assert_called_once()

    def test_html_email_sending(self, email_service):
        """Test HTML email sending."""
        html_content = """
        <html>
            <body>
                <h2>Trading Alert</h2>
                <p>Portfolio Value: <strong>$125,000</strong></p>
                <p>Daily P&L: <span style="color: green;">+$2,500</span></p>
            </body>
        </html>
        """

        result = email_service.send_html_email(
            to_address="trader@example.com", subject="Daily Trading Report", html_body=html_content
        )

        assert result is True

    def test_trading_alert_templates(self, email_service):
        """Test trading alert email templates."""
        alert_data = {
            "type": "order_executed",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": Decimal("150.25"),
            "order_id": "test_order_123",
            "timestamp": datetime.now(),
        }

        result = email_service.send_trading_alert(
            to_address="trader@example.com", alert_data=alert_data
        )

        assert result is True

    def test_error_notification_email(self, email_service):
        """Test error notification email."""
        error_data = {
            "component": "TradingEngine",
            "error_type": "OrderValidationError",
            "error_message": "Insufficient buying power",
            "timestamp": datetime.now(),
            "context": {
                "symbol": "AAPL",
                "attempted_quantity": 1000,
                "available_buying_power": "$25,000",
            },
        }

        result = email_service.send_error_notification(
            to_address="admin@example.com", error_data=error_data
        )

        assert result is True

    def test_email_failure_handling(self, email_service):
        """Test email sending failure handling."""
        # Mock SMTP failure
        email_service.smtp_client.send_message.side_effect = Exception("SMTP connection failed")

        result = email_service.send_email(
            to_address="test@example.com", subject="Test", body="Test message"
        )

        # Should handle failure gracefully
        assert result is False


class TestNotificationManager:
    """Test notification management system."""

    @pytest.fixture
    def notification_manager(self, mocker):
        """Create NotificationManager with mocked dependencies."""
        mock_email_service = Mock(spec=EmailService)
        manager = NotificationManager(email_service=mock_email_service)
        return manager

    def test_trading_notification_sending(self, notification_manager):
        """Test trading notification sending."""
        notification_data = {
            "type": "position_opened",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": Decimal("150.00"),
            "portfolio_impact": "+2.5%",
        }

        result = notification_manager.send_trading_notification(
            notification_type="position_opened", data=notification_data
        )

        assert result is True
        notification_manager.email_service.send_trading_alert.assert_called_once()

    def test_error_notification_sending(self, notification_manager):
        """Test error notification sending."""
        error_data = {
            "component": "PortfolioRebalancer",
            "error_message": "Rebalancing failed due to market closure",
            "severity": "warning",
            "timestamp": datetime.now(),
        }

        result = notification_manager.send_error_notification(error_data)

        assert result is True
        notification_manager.email_service.send_error_notification.assert_called_once()

    def test_notification_throttling(self, notification_manager):
        """Test notification throttling to prevent spam."""
        # Send multiple similar notifications quickly
        for i in range(5):
            notification_manager.send_trading_notification(
                notification_type="price_alert", data={"symbol": "AAPL", "price": 150 + i}
            )

        # Should throttle repeated notifications
        # (Implementation would limit to 1 per minute for same type)
        call_count = notification_manager.email_service.send_trading_alert.call_count
        assert call_count <= 3  # Should throttle after first few

    def test_notification_priority_handling(self, notification_manager):
        """Test notification priority handling."""
        # High priority notification (error)
        high_priority = {
            "type": "critical_error",
            "priority": "high",
            "message": "Trading system disconnected",
            "timestamp": datetime.now(),
        }

        # Low priority notification (info)
        low_priority = {
            "type": "daily_summary",
            "priority": "low",
            "message": "Daily trading summary available",
            "timestamp": datetime.now(),
        }

        # High priority should be sent immediately
        result1 = notification_manager.send_notification(high_priority)
        assert result1 is True

        # Low priority might be batched or delayed
        result2 = notification_manager.send_notification(low_priority)
        assert result2 is True


if __name__ == "__main__":
    pytest.main([__file__])
