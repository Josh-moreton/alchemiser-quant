#!/usr/bin/env python3
"""
Integration tests for StrategyOrderTracker DTO CLI integration.

Tests the CLI integration examples with the new DTO-based methods.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from the_alchemiser.application.tracking.strategy_order_tracker import StrategyOrderTracker
from the_alchemiser.interface.cli.strategy_tracking_cli_example import (
    display_all_strategies_pnl_dto,
    display_positions_summary_dto,
    display_strategy_orders_dto,
    display_strategy_pnl_dto,
)
from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderDTO,
    StrategyPnLDTO,
    StrategyPositionDTO,
)


class TestStrategyTrackingCLIIntegration:
    """Test CLI integration with DTO-based strategy tracking."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock the global tracker function
        self.mock_tracker = Mock(spec=StrategyOrderTracker)

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_display_strategy_orders_dto(self, mock_console_class, mock_get_tracker):
        """Test displaying strategy orders using DTO interface."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Create test orders
        test_orders = [
            StrategyOrderDTO(
                order_id="test_001",
                strategy="NUCLEAR",
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                price=Decimal("150.25"),
                timestamp=datetime.now(UTC)
            ),
            StrategyOrderDTO(
                order_id="test_002",
                strategy="NUCLEAR",
                symbol="MSFT",
                side="sell",
                quantity=Decimal("50"),
                price=Decimal("300.50"),
                timestamp=datetime.now(UTC)
            )
        ]

        self.mock_tracker.get_orders_for_strategy.return_value = test_orders

        # Call the function
        display_strategy_orders_dto("NUCLEAR", paper_trading=True)

        # Verify calls
        mock_get_tracker.assert_called_once_with(paper_trading=True)
        self.mock_tracker.get_orders_for_strategy.assert_called_once_with("NUCLEAR")
        mock_console.print.assert_called()

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_display_positions_summary_dto(self, mock_console_class, mock_get_tracker):
        """Test displaying positions summary using DTO interface."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Create test positions
        test_positions = [
            StrategyPositionDTO(
                strategy="NUCLEAR",
                symbol="AAPL",
                quantity=Decimal("100"),
                average_cost=Decimal("150.25"),
                total_cost=Decimal("15025.00"),
                last_updated=datetime.now(UTC)
            ),
            StrategyPositionDTO(
                strategy="TECL",
                symbol="MSFT",
                quantity=Decimal("50"),
                average_cost=Decimal("300.50"),
                total_cost=Decimal("15025.00"),
                last_updated=datetime.now(UTC)
            )
        ]

        self.mock_tracker.get_positions_summary.return_value = test_positions

        # Call the function
        display_positions_summary_dto(paper_trading=True)

        # Verify calls
        mock_get_tracker.assert_called_once_with(paper_trading=True)
        self.mock_tracker.get_positions_summary.assert_called_once()
        mock_console.print.assert_called()

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_display_strategy_pnl_dto(self, mock_console_class, mock_get_tracker):
        """Test displaying strategy P&L using DTO interface."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Create test P&L
        test_pnl = StrategyPnLDTO(
            strategy="NUCLEAR",
            realized_pnl=Decimal("250.00"),
            unrealized_pnl=Decimal("150.00"),
            total_pnl=Decimal("400.00"),
            positions={"AAPL": Decimal("100"), "MSFT": Decimal("50")},
            allocation_value=Decimal("30000.00")
        )

        self.mock_tracker.get_pnl_summary.return_value = test_pnl

        # Call the function
        current_prices = {"AAPL": 155.0, "MSFT": 305.0}
        display_strategy_pnl_dto("NUCLEAR", current_prices, paper_trading=True)

        # Verify calls
        mock_get_tracker.assert_called_once_with(paper_trading=True)
        self.mock_tracker.get_pnl_summary.assert_called_once_with("NUCLEAR", current_prices)
        mock_console.print.assert_called()

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_display_all_strategies_pnl_dto(self, mock_console_class, mock_get_tracker):
        """Test displaying P&L for all strategies using DTO interface."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Create test P&L for different strategies
        def mock_get_pnl_summary(strategy_name, current_prices=None):
            pnl_data = {
                "NUCLEAR": {
                    "realized_pnl": Decimal("250.00"),
                    "unrealized_pnl": Decimal("150.00"),
                    "allocation_value": Decimal("30000.00"),
                    "positions": {"AAPL": Decimal("100")}
                },
                "TECL": {
                    "realized_pnl": Decimal("100.00"),
                    "unrealized_pnl": Decimal("-50.00"),
                    "allocation_value": Decimal("20000.00"),
                    "positions": {"MSFT": Decimal("50")}
                },
                "KLM": {
                    "realized_pnl": Decimal("0.00"),
                    "unrealized_pnl": Decimal("0.00"),
                    "allocation_value": Decimal("0.00"),
                    "positions": {}
                }
            }

            data = pnl_data.get(strategy_name, pnl_data["KLM"])
            return StrategyPnLDTO(
                strategy=strategy_name,
                realized_pnl=data["realized_pnl"],
                unrealized_pnl=data["unrealized_pnl"],
                total_pnl=data["realized_pnl"] + data["unrealized_pnl"],
                positions=data["positions"],
                allocation_value=data["allocation_value"]
            )

        self.mock_tracker.get_pnl_summary.side_effect = mock_get_pnl_summary

        # Call the function
        current_prices = {"AAPL": 155.0, "MSFT": 305.0}
        display_all_strategies_pnl_dto(current_prices, paper_trading=True)

        # Verify calls
        mock_get_tracker.assert_called_once_with(paper_trading=True)
        # Should be called once for each strategy
        assert self.mock_tracker.get_pnl_summary.call_count == 3
        mock_console.print.assert_called()

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_empty_orders_display(self, mock_console_class, mock_get_tracker):
        """Test displaying empty orders list."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Return empty list
        self.mock_tracker.get_orders_for_strategy.return_value = []

        # Call the function
        display_strategy_orders_dto("NUCLEAR", paper_trading=True)

        # Verify warning message
        mock_console.print.assert_called_with("[yellow]No orders found for strategy NUCLEAR[/yellow]")

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_empty_positions_display(self, mock_console_class, mock_get_tracker):
        """Test displaying empty positions list."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.return_value = self.mock_tracker

        # Return empty list
        self.mock_tracker.get_positions_summary.return_value = []

        # Call the function
        display_positions_summary_dto(paper_trading=True)

        # Verify warning message
        mock_console.print.assert_called_with("[yellow]No active positions found[/yellow]")

    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.get_strategy_tracker')
    @patch('the_alchemiser.interface.cli.strategy_tracking_cli_example.Console')
    def test_error_handling_in_cli(self, mock_console_class, mock_get_tracker):
        """Test error handling in CLI functions."""
        # Setup mocks
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_get_tracker.side_effect = Exception("Test error")

        # Call the function
        display_strategy_orders_dto("NUCLEAR", paper_trading=True)

        # Verify error message
        mock_console.print.assert_called_with("[red]Error displaying strategy orders: Test error[/red]")
