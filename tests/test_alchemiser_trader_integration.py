#!/usr/bin/env python3
"""
Integration Test for TradingEngine

Tests the unified TradingEngine functionality to ensure all components
work together correctly after the consolidation refactoring.

This test verifies:
1. Account info retrieval works correctly
2. Position data is correctly structured and accessible
3. Multi-strategy execution produces expected results
4. Portfolio rebalancing behavior works as expected
5. Order execution logic is preserved
6. Error handling is robust
"""

from unittest.mock import Mock, patch

import pytest
from alpaca.trading.enums import OrderSide

# NOTE: Old classes have been consolidated into TradingEngine
# from the_alchemiser.execution.alpaca_trader import AlpacaTradingBot  # Now .old file
# from the_alchemiser.execution.multi_strategy_trader import MultiStrategyAlpacaTrader  # Now .old file
from the_alchemiser.core.trading.strategy_manager import StrategyType

# Import the classes we're testing
from the_alchemiser.execution.trading_engine import TradingEngine


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    return {
        "alpaca": {
            "paper_endpoint": "https://paper-api.alpaca.markets/v2",
            "endpoint": "https://api.alpaca.markets/v2",
            "cash_reserve_pct": 0.05,
            "slippage_bps": 5,
        },
        "strategy": {
            "default_strategy_allocations": {"nuclear": 0.4, "tecl": 0.6},
            "poll_timeout": 30,
            "poll_interval": 2.0,
        },
        "data": {"cache_duration": 300, "default_symbol": "AAPL"},
        "logging": {"level": "INFO"},
    }


@pytest.fixture
def mock_account_data():
    """Mock account data that should be returned consistently"""
    mock_account = Mock()
    mock_account.account_number = "TEST123"
    mock_account.portfolio_value = 10000.0
    mock_account.equity = 10000.0
    mock_account.buying_power = 5000.0
    mock_account.cash = 1000.0
    mock_account.day_trade_count = 0
    mock_account.status = "ACTIVE"

    # Create mock position objects that work with the old trader's getattr() calls
    mock_spy_position = Mock()
    mock_spy_position.symbol = "SPY"
    mock_spy_position.qty = 10
    mock_spy_position.market_value = 4500.0
    mock_spy_position.cost_basis = 4450.0
    mock_spy_position.unrealized_pl = 50.0
    mock_spy_position.unrealized_plpc = 0.011
    mock_spy_position.current_price = 450.0

    mock_qqq_position = Mock()
    mock_qqq_position.symbol = "QQQ"
    mock_qqq_position.qty = 5
    mock_qqq_position.market_value = 2000.0
    mock_qqq_position.cost_basis = 2025.0
    mock_qqq_position.unrealized_pl = -25.0
    mock_qqq_position.unrealized_plpc = -0.012
    mock_qqq_position.current_price = 400.0

    return {
        "account": mock_account,
        "portfolio_history": {
            "equity": [9900, 10000],
            "profit_loss": [100],
            "profit_loss_pct": [0.01],
        },
        "positions": [mock_spy_position, mock_qqq_position],
        "positions_dict": {  # For the new trader that expects dict format
            "SPY": {
                "symbol": "SPY",
                "qty": 10,
                "market_value": 4500.0,
                "unrealized_pl": 50.0,
                "unrealized_plpc": 0.011,
                "current_price": 450.0,
                "avg_entry_price": 445.0,
                "side": "long",
                "change_today": 5.0,
            },
            "QQQ": {
                "symbol": "QQQ",
                "qty": 5,
                "market_value": 2000.0,
                "unrealized_pl": -25.0,
                "unrealized_plpc": -0.012,
                "current_price": 400.0,
                "avg_entry_price": 405.0,
                "side": "long",
                "change_today": -5.0,
            },
        },
    }


@pytest.fixture
def mock_strategy_signals():
    """Mock strategy signals for testing"""
    return {
        StrategyType.NUCLEAR: {
            "action": "BUY",
            "symbol": "SPY",
            "reason": "Nuclear signal triggered",
            "timestamp": "2025-07-29T10:00:00",
        },
        StrategyType.TECL: {
            "action": "HOLD",
            "symbol": "QQQ",
            "reason": "TECL signal neutral",
            "timestamp": "2025-07-29T10:00:00",
        },
    }


@pytest.fixture
def mock_consolidated_portfolio():
    """Mock consolidated portfolio allocation"""
    return {"SPY": 0.6, "QQQ": 0.3, "BIL": 0.1}


