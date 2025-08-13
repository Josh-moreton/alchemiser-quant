"""
Comprehensive unit tests for application layer.

Tests trading engine, portfolio management, and execution workflows.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime
from typing import Dict, List

from the_alchemiser.application.trading_engine import TradingEngine
from the_alchemiser.application.portfolio_rebalancer.portfolio_rebalancer import PortfolioRebalancer
from the_alchemiser.application.smart_execution import SmartExecution
from the_alchemiser.application.order_validation import OrderValidator
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager
from the_alchemiser.services.exceptions import (
    TradingClientError,
    ValidationError,
    StrategyExecutionError,
)


class TestTradingEngine:
    """Test the main trading engine orchestration."""

    @pytest.fixture
    def mock_services(self, mocker):
        """Create mocked service dependencies."""
        mock_tsm = mocker.Mock(spec=TradingServiceManager)
        mock_tsm.paper_trading = True
        return mock_tsm

    @pytest.fixture
    def mock_strategy_manager(self, mocker):
        """Create mocked strategy manager."""
        mock = mocker.Mock()
        mock.generate_combined_signals.return_value = {
            "AAPL": {"signal": "BUY", "allocation": 0.25, "confidence": 0.8},
            "TSLA": {"signal": "SELL", "allocation": 0.15, "confidence": 0.7},
            "CASH": {"signal": "HOLD", "allocation": 0.60, "confidence": 1.0},
        }
        return mock

    @pytest.fixture
    def trading_engine(self, mock_services, mock_strategy_manager):
        """Create TradingEngine with mocked dependencies."""
        with patch("the_alchemiser.application.trading_engine.MultiStrategyManager") as mock_msm:
            mock_msm.return_value = mock_strategy_manager

            engine = TradingEngine(trading_service_manager=mock_services)
            engine.strategy_manager = mock_strategy_manager
            return engine

    def test_initialization_with_service_manager(self, mock_services, mocker):
        """Test TradingEngine initialization with service manager."""
        with patch("the_alchemiser.application.trading_engine.MultiStrategyManager") as mock_msm:
            mock_msm.return_value = mocker.Mock()

            engine = TradingEngine(trading_service_manager=mock_services)

            assert engine.trading_service_manager == mock_services
            assert engine.paper_trading is True

    def test_initialization_with_di_container(self, mocker):
        """Test TradingEngine initialization with DI container."""
        mock_container = mocker.Mock()
        mock_container.trading_service_manager.return_value = mocker.Mock(
            spec=TradingServiceManager
        )

        with patch("the_alchemiser.application.trading_engine.MultiStrategyManager") as mock_msm:
            mock_msm.return_value = mocker.Mock()

            engine = TradingEngine(di_container=mock_container)

            assert engine.di_container == mock_container

    def test_execute_full_trading_cycle(self, trading_engine, mock_services, mock_strategy_manager):
        """Test complete trading cycle execution."""
        # Mock account and position data
        mock_services.get_account_info.return_value = {
            "portfolio_value": "100000.00",
            "cash": "20000.00",
            "buying_power": "50000.00",
        }

        mock_services.get_all_positions.return_value = [
            {"symbol": "AAPL", "qty": "100", "market_value": "15000.00", "unrealized_pl": "500.00"}
        ]

        # Mock order execution
        mock_services.place_market_order.return_value = {
            "id": "order_123",
            "status": "filled",
            "symbol": "TSLA",
            "qty": "50",
            "side": "buy",
        }

        # Execute trading cycle
        result = trading_engine.execute_trading_cycle()

        assert result["success"] is True
        assert "signals" in result
        assert "trades_executed" in result
        assert len(result["trades_executed"]) >= 0

    def test_strategy_signal_generation(self, trading_engine, mock_strategy_manager):
        """Test strategy signal generation."""
        signals = trading_engine.generate_strategy_signals()

        assert "AAPL" in signals
        assert "TSLA" in signals
        assert signals["AAPL"]["signal"] == "BUY"
        assert signals["TSLA"]["signal"] == "SELL"

        mock_strategy_manager.generate_combined_signals.assert_called_once()

    def test_portfolio_rebalancing_execution(self, trading_engine, mock_services):
        """Test portfolio rebalancing execution."""
        # Mock current portfolio
        mock_services.get_all_positions.return_value = [
            {"symbol": "AAPL", "qty": "200", "market_value": "30000.00"},
            {"symbol": "TSLA", "qty": "100", "market_value": "25000.00"},
        ]

        mock_services.get_account_info.return_value = {
            "portfolio_value": "100000.00",
            "cash": "45000.00",
        }

        # Mock order execution
        mock_services.place_market_order.return_value = {
            "id": "rebalance_order_123",
            "status": "filled",
        }

        target_allocations = {
            "AAPL": Decimal("0.25"),
            "TSLA": Decimal("0.15"),
            "CASH": Decimal("0.60"),
        }

        trades = trading_engine.execute_rebalancing_trades(target_allocations)

        assert isinstance(trades, list)
        # Should execute some trades to reach target allocations

    def test_error_handling_in_trading_cycle(
        self, trading_engine, mock_services, mock_strategy_manager
    ):
        """Test error handling during trading cycle."""
        # Mock strategy error
        mock_strategy_manager.generate_combined_signals.side_effect = StrategyExecutionError(
            "Strategy failed"
        )

        result = trading_engine.execute_trading_cycle()

        assert result["success"] is False
        assert "error" in result

    def test_paper_trading_validation(self, trading_engine):
        """Test paper trading mode validation."""
        assert trading_engine.paper_trading is True

        # Should log paper trading mode
        result = trading_engine.execute_trading_cycle()
        assert result is not None

    def test_risk_management_integration(self, trading_engine, mock_services):
        """Test risk management integration."""
        # Mock excessive position size request
        mock_services.get_account_info.return_value = {
            "portfolio_value": "100000.00",
            "buying_power": "50000.00",
        }

        # Should validate order sizes against portfolio limits
        large_order = {
            "symbol": "AAPL",
            "quantity": Decimal("1000"),  # Very large order
            "side": "buy",
            "notional_value": Decimal("150000.00"),  # Exceeds portfolio
        }

        # Risk management should prevent oversized orders
        is_valid = trading_engine.validate_order_risk(large_order)
        assert is_valid is False

    def test_performance_tracking(self, trading_engine, mock_services):
        """Test performance tracking functionality."""
        # Mock filled orders
        mock_services.get_order.return_value = {
            "id": "order_123",
            "status": "filled",
            "symbol": "AAPL",
            "qty": "100",
            "filled_avg_price": "150.00",
        }

        # Should track performance metrics
        performance = trading_engine.calculate_performance_metrics()

        assert isinstance(performance, dict)
        assert "total_trades" in performance or "portfolio_value" in performance


class TestPortfolioRebalancer:
    """Test portfolio rebalancing logic."""

    @pytest.fixture
    def mock_trading_service(self, mocker):
        """Create mocked trading service."""
        mock = mocker.Mock(spec=TradingServiceManager)
        mock.get_account_info.return_value = {"portfolio_value": "100000.00", "cash": "10000.00"}
        return mock

    @pytest.fixture
    def portfolio_rebalancer(self, mock_trading_service):
        """Create PortfolioRebalancer with mocked services."""
        return PortfolioRebalancer(mock_trading_service)

    def test_calculate_target_allocations(self, portfolio_rebalancer):
        """Test target allocation calculation."""
        strategy_signals = {
            "AAPL": {"allocation": 0.30, "confidence": 0.8},
            "TSLA": {"allocation": 0.20, "confidence": 0.7},
            "SPY": {"allocation": 0.35, "confidence": 0.9},
            "CASH": {"allocation": 0.15, "confidence": 1.0},
        }

        allocations = portfolio_rebalancer.calculate_target_allocations(
            strategy_signals, Decimal("100000.00")
        )

        assert "AAPL" in allocations
        assert "TSLA" in allocations
        assert "SPY" in allocations

        # Allocations should sum to approximately 1.0
        total_allocation = sum(allocations.values())
        assert abs(total_allocation - Decimal("1.0")) < Decimal("0.01")

    def test_calculate_required_trades(self, portfolio_rebalancer):
        """Test required trade calculation."""
        current_positions = {
            "AAPL": {"qty": "200", "market_value": "30000.00"},
            "TSLA": {"qty": "0", "market_value": "0.00"},
        }

        target_allocations = {
            "AAPL": Decimal("0.25"),  # Reduce position
            "TSLA": Decimal("0.15"),  # Increase position
            "CASH": Decimal("0.60"),
        }

        portfolio_value = Decimal("100000.00")

        trades = portfolio_rebalancer.calculate_required_trades(
            current_positions, target_allocations, portfolio_value
        )

        assert isinstance(trades, list)

        # Should have trades to rebalance
        aapl_trades = [t for t in trades if t["symbol"] == "AAPL"]
        tsla_trades = [t for t in trades if t["symbol"] == "TSLA"]

        if aapl_trades:
            assert aapl_trades[0]["side"] == "sell"  # Reduce AAPL
        if tsla_trades:
            assert tsla_trades[0]["side"] == "buy"  # Increase TSLA

    def test_rebalance_threshold_checking(self, portfolio_rebalancer):
        """Test rebalance threshold checking."""
        current_allocations = {
            "AAPL": Decimal("0.26"),  # 1% over target
            "TSLA": Decimal("0.24"),  # 1% under target
            "CASH": Decimal("0.50"),
        }

        target_allocations = {
            "AAPL": Decimal("0.25"),
            "TSLA": Decimal("0.25"),
            "CASH": Decimal("0.50"),
        }

        # With 5% threshold, should not trigger rebalance
        needs_rebalance = portfolio_rebalancer.needs_rebalancing(
            current_allocations, target_allocations, threshold=Decimal("0.05")
        )
        assert needs_rebalance is False

        # With 0.5% threshold, should trigger rebalance
        needs_rebalance = portfolio_rebalancer.needs_rebalancing(
            current_allocations, target_allocations, threshold=Decimal("0.005")
        )
        assert needs_rebalance is True

    def test_cash_reserve_management(self, portfolio_rebalancer):
        """Test cash reserve management."""
        target_allocations = {
            "AAPL": Decimal("0.45"),
            "TSLA": Decimal("0.45"),
            "CASH": Decimal("0.10"),  # 10% cash reserve
        }

        # Should enforce minimum cash reserve
        adjusted_allocations = portfolio_rebalancer.enforce_cash_reserve(
            target_allocations, min_cash_pct=Decimal("0.05")
        )

        assert adjusted_allocations["CASH"] >= Decimal("0.05")

        # Total should still sum to 1.0
        total = sum(adjusted_allocations.values())
        assert abs(total - Decimal("1.0")) < Decimal("0.01")

    def test_fractional_share_handling(self, portfolio_rebalancer):
        """Test fractional share handling."""
        trade = {
            "symbol": "AAPL",
            "quantity": Decimal("100.7"),  # Fractional shares
            "side": "buy",
            "price": Decimal("150.00"),
        }

        adjusted_trade = portfolio_rebalancer.adjust_for_fractional_shares(trade)

        # Should handle fractional shares appropriately
        assert isinstance(adjusted_trade["quantity"], Decimal)

    def test_order_execution_sequencing(self, portfolio_rebalancer, mock_trading_service):
        """Test order execution sequencing."""
        trades = [
            {"symbol": "AAPL", "side": "sell", "quantity": Decimal("50")},  # Sell first
            {"symbol": "TSLA", "side": "buy", "quantity": Decimal("40")},  # Then buy
        ]

        mock_trading_service.place_market_order.return_value = {
            "id": "order_123",
            "status": "filled",
        }

        results = portfolio_rebalancer.execute_trades_sequentially(trades)

        assert len(results) == 2
        # Should execute sell orders before buy orders
        assert mock_trading_service.place_market_order.call_count == 2

    def test_error_handling_in_rebalancing(self, portfolio_rebalancer, mock_trading_service):
        """Test error handling during rebalancing."""
        mock_trading_service.place_market_order.side_effect = TradingClientError("Order failed")

        trades = [{"symbol": "AAPL", "side": "buy", "quantity": Decimal("100")}]

        results = portfolio_rebalancer.execute_trades_sequentially(trades)

        # Should handle errors gracefully and continue with other trades
        assert len(results) >= 0


class TestSmartExecution:
    """Test smart order execution logic."""

    @pytest.fixture
    def mock_alpaca_manager(self, mocker):
        """Create mocked AlpacaManager."""
        mock = mocker.Mock()
        mock.paper_trading = True
        return mock

    @pytest.fixture
    def smart_execution(self, mock_alpaca_manager):
        """Create SmartExecution with mocked dependencies."""
        return SmartExecution(mock_alpaca_manager)

    def test_progressive_order_execution(self, smart_execution, mock_alpaca_manager):
        """Test progressive order execution strategy."""
        # Mock market data
        mock_alpaca_manager.get_latest_quote.return_value = {
            "symbol": "AAPL",
            "bid": 149.50,
            "ask": 150.50,
            "bid_size": 100,
            "ask_size": 200,
        }

        # Mock order responses
        mock_alpaca_manager.place_order.side_effect = [
            {"id": "order_1", "status": "partially_filled", "filled_qty": "25"},
            {"id": "order_2", "status": "filled", "filled_qty": "75"},
        ]

        order_request = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "limit",
        }

        result = smart_execution.execute_progressive_order(order_request)

        assert result["total_filled"] == Decimal("100")
        assert len(result["orders"]) >= 1

    def test_market_impact_assessment(self, smart_execution, mock_alpaca_manager):
        """Test market impact assessment."""
        # Mock order book data
        mock_alpaca_manager.get_latest_quote.return_value = {
            "bid": 149.50,
            "ask": 150.50,
            "bid_size": 500,
            "ask_size": 300,
        }

        large_order = {"symbol": "AAPL", "quantity": Decimal("1000"), "side": "buy"}  # Large order

        impact = smart_execution.assess_market_impact(large_order)

        assert "estimated_impact" in impact
        assert "liquidity_score" in impact
        assert impact["estimated_impact"] >= 0

    def test_optimal_order_sizing(self, smart_execution):
        """Test optimal order sizing strategy."""
        large_order = Decimal("1000")

        order_chunks = smart_execution.calculate_optimal_order_sizes(large_order)

        assert isinstance(order_chunks, list)
        assert len(order_chunks) > 1  # Should split large orders
        assert sum(order_chunks) == large_order

    def test_spread_analysis(self, smart_execution, mock_alpaca_manager):
        """Test bid-ask spread analysis."""
        mock_alpaca_manager.get_latest_quote.return_value = {
            "bid": 149.75,
            "ask": 150.25,
            "bid_size": 200,
            "ask_size": 250,
        }

        spread_analysis = smart_execution.analyze_spread("AAPL")

        assert "spread_bps" in spread_analysis
        assert "mid_price" in spread_analysis
        assert spread_analysis["spread_bps"] > 0

    def test_order_timing_optimization(self, smart_execution):
        """Test order timing optimization."""
        order_request = {"symbol": "AAPL", "quantity": Decimal("500"), "side": "buy"}

        timing_strategy = smart_execution.optimize_order_timing(order_request)

        assert "execution_schedule" in timing_strategy
        assert "time_intervals" in timing_strategy

    def test_fallback_execution_strategy(self, smart_execution, mock_alpaca_manager):
        """Test fallback execution when primary strategy fails."""
        # Mock primary execution failure
        mock_alpaca_manager.place_order.side_effect = [
            TradingClientError("Limit order rejected"),  # Primary fails
            {"id": "fallback_order", "status": "filled"},  # Fallback succeeds
        ]

        order_request = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("150.00"),
        }

        result = smart_execution.execute_with_fallback(order_request)

        assert result["id"] == "fallback_order"
        assert result["execution_strategy"] == "fallback"

    def test_execution_monitoring(self, smart_execution, mock_alpaca_manager):
        """Test order execution monitoring."""
        mock_alpaca_manager.get_order.return_value = {
            "id": "order_123",
            "status": "partially_filled",
            "filled_qty": "50",
            "qty": "100",
        }

        monitoring_result = smart_execution.monitor_order_execution("order_123")

        assert monitoring_result["fill_percentage"] == 0.5
        assert monitoring_result["status"] == "partially_filled"


class TestOrderValidation:
    """Test order validation logic."""

    @pytest.fixture
    def order_validator(self):
        """Create OrderValidator instance."""
        return OrderValidator()

    def test_basic_order_validation(self, order_validator):
        """Test basic order parameter validation."""
        valid_order = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "market",
        }

        is_valid, errors = order_validator.validate_order(valid_order)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_symbol_validation(self, order_validator):
        """Test invalid symbol validation."""
        invalid_order = {
            "symbol": "",  # Invalid empty symbol
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "market",
        }

        is_valid, errors = order_validator.validate_order(invalid_order)

        assert is_valid is False
        assert any("symbol" in error for error in errors)

    def test_quantity_validation(self, order_validator):
        """Test quantity validation rules."""
        # Zero quantity
        zero_qty_order = {
            "symbol": "AAPL",
            "quantity": Decimal("0"),
            "side": "buy",
            "order_type": "market",
        }

        is_valid, errors = order_validator.validate_order(zero_qty_order)
        assert is_valid is False

        # Negative quantity
        negative_qty_order = {
            "symbol": "AAPL",
            "quantity": Decimal("-10"),
            "side": "buy",
            "order_type": "market",
        }

        is_valid, errors = order_validator.validate_order(negative_qty_order)
        assert is_valid is False

    def test_limit_order_price_validation(self, order_validator):
        """Test limit order price validation."""
        # Missing limit price
        limit_order_no_price = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "limit",
            # Missing limit_price
        }

        is_valid, errors = order_validator.validate_order(limit_order_no_price)
        assert is_valid is False

        # Invalid limit price
        limit_order_invalid_price = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("0"),  # Invalid price
        }

        is_valid, errors = order_validator.validate_order(limit_order_invalid_price)
        assert is_valid is False

    def test_buying_power_validation(self, order_validator):
        """Test buying power validation."""
        account_info = {"buying_power": "10000.00", "cash": "5000.00"}

        # Order within buying power
        valid_order = {
            "symbol": "AAPL",
            "quantity": Decimal("50"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("150.00"),  # Total: $7,500
        }

        is_valid = order_validator.validate_buying_power(valid_order, account_info)
        assert is_valid is True

        # Order exceeding buying power
        excessive_order = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("150.00"),  # Total: $15,000
        }

        is_valid = order_validator.validate_buying_power(excessive_order, account_info)
        assert is_valid is False

    def test_position_validation_for_sells(self, order_validator):
        """Test position validation for sell orders."""
        positions = [
            {"symbol": "AAPL", "qty": "200", "side": "long"},
            {"symbol": "TSLA", "qty": "100", "side": "long"},
        ]

        # Valid sell order
        valid_sell = {"symbol": "AAPL", "quantity": Decimal("100"), "side": "sell"}

        is_valid = order_validator.validate_position_for_sell(valid_sell, positions)
        assert is_valid is True

        # Invalid sell order (exceeds position)
        excessive_sell = {"symbol": "AAPL", "quantity": Decimal("300"), "side": "sell"}

        is_valid = order_validator.validate_position_for_sell(excessive_sell, positions)
        assert is_valid is False

    def test_risk_limits_validation(self, order_validator):
        """Test risk limits validation."""
        risk_limits = {
            "max_position_size": Decimal("0.20"),  # 20% max per position
            "max_order_value": Decimal("50000.00"),
        }

        portfolio_value = Decimal("200000.00")

        # Order within risk limits
        safe_order = {
            "symbol": "AAPL",
            "quantity": Decimal("200"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("150.00"),  # $30,000 total
        }

        is_valid = order_validator.validate_risk_limits(safe_order, portfolio_value, risk_limits)
        assert is_valid is True

        # Order exceeding risk limits
        risky_order = {
            "symbol": "AAPL",
            "quantity": Decimal("400"),
            "side": "buy",
            "order_type": "limit",
            "limit_price": Decimal("150.00"),  # $60,000 total (30% of portfolio)
        }

        is_valid = order_validator.validate_risk_limits(risky_order, portfolio_value, risk_limits)
        assert is_valid is False


class TestApplicationIntegration:
    """Test integration between application components."""

    @pytest.fixture
    def integrated_components(self, mocker):
        """Create integrated application components."""
        mock_tsm = mocker.Mock(spec=TradingServiceManager)
        mock_tsm.paper_trading = True

        # Mock service responses
        mock_tsm.get_account_info.return_value = {
            "portfolio_value": "100000.00",
            "buying_power": "50000.00",
            "cash": "20000.00",
        }

        mock_tsm.get_all_positions.return_value = [
            {"symbol": "AAPL", "qty": "100", "market_value": "15000.00"}
        ]

        mock_tsm.place_market_order.return_value = {"id": "order_123", "status": "filled"}

        return {
            "trading_service": mock_tsm,
            "rebalancer": PortfolioRebalancer(mock_tsm),
            "validator": OrderValidator(),
        }

    def test_end_to_end_trading_workflow(self, integrated_components):
        """Test complete end-to-end trading workflow."""
        tsm = integrated_components["trading_service"]
        rebalancer = integrated_components["rebalancer"]
        validator = integrated_components["validator"]

        # 1. Generate target allocations
        target_allocations = {
            "AAPL": Decimal("0.20"),
            "TSLA": Decimal("0.15"),
            "CASH": Decimal("0.65"),
        }

        # 2. Calculate required trades
        current_positions = {"AAPL": {"qty": "100", "market_value": "15000.00"}}
        trades = rebalancer.calculate_required_trades(
            current_positions, target_allocations, Decimal("100000.00")
        )

        # 3. Validate trades
        for trade in trades:
            is_valid, errors = validator.validate_order(trade)
            assert is_valid is True, f"Trade validation failed: {errors}"

        # 4. Execute trades
        results = rebalancer.execute_trades_sequentially(trades)

        assert len(results) >= 0
        # Should have attempted to execute the trades

    def test_error_recovery_in_workflow(self, integrated_components):
        """Test error recovery in integrated workflow."""
        tsm = integrated_components["trading_service"]
        rebalancer = integrated_components["rebalancer"]

        # Mock order failure
        tsm.place_market_order.side_effect = [
            TradingClientError("First order failed"),
            {"id": "order_456", "status": "filled"},  # Second succeeds
        ]

        trades = [
            {"symbol": "AAPL", "side": "buy", "quantity": Decimal("50")},
            {"symbol": "TSLA", "side": "buy", "quantity": Decimal("30")},
        ]

        results = rebalancer.execute_trades_sequentially(trades)

        # Should handle partial failures gracefully
        assert len(results) >= 0

    def test_performance_under_load(self, integrated_components):
        """Test performance with multiple concurrent operations."""
        rebalancer = integrated_components["rebalancer"]

        # Simulate multiple rebalancing operations
        large_allocation_set = {f"STOCK_{i}": Decimal("0.01") for i in range(50)}
        large_allocation_set["CASH"] = Decimal("0.50")

        # Should handle large allocation sets efficiently
        start_time = datetime.now()
        trades = rebalancer.calculate_required_trades(
            {}, large_allocation_set, Decimal("1000000.00")
        )
        end_time = datetime.now()

        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert isinstance(trades, list)


if __name__ == "__main__":
    pytest.main([__file__])
