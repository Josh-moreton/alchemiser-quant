"""
Comprehensive unit tests for domain models.

Tests all domain models with complete validation, edge cases, and error conditions.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from the_alchemiser.domain.models.account import AccountInfo, PortfolioInfo, BuyingPower
from the_alchemiser.domain.models.order import (
    OrderRequest,
    OrderInfo,
    OrderStatus,
    OrderType,
    OrderSide,
    TimeInForce,
)
from the_alchemiser.domain.models.position import PositionInfo, PositionSide
from the_alchemiser.domain.models.market_data import Quote, Bar, Trade, MarketDataType, PriceData
from the_alchemiser.domain.models.strategy import (
    StrategySignal,
    StrategyAllocation,
    PortfolioTarget,
)


class TestAccountModels:
    """Test account-related domain models."""

    def test_account_info_creation(self):
        """Test AccountInfo model creation and validation."""
        account = AccountInfo(
            account_id="test_account_123",
            buying_power=Decimal("50000.00"),
            cash=Decimal("10000.00"),
            portfolio_value=Decimal("100000.00"),
            equity=Decimal("90000.00"),
            currency="USD",
        )

        assert account.account_id == "test_account_123"
        assert account.buying_power == Decimal("50000.00")
        assert account.cash == Decimal("10000.00")
        assert account.portfolio_value == Decimal("100000.00")
        assert account.equity == Decimal("90000.00")
        assert account.currency == "USD"

    def test_account_info_validation(self):
        """Test AccountInfo validation rules."""
        # Negative buying power should be allowed (margin accounts)
        account = AccountInfo(
            account_id="test",
            buying_power=Decimal("-1000.00"),
            cash=Decimal("0.00"),
            portfolio_value=Decimal("0.00"),
            equity=Decimal("0.00"),
        )
        assert account.buying_power == Decimal("-1000.00")

    def test_portfolio_info_creation(self):
        """Test PortfolioInfo model creation."""
        portfolio = PortfolioInfo(
            total_value=Decimal("100000.00"),
            cash=Decimal("10000.00"),
            long_market_value=Decimal("85000.00"),
            short_market_value=Decimal("5000.00"),
            unrealized_pnl=Decimal("2500.00"),
            realized_pnl=Decimal("1500.00"),
        )

        assert portfolio.total_value == Decimal("100000.00")
        assert portfolio.unrealized_pnl == Decimal("2500.00")
        assert portfolio.realized_pnl == Decimal("1500.00")

    def test_buying_power_calculations(self):
        """Test BuyingPower model calculations."""
        buying_power = BuyingPower(
            day_trading_buying_power=Decimal("100000.00"),
            overnight_buying_power=Decimal("50000.00"),
            reg_t_buying_power=Decimal("50000.00"),
            cash=Decimal("25000.00"),
        )

        assert buying_power.day_trading_buying_power == Decimal("100000.00")
        assert buying_power.overnight_buying_power == Decimal("50000.00")
        assert buying_power.effective_buying_power() == Decimal("50000.00")

    def test_buying_power_edge_cases(self):
        """Test BuyingPower edge cases."""
        # Zero buying power
        bp_zero = BuyingPower(
            day_trading_buying_power=Decimal("0.00"),
            overnight_buying_power=Decimal("0.00"),
            reg_t_buying_power=Decimal("0.00"),
            cash=Decimal("0.00"),
        )
        assert bp_zero.effective_buying_power() == Decimal("0.00")

        # Negative buying power (margin call scenario)
        bp_negative = BuyingPower(
            day_trading_buying_power=Decimal("-5000.00"),
            overnight_buying_power=Decimal("-2500.00"),
            reg_t_buying_power=Decimal("-2500.00"),
            cash=Decimal("1000.00"),
        )
        assert bp_negative.effective_buying_power() == Decimal("-2500.00")


class TestOrderModels:
    """Test order-related domain models."""

    def test_order_request_creation(self):
        """Test OrderRequest model creation."""
        order = OrderRequest(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        assert order.symbol == "AAPL"
        assert order.quantity == Decimal("100")
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.time_in_force == TimeInForce.DAY

    def test_order_request_with_limit_price(self):
        """Test OrderRequest with limit price."""
        order = OrderRequest(
            symbol="TSLA",
            quantity=Decimal("50"),
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            limit_price=Decimal("250.50"),
        )

        assert order.limit_price == Decimal("250.50")
        assert order.order_type == OrderType.LIMIT

    def test_order_request_fractional(self):
        """Test OrderRequest with fractional shares."""
        order = OrderRequest(
            symbol="NVDA",
            quantity=Decimal("0.5"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        assert order.quantity == Decimal("0.5")
        assert order.is_fractional() == True

    def test_order_info_status_transitions(self):
        """Test OrderInfo status transitions."""
        order = OrderInfo(
            order_id="order_123",
            symbol="SPY",
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=OrderStatus.NEW,
            submitted_at=datetime.now(timezone.utc),
        )

        assert order.status == OrderStatus.NEW
        assert order.is_active() == True

        # Test status transitions
        filled_order = order.model_copy(update={"status": OrderStatus.FILLED})
        assert filled_order.is_active() == False
        assert filled_order.is_filled() == True

    def test_order_validation_edge_cases(self):
        """Test order validation edge cases."""
        # Zero quantity should be invalid
        with pytest.raises(ValueError):
            OrderRequest(
                symbol="AAPL",
                quantity=Decimal("0"),
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

        # Negative quantity should be invalid
        with pytest.raises(ValueError):
            OrderRequest(
                symbol="AAPL",
                quantity=Decimal("-10"),
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

    def test_order_calculations(self):
        """Test order value calculations."""
        order = OrderRequest(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=Decimal("150.00"),
        )

        assert order.notional_value() == Decimal("15000.00")

        # Market order should not have notional value without price
        market_order = OrderRequest(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        assert market_order.notional_value() is None


class TestPositionModels:
    """Test position-related domain models."""

    def test_position_info_creation(self):
        """Test PositionInfo model creation."""
        position = PositionInfo(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=PositionSide.LONG,
            market_value=Decimal("15000.00"),
            avg_entry_price=Decimal("145.00"),
            unrealized_pnl=Decimal("500.00"),
            cost_basis=Decimal("14500.00"),
        )

        assert position.symbol == "AAPL"
        assert position.quantity == Decimal("100")
        assert position.side == PositionSide.LONG
        assert position.market_value == Decimal("15000.00")
        assert position.unrealized_pnl == Decimal("500.00")

    def test_position_calculations(self):
        """Test position calculations."""
        position = PositionInfo(
            symbol="TSLA",
            quantity=Decimal("50"),
            side=PositionSide.LONG,
            market_value=Decimal("12500.00"),
            avg_entry_price=Decimal("240.00"),
            unrealized_pnl=Decimal("500.00"),
            cost_basis=Decimal("12000.00"),
        )

        # Current price calculation
        current_price = position.current_price()
        assert current_price == Decimal("250.00")  # 12500 / 50

        # P&L percentage
        pnl_pct = position.pnl_percentage()
        assert pnl_pct == pytest.approx(4.17, rel=1e-2)  # 500/12000 * 100

    def test_position_short_side(self):
        """Test short position handling."""
        short_position = PositionInfo(
            symbol="SQQQ",
            quantity=Decimal("-100"),
            side=PositionSide.SHORT,
            market_value=Decimal("-5000.00"),
            avg_entry_price=Decimal("52.00"),
            unrealized_pnl=Decimal("200.00"),
            cost_basis=Decimal("5200.00"),
        )

        assert short_position.side == PositionSide.SHORT
        assert short_position.quantity == Decimal("-100")
        assert short_position.is_short() == True
        assert short_position.current_price() == Decimal("50.00")

    def test_position_edge_cases(self):
        """Test position edge cases."""
        # Zero position
        zero_position = PositionInfo(
            symbol="CASH",
            quantity=Decimal("0"),
            side=PositionSide.FLAT,
            market_value=Decimal("0.00"),
            avg_entry_price=Decimal("1.00"),
            unrealized_pnl=Decimal("0.00"),
            cost_basis=Decimal("0.00"),
        )

        assert zero_position.is_flat() == True
        assert zero_position.current_price() == Decimal("1.00")  # Should handle division by zero


class TestMarketDataModels:
    """Test market data domain models."""

    def test_quote_creation(self):
        """Test Quote model creation."""
        quote = Quote(
            symbol="AAPL",
            bid=Decimal("149.95"),
            ask=Decimal("150.05"),
            bid_size=100,
            ask_size=200,
            timestamp=datetime.now(timezone.utc),
        )

        assert quote.symbol == "AAPL"
        assert quote.bid == Decimal("149.95")
        assert quote.ask == Decimal("150.05")
        assert quote.spread() == Decimal("0.10")
        assert quote.mid_price() == Decimal("150.00")

    def test_quote_calculations(self):
        """Test quote calculation methods."""
        quote = Quote(
            symbol="TSLA",
            bid=Decimal("248.50"),
            ask=Decimal("249.50"),
            bid_size=50,
            ask_size=75,
            timestamp=datetime.now(timezone.utc),
        )

        # Spread calculations
        assert quote.spread() == Decimal("1.00")
        assert quote.spread_bps() == pytest.approx(40.16, rel=1e-2)  # 1.00/249.00 * 10000

        # Price calculations
        assert quote.mid_price() == Decimal("249.00")
        assert quote.weighted_mid_price() == pytest.approx(Decimal("249.20"), rel=1e-2)

    def test_bar_creation(self):
        """Test Bar model creation."""
        bar = Bar(
            symbol="SPY",
            open=Decimal("420.00"),
            high=Decimal("422.50"),
            low=Decimal("419.75"),
            close=Decimal("421.25"),
            volume=1000000,
            timestamp=datetime.now(timezone.utc),
            timeframe="1Day",
        )

        assert bar.symbol == "SPY"
        assert bar.open == Decimal("420.00")
        assert bar.high == Decimal("422.50")
        assert bar.low == Decimal("419.75")
        assert bar.close == Decimal("421.25")
        assert bar.volume == 1000000

    def test_bar_calculations(self):
        """Test bar calculation methods."""
        bar = Bar(
            symbol="QQQ",
            open=Decimal("350.00"),
            high=Decimal("355.00"),
            low=Decimal("348.00"),
            close=Decimal("352.00"),
            volume=500000,
            timestamp=datetime.now(timezone.utc),
            timeframe="1Hour",
        )

        # OHLC calculations
        assert bar.typical_price() == Decimal("351.67")  # (H+L+C)/3
        assert bar.range_pct() == pytest.approx(2.00, rel=1e-2)  # (H-L)/O * 100
        assert bar.body_pct() == pytest.approx(0.57, rel=1e-2)  # |C-O|/O * 100

    def test_trade_creation(self):
        """Test Trade model creation."""
        trade = Trade(
            symbol="NVDA",
            price=Decimal("450.75"),
            size=100,
            timestamp=datetime.now(timezone.utc),
            conditions=["@", "T"],
        )

        assert trade.symbol == "NVDA"
        assert trade.price == Decimal("450.75")
        assert trade.size == 100
        assert trade.notional_value() == Decimal("45075.00")

    def test_price_data_aggregation(self):
        """Test PriceData aggregation methods."""
        price_data = PriceData(
            symbol="AMZN",
            current_price=Decimal("135.50"),
            quote=Quote(
                symbol="AMZN",
                bid=Decimal("135.45"),
                ask=Decimal("135.55"),
                bid_size=100,
                ask_size=150,
                timestamp=datetime.now(timezone.utc),
            ),
            last_trade=Trade(
                symbol="AMZN",
                price=Decimal("135.50"),
                size=200,
                timestamp=datetime.now(timezone.utc),
            ),
            data_type=MarketDataType.REAL_TIME,
        )

        assert price_data.current_price == Decimal("135.50")
        assert price_data.quote.mid_price() == Decimal("135.50")
        assert price_data.is_real_time() == True
        assert price_data.is_stale() == False  # Just created


class TestStrategyModels:
    """Test strategy-related domain models."""

    def test_strategy_signal_creation(self):
        """Test StrategySignal model creation."""
        signal = StrategySignal(
            symbol="AAPL",
            signal="BUY",
            confidence=0.85,
            target_allocation=0.10,
            reasoning="Strong technical indicators",
            strategy_name="Nuclear",
            timestamp=datetime.now(timezone.utc),
        )

        assert signal.symbol == "AAPL"
        assert signal.signal == "BUY"
        assert signal.confidence == 0.85
        assert signal.target_allocation == 0.10
        assert signal.strategy_name == "Nuclear"

    def test_strategy_signal_validation(self):
        """Test StrategySignal validation rules."""
        # Confidence should be between 0 and 1
        with pytest.raises(ValueError):
            StrategySignal(
                symbol="AAPL",
                signal="BUY",
                confidence=1.5,  # Invalid
                target_allocation=0.10,
                strategy_name="Test",
            )

        # Target allocation should be between 0 and 1
        with pytest.raises(ValueError):
            StrategySignal(
                symbol="AAPL",
                signal="BUY",
                confidence=0.80,
                target_allocation=1.5,  # Invalid
                strategy_name="Test",
            )

    def test_strategy_allocation_creation(self):
        """Test StrategyAllocation model creation."""
        allocation = StrategyAllocation(
            strategy_name="Nuclear",
            base_allocation=0.33,
            current_allocation=0.35,
            performance_modifier=0.02,
            risk_adjusted_allocation=0.30,
        )

        assert allocation.strategy_name == "Nuclear"
        assert allocation.base_allocation == 0.33
        assert allocation.current_allocation == 0.35
        assert allocation.performance_modifier == 0.02

    def test_portfolio_target_creation(self):
        """Test PortfolioTarget model creation."""
        targets = {"AAPL": Decimal("0.15"), "TSLA": Decimal("0.10"), "CASH": Decimal("0.75")}

        portfolio_target = PortfolioTarget(
            allocations=targets,
            total_value=Decimal("100000.00"),
            rebalance_threshold=Decimal("0.05"),
            timestamp=datetime.now(timezone.utc),
        )

        assert portfolio_target.allocations["AAPL"] == Decimal("0.15")
        assert portfolio_target.total_value == Decimal("100000.00")
        assert portfolio_target.validate_allocations() == True

    def test_portfolio_target_validation(self):
        """Test PortfolioTarget validation."""
        # Allocations should sum to 1.0
        invalid_targets = {
            "AAPL": Decimal("0.60"),
            "TSLA": Decimal("0.50"),  # Sum = 1.10, invalid
        }

        portfolio_target = PortfolioTarget(
            allocations=invalid_targets,
            total_value=Decimal("100000.00"),
            rebalance_threshold=Decimal("0.05"),
            timestamp=datetime.now(timezone.utc),
        )

        assert portfolio_target.validate_allocations() == False

    def test_portfolio_target_calculations(self):
        """Test PortfolioTarget calculation methods."""
        targets = {
            "AAPL": Decimal("0.25"),
            "TSLA": Decimal("0.15"),
            "SPY": Decimal("0.35"),
            "CASH": Decimal("0.25"),
        }

        portfolio_target = PortfolioTarget(
            allocations=targets,
            total_value=Decimal("100000.00"),
            rebalance_threshold=Decimal("0.05"),
            timestamp=datetime.now(timezone.utc),
        )

        # Dollar amounts
        assert portfolio_target.dollar_allocation("AAPL") == Decimal("25000.00")
        assert portfolio_target.dollar_allocation("TSLA") == Decimal("15000.00")

        # Concentration metrics
        assert portfolio_target.max_allocation() == Decimal("0.35")
        assert portfolio_target.concentration_risk() == 4  # Number of positions


class TestModelIntegration:
    """Test integration between different domain models."""

    def test_order_position_relationship(self):
        """Test relationship between orders and positions."""
        # Create a buy order
        buy_order = OrderRequest(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        # Create resulting position
        position = PositionInfo(
            symbol="AAPL",
            quantity=Decimal("100"),
            side=PositionSide.LONG,
            market_value=Decimal("15000.00"),
            avg_entry_price=Decimal("150.00"),
            unrealized_pnl=Decimal("0.00"),
            cost_basis=Decimal("15000.00"),
        )

        assert buy_order.symbol == position.symbol
        assert buy_order.quantity == position.quantity

    def test_quote_order_price_relationship(self):
        """Test relationship between quotes and order pricing."""
        quote = Quote(
            symbol="TSLA",
            bid=Decimal("248.50"),
            ask=Decimal("249.50"),
            bid_size=100,
            ask_size=200,
            timestamp=datetime.now(timezone.utc),
        )

        # Buy order should use ask price
        buy_order = OrderRequest(
            symbol="TSLA",
            quantity=Decimal("50"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=quote.ask,
        )

        # Sell order should use bid price
        sell_order = OrderRequest(
            symbol="TSLA",
            quantity=Decimal("50"),
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=quote.bid,
        )

        assert buy_order.limit_price == quote.ask
        assert sell_order.limit_price == quote.bid

    def test_account_buying_power_order_validation(self):
        """Test account buying power against order requirements."""
        account = AccountInfo(
            account_id="test",
            buying_power=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            portfolio_value=Decimal("50000.00"),
            equity=Decimal("45000.00"),
        )

        # Order within buying power
        valid_order = OrderRequest(
            symbol="SPY",
            quantity=Decimal("20"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=Decimal("420.00"),
        )

        order_value = valid_order.notional_value()
        assert order_value <= account.buying_power

        # Order exceeding buying power
        invalid_order = OrderRequest(
            symbol="SPY",
            quantity=Decimal("50"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            limit_price=Decimal("420.00"),
        )

        order_value = invalid_order.notional_value()
        assert order_value > account.buying_power


if __name__ == "__main__":
    pytest.main([__file__])
