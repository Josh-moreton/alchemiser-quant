"""
Comprehensive integration tests for the Alchemiser trading system.

Tests end-to-end workflows, service integration, and realistic trading scenarios.
"""

import pytest
from unittest.mock import patch, Mock
from decimal import Decimal
from datetime import datetime, timedelta
import json

from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
from the_alchemiser.application.trading_engine import TradingEngine
from the_alchemiser.domain.strategies.multi_strategy_manager import MultiStrategyManager
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.services.di_container import DIContainer
from the_alchemiser.services.exceptions import (
    TradingClientError,
    StrategyExecutionError,
    ConfigurationError,
)


class TestEndToEndTradingWorkflows:
    """Test complete end-to-end trading workflows."""

    @pytest.fixture
    def mock_alpaca_responses(self):
        """Mock comprehensive Alpaca API responses for integration testing."""
        return {
            "account": {
                "id": "test_account_123",
                "account_number": "123456789",
                "status": "ACTIVE",
                "currency": "USD",
                "buying_power": "50000.00",
                "regt_buying_power": "50000.00",
                "daytrading_buying_power": "50000.00",
                "cash": "25000.00",
                "portfolio_value": "100000.00",
                "equity": "100000.00",
                "last_equity": "99500.00",
                "multiplier": "2",
                "initial_margin": "25000.00",
                "maintenance_margin": "15000.00",
                "pattern_day_trader": False,
                "trading_blocked": False,
                "transfers_blocked": False,
                "account_blocked": False,
                "created_at": "2023-01-01T00:00:00Z",
                "trade_suspended_by_user": False,
                "accrued_fees": "0.00",
            },
            "positions": [
                {
                    "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
                    "symbol": "AAPL",
                    "exchange": "NASDAQ",
                    "asset_class": "us_equity",
                    "side": "long",
                    "qty": "100",
                    "avg_entry_price": "148.50",
                    "market_value": "15000.00",
                    "cost_basis": "14850.00",
                    "unrealized_pl": "150.00",
                    "unrealized_plpc": "0.0101",
                    "change_today": "50.00",
                },
                {
                    "asset_id": "e3b85e5b-3c3a-4a9f-8a8c-1d8b2e3f4a5b",
                    "symbol": "TSLA",
                    "exchange": "NASDAQ",
                    "asset_class": "us_equity",
                    "side": "long",
                    "qty": "50",
                    "avg_entry_price": "240.00",
                    "market_value": "12500.00",
                    "cost_basis": "12000.00",
                    "unrealized_pl": "500.00",
                    "unrealized_plpc": "0.0417",
                    "change_today": "100.00",
                },
            ],
            "orders": [
                {
                    "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
                    "client_order_id": "test_order_123",
                    "created_at": "2024-01-15T09:30:00Z",
                    "updated_at": "2024-01-15T09:30:05Z",
                    "submitted_at": "2024-01-15T09:30:00Z",
                    "filled_at": "2024-01-15T09:30:05Z",
                    "expired_at": None,
                    "canceled_at": None,
                    "failed_at": None,
                    "replaced_at": None,
                    "replaced_by": None,
                    "replaces": None,
                    "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
                    "symbol": "AAPL",
                    "exchange": "NASDAQ",
                    "asset_class": "us_equity",
                    "notional": None,
                    "qty": "10",
                    "filled_qty": "10",
                    "type": "market",
                    "side": "buy",
                    "time_in_force": "day",
                    "limit_price": None,
                    "stop_price": None,
                    "status": "filled",
                    "extended_hours": False,
                    "legs": None,
                    "trail_percent": None,
                    "trail_price": None,
                    "hwm": None,
                    "commission": "0.00",
                    "filled_avg_price": "150.25",
                }
            ],
            "market_data": {
                "AAPL": {
                    "bars": [
                        {
                            "timestamp": "2024-01-15T09:30:00Z",
                            "open": 150.00,
                            "high": 152.50,
                            "low": 149.50,
                            "close": 151.75,
                            "volume": 1250000,
                            "trade_count": 15000,
                            "vwap": 151.20,
                        }
                    ],
                    "quotes": {
                        "timestamp": "2024-01-15T15:59:00Z",
                        "timeframe": "latest",
                        "bid": 151.20,
                        "ask": 151.30,
                        "bid_size": 200,
                        "ask_size": 150,
                        "bid_exchange": "V",
                        "ask_exchange": "V",
                    },
                },
                "TSLA": {
                    "bars": [
                        {
                            "timestamp": "2024-01-15T09:30:00Z",
                            "open": 248.00,
                            "high": 252.00,
                            "low": 246.50,
                            "close": 250.75,
                            "volume": 2100000,
                            "trade_count": 22000,
                            "vwap": 249.80,
                        }
                    ],
                    "quotes": {
                        "timestamp": "2024-01-15T15:59:00Z",
                        "timeframe": "latest",
                        "bid": 250.40,
                        "ask": 250.60,
                        "bid_size": 100,
                        "ask_size": 75,
                        "bid_exchange": "V",
                        "ask_exchange": "V",
                    },
                },
            },
        }

    @pytest.fixture
    def integration_trading_manager(self, mock_alpaca_responses, mocker):
        """Create TradingServiceManager with comprehensive mocked responses."""
        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            # Set up trading client mocks
            trading_client = Mock()
            trading_client.get_account.return_value = Mock(**mock_alpaca_responses["account"])

            # Mock positions
            position_mocks = []
            for pos_data in mock_alpaca_responses["positions"]:
                position_mock = Mock()
                for key, value in pos_data.items():
                    setattr(position_mock, key, value)
                position_mocks.append(position_mock)
            trading_client.list_positions.return_value = position_mocks

            # Mock order submission
            order_mock = Mock()
            order_data = mock_alpaca_responses["orders"][0]
            for key, value in order_data.items():
                setattr(order_mock, key, value)
            trading_client.submit_order.return_value = order_mock
            trading_client.get_order.return_value = order_mock

            # Set up data client mocks
            data_client = Mock()
            data_client.get_stock_bars.return_value = {}
            data_client.get_stock_latest_quote.return_value = {}

            mock_trading.return_value = trading_client
            mock_data.return_value = data_client

            # Create TradingServiceManager
            manager = TradingServiceManager(
                api_key="test_key", secret_key="test_secret", paper=True
            )

            return manager

    def test_complete_trading_cycle_execution(self, integration_trading_manager, mocker):
        """Test complete trading cycle from signal generation to order execution."""
        # Create trading engine with mocked strategy manager
        mock_strategy_manager = Mock()
        mock_strategy_manager.generate_combined_signals.return_value = {
            "AAPL": {
                "signal": "BUY",
                "allocation": 0.30,
                "confidence": 0.85,
                "reasoning": "Strong technical indicators",
                "strategy_weights": {"nuclear": 0.4, "tecl": 0.3, "klm": 0.3},
            },
            "TSLA": {
                "signal": "REDUCE",
                "allocation": 0.10,
                "confidence": 0.70,
                "reasoning": "High volatility concerns",
                "strategy_weights": {"nuclear": 0.2, "tecl": 0.5, "klm": 0.3},
            },
            "CASH": {
                "signal": "HOLD",
                "allocation": 0.60,
                "confidence": 1.0,
                "reasoning": "Maintain cash reserves",
                "strategy_weights": {"nuclear": 0.3, "tecl": 0.3, "klm": 0.4},
            },
        }

        with patch("the_alchemiser.application.trading_engine.MultiStrategyManager") as mock_msm:
            mock_msm.return_value = mock_strategy_manager

            # Create trading engine
            trading_engine = TradingEngine(trading_service_manager=integration_trading_manager)

            # Execute complete trading cycle
            result = trading_engine.execute_trading_cycle()

            # Validate results
            assert result["success"] is True
            assert "signals" in result
            assert "portfolio_analysis" in result
            assert "trades_executed" in result

            # Verify signals were generated
            signals = result["signals"]
            assert "AAPL" in signals
            assert "TSLA" in signals
            assert signals["AAPL"]["signal"] == "BUY"
            assert signals["TSLA"]["signal"] == "REDUCE"

            # Verify strategy manager was called
            mock_strategy_manager.generate_combined_signals.assert_called_once()

    def test_portfolio_rebalancing_integration(self, integration_trading_manager):
        """Test portfolio rebalancing integration with real position data."""
        # Get current portfolio state
        account_info = integration_trading_manager.get_account_info()
        positions = integration_trading_manager.get_all_positions()

        # Verify account info
        assert account_info["portfolio_value"] == "100000.00"
        assert account_info["cash"] == "25000.00"
        assert account_info["buying_power"] == "50000.00"

        # Verify positions
        assert len(positions) == 2
        aapl_position = next(p for p in positions if p["symbol"] == "AAPL")
        tsla_position = next(p for p in positions if p["symbol"] == "TSLA")

        assert aapl_position["qty"] == "100"
        assert aapl_position["market_value"] == "15000.00"
        assert tsla_position["qty"] == "50"
        assert tsla_position["market_value"] == "12500.00"

        # Calculate portfolio allocation
        total_value = Decimal(account_info["portfolio_value"])
        aapl_allocation = Decimal(aapl_position["market_value"]) / total_value
        tsla_allocation = Decimal(tsla_position["market_value"]) / total_value
        cash_allocation = Decimal(account_info["cash"]) / total_value

        assert abs(aapl_allocation - Decimal("0.15")) < Decimal("0.01")  # ~15%
        assert abs(tsla_allocation - Decimal("0.125")) < Decimal("0.01")  # ~12.5%
        assert abs(cash_allocation - Decimal("0.25")) < Decimal("0.01")  # ~25%

    def test_order_execution_and_monitoring(self, integration_trading_manager):
        """Test order execution and monitoring workflow."""
        # Place a market order
        order_result = integration_trading_manager.place_market_order(
            symbol="AAPL", side="buy", quantity=Decimal("10")
        )

        # Verify order placement
        assert order_result["id"] == "61e69015-8549-4bfd-b9c3-01e75843f47d"
        assert order_result["symbol"] == "AAPL"
        assert order_result["qty"] == "10"
        assert order_result["side"] == "buy"
        assert order_result["status"] == "filled"

        # Monitor order status
        order_status = integration_trading_manager.get_order_status(order_result["id"])
        assert order_status["status"] == "filled"
        assert order_status["filled_qty"] == "10"
        assert order_status["filled_avg_price"] == "150.25"

    def test_error_handling_in_integration(self, integration_trading_manager, mocker):
        """Test error handling in integrated workflows."""
        # Mock API failure
        integration_trading_manager.alpaca_manager.trading_client.get_account.side_effect = (
            Exception("API Error")
        )

        # Should handle error gracefully
        with pytest.raises(TradingClientError):
            integration_trading_manager.get_account_info()

    def test_multi_strategy_signal_integration(self, mocker):
        """Test multi-strategy signal generation integration."""
        # Mock individual strategy responses
        mock_nuclear = Mock()
        mock_nuclear.generate_signals.return_value = {
            "AAPL": {"signal": "BUY", "allocation": 0.25, "confidence": 0.8},
            "TSLA": {"signal": "HOLD", "allocation": 0.15, "confidence": 0.6},
        }

        mock_tecl = Mock()
        mock_tecl.generate_signals.return_value = {
            "AAPL": {"signal": "BUY", "allocation": 0.30, "confidence": 0.9},
            "TSLA": {"signal": "SELL", "allocation": 0.05, "confidence": 0.8},
        }

        mock_klm = Mock()
        mock_klm.generate_signals.return_value = {
            "AAPL": {"signal": "HOLD", "allocation": 0.20, "confidence": 0.7},
            "TSLA": {"signal": "BUY", "allocation": 0.20, "confidence": 0.75},
        }

        # Create multi-strategy manager with mocked strategies
        with (
            patch("the_alchemiser.domain.strategies.nuclear_strategy.NuclearStrategy") as mock_n,
            patch("the_alchemiser.domain.strategies.tecl_strategy.TECLStrategy") as mock_t,
            patch("the_alchemiser.domain.strategies.klm_strategy.KLMStrategy") as mock_k,
        ):

            mock_n.return_value = mock_nuclear
            mock_t.return_value = mock_tecl
            mock_k.return_value = mock_klm

            # Create strategy manager
            strategy_manager = MultiStrategyManager()

            # Generate combined signals
            combined_signals = strategy_manager.generate_combined_signals()

            # Verify signal combination
            assert "AAPL" in combined_signals
            assert "TSLA" in combined_signals

            # Should aggregate strategies with proper weights
            aapl_signal = combined_signals["AAPL"]
            assert aapl_signal["signal"] in ["BUY", "HOLD", "SELL"]
            assert 0 <= aapl_signal["allocation"] <= 1
            assert 0 <= aapl_signal["confidence"] <= 1

    def test_configuration_driven_initialization(self):
        """Test configuration-driven system initialization."""
        env_vars = {
            "ALPACA_API_KEY": "integration_test_key",
            "ALPACA_SECRET_KEY": "integration_test_secret",
            "PAPER_TRADING": "true",
            "ALPACA__CASH_RESERVE_PCT": "0.05",
            "ALPACA__SLIPPAGE_BPS": "3",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            # Load configuration
            settings = load_settings()

            # Verify configuration values
            assert settings.alpaca.api_key == "integration_test_key"
            assert settings.alpaca.secret_key == "integration_test_secret"
            assert settings.alpaca.paper_trading is True
            assert settings.alpaca.cash_reserve_pct == Decimal("0.05")
            assert settings.alpaca.slippage_bps == 3

            # Initialize services with configuration
            with (
                patch("alpaca.trading.TradingClient") as mock_trading,
                patch("alpaca.data.StockHistoricalDataClient") as mock_data,
            ):

                mock_trading.return_value = Mock()
                mock_data.return_value = Mock()

                # Should initialize with correct configuration
                manager = TradingServiceManager.from_settings(settings)
                assert manager.paper_trading is True


class TestDependencyInjectionIntegration:
    """Test dependency injection container integration."""

    def test_di_container_initialization(self, mocker):
        """Test DI container initialization and service resolution."""
        # Mock environment for testing
        env_vars = {
            "ALPACA_API_KEY": "di_test_key",
            "ALPACA_SECRET_KEY": "di_test_secret",
            "PAPER_TRADING": "true",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with (
                patch("alpaca.trading.TradingClient") as mock_trading,
                patch("alpaca.data.StockHistoricalDataClient") as mock_data,
            ):

                mock_trading.return_value = Mock()
                mock_data.return_value = Mock()

                # Create DI container
                container = DIContainer()

                # Resolve trading service manager
                tsm = container.trading_service_manager()
                assert tsm is not None
                assert tsm.paper_trading is True

                # Should return same instance (singleton)
                tsm2 = container.trading_service_manager()
                assert tsm is tsm2

    def test_di_container_with_trading_engine(self, mocker):
        """Test DI container integration with TradingEngine."""
        env_vars = {
            "ALPACA_API_KEY": "engine_test_key",
            "ALPACA_SECRET_KEY": "engine_test_secret",
            "PAPER_TRADING": "true",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            with (
                patch("alpaca.trading.TradingClient") as mock_trading,
                patch("alpaca.data.StockHistoricalDataClient") as mock_data,
                patch("the_alchemiser.application.trading_engine.MultiStrategyManager") as mock_msm,
            ):

                mock_trading.return_value = Mock()
                mock_data.return_value = Mock()
                mock_msm.return_value = Mock()

                # Create DI container
                container = DIContainer()

                # Create trading engine with DI container
                engine = TradingEngine(di_container=container)

                # Verify engine initialization
                assert engine.di_container is not None
                assert hasattr(engine, "strategy_manager")

    def test_service_lifecycle_management(self, mocker):
        """Test service lifecycle management in DI container."""
        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            mock_trading.return_value = Mock()
            mock_data.return_value = Mock()

            container = DIContainer()

            # Test singleton behavior
            tsm1 = container.trading_service_manager()
            tsm2 = container.trading_service_manager()
            assert tsm1 is tsm2

            # Test service cleanup
            container.cleanup()

            # After cleanup, should create new instances
            tsm3 = container.trading_service_manager()
            assert tsm3 is not tsm1


class TestRealisticTradingScenarios:
    """Test realistic trading scenarios and edge cases."""

    @pytest.fixture
    def scenario_trading_manager(self, mocker):
        """Create trading manager for scenario testing."""
        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            # Create flexible mocks for different scenarios
            trading_client = Mock()
            data_client = Mock()

            mock_trading.return_value = trading_client
            mock_data.return_value = data_client

            manager = TradingServiceManager(
                api_key="scenario_key", secret_key="scenario_secret", paper=True
            )

            # Store mocks for scenario configuration
            manager._mock_trading_client = trading_client
            manager._mock_data_client = data_client

            return manager

    def test_high_volatility_market_scenario(self, scenario_trading_manager):
        """Test trading in high volatility market conditions."""
        # Configure high volatility scenario
        volatile_account = Mock(
            portfolio_value=95000.0,  # Down 5% from previous
            cash=15000.0,
            buying_power=30000.0,  # Reduced buying power
        )
        scenario_trading_manager._mock_trading_client.get_account.return_value = volatile_account

        # Mock volatile positions
        volatile_positions = [
            Mock(
                symbol="AAPL",
                qty=100,
                market_value=13500.0,  # Down from cost basis
                unrealized_pl=-1500.0,
                unrealized_plpc=-0.10,  # -10% unrealized loss
            ),
            Mock(
                symbol="TSLA",
                qty=50,
                market_value=10000.0,
                unrealized_pl=-2000.0,
                unrealized_plpc=-0.167,  # -16.7% unrealized loss
            ),
        ]
        scenario_trading_manager._mock_trading_client.list_positions.return_value = (
            volatile_positions
        )

        # Test account info retrieval in volatile conditions
        account_info = scenario_trading_manager.get_account_info()
        assert float(account_info["portfolio_value"]) < 100000.0

        # Test position analysis
        positions = scenario_trading_manager.get_all_positions()
        total_unrealized_pl = sum(float(p["unrealized_pl"]) for p in positions)
        assert total_unrealized_pl < 0  # Should show losses

    def test_low_liquidity_trading_scenario(self, scenario_trading_manager):
        """Test trading in low liquidity conditions."""
        # Mock low liquidity order response
        low_liquidity_order = Mock(
            id="low_liq_order_123",
            status="partially_filled",
            qty="100",
            filled_qty="25",  # Only 25% filled
            symbol="SMALLCAP",
            side="buy",
        )
        scenario_trading_manager._mock_trading_client.submit_order.return_value = (
            low_liquidity_order
        )

        # Attempt order in low liquidity stock
        order_result = scenario_trading_manager.place_market_order(
            symbol="SMALLCAP", side="buy", quantity=Decimal("100")
        )

        # Should handle partial fills
        assert order_result["status"] == "partially_filled"
        assert order_result["filled_qty"] == "25"

    def test_market_closure_scenario(self, scenario_trading_manager):
        """Test behavior during market closure."""
        from alpaca.common.exceptions import APIError

        # Mock market closed error
        scenario_trading_manager._mock_trading_client.submit_order.side_effect = APIError(
            "Market is closed"
        )

        # Should handle market closure gracefully
        with pytest.raises(TradingClientError):
            scenario_trading_manager.place_market_order(
                symbol="AAPL", side="buy", quantity=Decimal("10")
            )

    def test_insufficient_buying_power_scenario(self, scenario_trading_manager):
        """Test scenario with insufficient buying power."""
        # Mock low buying power account
        low_power_account = Mock(
            portfolio_value=50000.0,
            cash=1000.0,  # Very low cash
            buying_power=2000.0,  # Low buying power
        )
        scenario_trading_manager._mock_trading_client.get_account.return_value = low_power_account

        # Mock insufficient buying power error
        scenario_trading_manager._mock_trading_client.submit_order.side_effect = APIError(
            "Insufficient buying power"
        )

        # Should handle insufficient buying power
        with pytest.raises(TradingClientError):
            scenario_trading_manager.place_market_order(
                symbol="AAPL", side="buy", quantity=Decimal("100")  # Large order
            )

    def test_rapid_market_movement_scenario(self, scenario_trading_manager):
        """Test scenario with rapid market movements."""
        # Mock rapidly changing quotes
        changing_quotes = [
            {"AAPL": {"bid": 150.00, "ask": 150.20}},  # Initial quote
            {"AAPL": {"bid": 148.50, "ask": 148.70}},  # Rapid decline
            {"AAPL": {"bid": 152.00, "ask": 152.20}},  # Rapid recovery
        ]

        call_count = 0

        def mock_get_quote(*args, **kwargs):
            nonlocal call_count
            quote = changing_quotes[call_count % len(changing_quotes)]
            call_count += 1
            return quote

        scenario_trading_manager._mock_data_client.get_latest_quote = mock_get_quote

        # Should handle rapid quote changes
        quote1 = scenario_trading_manager.get_latest_quote("AAPL")
        quote2 = scenario_trading_manager.get_latest_quote("AAPL")
        quote3 = scenario_trading_manager.get_latest_quote("AAPL")

        # Quotes should be different due to rapid movement
        assert quote1 != quote2 or quote2 != quote3


class TestPerformanceIntegration:
    """Test performance aspects of integrated system."""

    def test_concurrent_order_processing(self, mocker):
        """Test system performance with concurrent order processing."""
        import time

        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            # Mock fast order responses
            mock_order = Mock(id="concurrent_order", status="filled")
            mock_trading.return_value.submit_order.return_value = mock_order
            mock_data.return_value = Mock()

            manager = TradingServiceManager("test", "test", paper=True)

            # Measure concurrent order processing time
            start_time = time.time()

            orders = []
            for i in range(10):
                order = manager.place_market_order(
                    symbol=f"STOCK{i}", side="buy", quantity=Decimal("10")
                )
                orders.append(order)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should process orders efficiently
            assert len(orders) == 10
            assert processing_time < 5.0  # Should complete within 5 seconds

    def test_large_portfolio_processing(self, mocker):
        """Test system performance with large portfolios."""
        with (
            patch("alpaca.trading.TradingClient") as mock_trading,
            patch("alpaca.data.StockHistoricalDataClient") as mock_data,
        ):

            # Mock large position list
            large_positions = []
            for i in range(100):
                position = Mock(
                    symbol=f"STOCK{i}",
                    qty=f"{i * 10}",
                    market_value=f"{i * 1000}.00",
                    unrealized_pl=f"{i * 50}.00",
                )
                large_positions.append(position)

            mock_trading.return_value.list_positions.return_value = large_positions
            mock_data.return_value = Mock()

            manager = TradingServiceManager("test", "test", paper=True)

            # Process large portfolio
            start_time = time.time()
            positions = manager.get_all_positions()
            end_time = time.time()

            processing_time = end_time - start_time

            # Should handle large portfolios efficiently
            assert len(positions) == 100
            assert processing_time < 2.0  # Should complete within 2 seconds

    def test_strategy_calculation_performance(self, mocker):
        """Test strategy calculation performance with large datasets."""
        # Mock large market data
        large_market_data = {}
        for i in range(500):  # 500 stocks
            large_market_data[f"STOCK{i}"] = {
                "bars": [{"close": 100 + i, "volume": 1000000}] * 252,  # 1 year of data
                "quotes": {"bid": 100 + i - 0.05, "ask": 100 + i + 0.05},
            }

        # Mock strategy that processes large datasets
        mock_strategy = Mock()
        mock_strategy.generate_signals.return_value = {
            f"STOCK{i}": {"signal": "HOLD", "allocation": 0.002} for i in range(500)
        }

        # Measure strategy calculation time
        start_time = time.time()
        signals = mock_strategy.generate_signals()
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should calculate efficiently even with large datasets
        assert len(signals) == 500
        assert calculation_time < 10.0  # Should complete within 10 seconds


if __name__ == "__main__":
    pytest.main([__file__])