@pytest.fixture
def mock_orders_executed():
    """Mock executed orders"""
    return [
        {
            "symbol": "SPY",
            "qty": 5.0,
            "side": OrderSide.BUY,
            "order_id": "order123",
            "estimated_value": 2250.0,
            "price": 450.0,
            "timestamp": "2025-07-29T10:01:00",
            "status": "filled",
        },
        {
            "symbol": "BIL",
            "qty": 10.0,
            "side": OrderSide.BUY,
            "order_id": "order124",
            "estimated_value": 1000.0,
            "price": 100.0,
            "timestamp": "2025-07-29T10:02:00",
            "status": "filled",
        },
    ]


class TestTradingEngineIntegration:
    """Integration tests for the unified TradingEngine"""

    def test_account_info_consistency(self, mock_config, mock_account_data):
        """Test that account info retrieval works correctly with the unified TradingEngine"""

        with (
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info"
            ) as mock_get_account,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_portfolio_history"
            ) as mock_get_history,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_open_positions"
            ) as mock_get_open_pos,
        ):
            # Set up mocks
            mock_get_account.return_value = mock_account_data["account"]
            mock_get_history.return_value = mock_account_data["portfolio_history"]
            mock_get_open_pos.return_value = mock_account_data[
                "positions_dict"
            ].values()  # Use dict format for open positions

            # Initialize the unified trader
            new_trader = TradingEngine(paper_trading=True, config=mock_config)

            # Get account info from the trader
            account_info = new_trader.get_account_info()

            # Verify account info is correctly structured and contains expected data
            assert account_info["account_number"] == "TEST123"
            assert account_info["portfolio_value"] == 10000.0
            assert account_info["equity"] == 10000.0
            assert account_info["buying_power"] == 5000.0
            assert account_info["cash"] == 1000.0
            assert account_info["day_trade_count"] == 0
            assert account_info["status"] == "ACTIVE"

            # Verify portfolio history is included
            assert "portfolio_history" in account_info
            assert account_info["portfolio_history"]["equity"] == [9900, 10000]

    def test_positions_consistency(self, mock_config, mock_account_data):
        """Test that position retrieval works correctly with the unified TradingEngine"""

        # Initialize trader
        new_trader = TradingEngine(paper_trading=True, config=mock_config)

        # Mock get_positions for the trader to return appropriate format
        with patch.object(
            new_trader.data_provider,
            "get_positions",
            return_value=list(mock_account_data["positions_dict"].values()),
        ):
            # Get positions from the trader
            positions = new_trader.get_positions()

            # Verify positions are correctly structured
            assert len(positions) == 2

            # Check specific position data
            for symbol in ["SPY", "QQQ"]:
                assert symbol in positions

                # Verify position values are correctly retrieved
                if symbol == "SPY":
                    assert positions[symbol]["qty"] == 10
                    assert positions[symbol]["market_value"] == 4500.0
                elif symbol == "QQQ":
                    assert positions[symbol]["qty"] == 5
                    assert positions[symbol]["market_value"] == 2000.0

    def test_multi_strategy_execution_parity(
        self,
        mock_config,
        mock_account_data,
        mock_strategy_signals,
        mock_consolidated_portfolio,
        mock_orders_executed,
    ):
        """Test that multi-strategy execution works correctly with the unified TradingEngine"""

        # Create comprehensive mocks for all dependencies
        with (
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info"
            ) as mock_get_account,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_portfolio_history"
            ) as mock_get_history,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_open_positions"
            ) as mock_get_open_pos,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_positions"
            ) as mock_get_positions,
            patch(
                "the_alchemiser.core.trading.strategy_manager.MultiStrategyManager.run_all_strategies"
            ) as mock_run_strategies,
            patch(
                "the_alchemiser.execution.portfolio_rebalancer.PortfolioRebalancer.rebalance_portfolio"
            ) as mock_rebalance_new,
        ):
            # Set up mocks
            mock_get_account.return_value = mock_account_data["account"]
            mock_get_history.return_value = mock_account_data["portfolio_history"]
            mock_get_open_pos.return_value = mock_account_data["positions_dict"].values()
            mock_get_positions.return_value = list(mock_account_data["positions_dict"].values())
            mock_run_strategies.return_value = (mock_strategy_signals, mock_consolidated_portfolio)
            mock_rebalance_new.return_value = mock_orders_executed

            # Initialize trader
            strategy_allocations = {StrategyType.NUCLEAR: 0.6, StrategyType.TECL: 0.4}

            new_trader = TradingEngine(
                paper_trading=True, strategy_allocations=strategy_allocations, config=mock_config
            )

            # Execute multi-strategy
            result = new_trader.execute_multi_strategy()

            # Verify execution was successful
            assert result.success == True

            # Verify strategy signals are present
            assert result.strategy_signals is not None
            assert len(result.strategy_signals) == 2  # NUCLEAR and TECL

            # Verify consolidated portfolio is present
            assert result.consolidated_portfolio is not None
            assert "SPY" in result.consolidated_portfolio

            # Verify orders were executed
            assert result.orders_executed is not None
            assert len(result.orders_executed) == len(mock_orders_executed)

            # Verify account info is captured
            assert result.account_info_before is not None
            assert result.account_info_after is not None
            assert result.account_info_before["portfolio_value"] == 10000.0

    def test_portfolio_rebalancing_consistency(
        self, mock_config, mock_account_data, mock_consolidated_portfolio, mock_orders_executed
    ):
        """Test that portfolio rebalancing works correctly with the unified TradingEngine"""

        with (
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info"
            ) as mock_get_account,
            patch(
                "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_positions"
            ) as mock_get_positions,
            patch(
                "the_alchemiser.execution.portfolio_rebalancer.PortfolioRebalancer.rebalance_portfolio"
            ) as mock_rebalance_new,
        ):
            # Set up mocks
            mock_get_account.return_value = mock_account_data["account"]
            mock_get_positions.return_value = list(mock_account_data["positions_dict"].values())
            mock_rebalance_new.return_value = mock_orders_executed

            # Initialize trader
            new_trader = TradingEngine(paper_trading=True, config=mock_config)

            # Execute rebalancing
            orders = new_trader.rebalance_portfolio(mock_consolidated_portfolio)

            # Verify orders were returned
            assert orders is not None
            assert len(orders) == len(mock_orders_executed)

            # Verify order structure
            for order in orders:
                assert "symbol" in order
                assert "qty" in order
                assert "side" in order

    def test_display_target_vs_current_allocations(self, mock_config, mock_account_data):
        """Test the display_target_vs_current_allocations method works correctly"""

        with patch(
            "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info"
        ) as mock_get_account:
            mock_get_account.return_value = mock_account_data["account"]

            new_trader = TradingEngine(paper_trading=True, config=mock_config)

            target_portfolio = {"SPY": 0.6, "QQQ": 0.4}
            account_info = {"portfolio_value": 10000.0}
            current_positions = {"SPY": {"market_value": 5000.0}, "QQQ": {"market_value": 3000.0}}

            target_values, current_values = new_trader.display_target_vs_current_allocations(
                target_portfolio, account_info, current_positions
            )

            # Verify calculations
            assert target_values["SPY"] == 6000.0  # 10000 * 0.6
            assert target_values["QQQ"] == 4000.0  # 10000 * 0.4
            assert current_values["SPY"] == 5000.0
            assert current_values["QQQ"] == 3000.0

    def test_error_handling_consistency(self, mock_config):
        """Test that error handling works correctly in the unified TradingEngine"""

        # Mock a failure scenario
        with patch(
            "the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info"
        ) as mock_get_account:
            mock_get_account.side_effect = Exception("API Error")

            new_trader = TradingEngine(paper_trading=True, config=mock_config)

            # Should handle errors gracefully
            result = new_trader.execute_multi_strategy()

            # Should return failed result
            assert result.success == False

            # Should have error information
            assert "error" in result.execution_summary

    def test_initialization_consistency(self, mock_config):
        """Test that the unified TradingEngine initializes correctly with consistent configuration"""

        strategy_allocations = {StrategyType.NUCLEAR: 0.7, StrategyType.TECL: 0.3}

        # Initialize trader with parameters
        new_trader = TradingEngine(
            paper_trading=True,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=True,
            config=mock_config,
        )

        # Verify consistent configuration
        assert new_trader.paper_trading == True
        assert new_trader.ignore_market_hours == True
        assert new_trader.config == mock_config

        # Verify strategy allocations are correctly set
        assert new_trader.strategy_manager.strategy_allocations[StrategyType.NUCLEAR] == 0.7
        assert new_trader.strategy_manager.strategy_allocations[StrategyType.TECL] == 0.3


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
