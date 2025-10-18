"""Business Unit: shared | Status: current

Test comprehensive trading scenarios and business logic.

Tests real-world trading scenarios to validate business logic works correctly
for actual trading situations without requiring external broker connections.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestTradingScenarios:
    """Test comprehensive trading scenarios."""

    def test_new_account_first_trade_scenario(self):
        """Test business logic for new account's first trade."""
        # Starting with $10,000 cash, no positions
        initial_cash = Decimal("10000.00")

        # Strategy recommends diversified allocation
        allocation = StrategyAllocation(
            target_weights={
                "VTI": Decimal("0.4"),  # Total stock market
                "VXUS": Decimal("0.3"),  # International stocks
                "BND": Decimal("0.2"),  # Bonds
                "VNQ": Decimal("0.1"),  # REITs
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "balanced_portfolio"},
        )

        # Calculate target amounts
        target_amounts = {}
        for symbol, weight in allocation.target_weights.items():
            target_amounts[symbol] = initial_cash * weight

        # Business logic validation
        assert target_amounts["VTI"] == Decimal("4000.00")
        assert target_amounts["VXUS"] == Decimal("3000.00")
        assert target_amounts["BND"] == Decimal("2000.00")
        assert target_amounts["VNQ"] == Decimal("1000.00")

        # Total should equal initial cash
        total_invested = sum(target_amounts.values())
        assert total_invested == initial_cash

    def test_rebalancing_drift_scenario(self):
        """Test business logic for rebalancing when positions drift."""
        # Portfolio has drifted from target allocation
        current_portfolio_value = Decimal("15000.00")  # Grown from $10K

        current_positions = {
            "VTI": Decimal("7500.00"),  # 50% (target: 40%)
            "VXUS": Decimal("3000.00"),  # 20% (target: 30%)
            "BND": Decimal("3000.00"),  # 20% (target: 20%)
            "VNQ": Decimal("1500.00"),  # 10% (target: 10%)
        }

        # Target allocation
        target_allocation = StrategyAllocation(
            target_weights={
                "VTI": Decimal("0.4"),
                "VXUS": Decimal("0.3"),
                "BND": Decimal("0.2"),
                "VNQ": Decimal("0.1"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Calculate rebalancing needs
        rebalancing_trades = {}
        for symbol, target_weight in target_allocation.target_weights.items():
            target_value = current_portfolio_value * target_weight
            current_value = current_positions[symbol]
            trade_amount = target_value - current_value
            rebalancing_trades[symbol] = trade_amount

        # Business logic validation
        assert rebalancing_trades["VTI"] == Decimal("-1500.00")  # Sell $1,500
        assert rebalancing_trades["VXUS"] == Decimal("1500.00")  # Buy $1,500
        assert rebalancing_trades["BND"] == Decimal("0.00")  # No change
        assert rebalancing_trades["VNQ"] == Decimal("0.00")  # No change

        # Net trades should sum to zero (no cash added/removed)
        net_trades = sum(rebalancing_trades.values())
        assert net_trades == Decimal("0.00")

    def test_sector_rotation_scenario(self):
        """Test business logic for sector rotation strategy."""
        # Current tech-heavy allocation
        current_allocation = {
            "AAPL": Decimal("0.3"),
            "MSFT": Decimal("0.2"),
            "GOOGL": Decimal("0.2"),
            "AMZN": Decimal("0.1"),
            "TSLA": Decimal("0.1"),
            "NVDA": Decimal("0.1"),
        }

        # New strategy rotates to value/defensive
        new_allocation = StrategyAllocation(
            target_weights={
                "JPM": Decimal("0.2"),  # Finance
                "JNJ": Decimal("0.2"),  # Healthcare
                "PG": Decimal("0.15"),  # Consumer defensive
                "KO": Decimal("0.15"),  # Consumer defensive
                "WMT": Decimal("0.15"),  # Consumer defensive
                "XOM": Decimal("0.15"),  # Energy
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "defensive_rotation"},
        )

        # Complete sector rotation (sell all tech, buy defensive)
        portfolio_value = Decimal("50000.00")

        # Calculate trades needed
        exit_trades = {}  # Sell current positions
        for symbol, weight in current_allocation.items():
            exit_trades[symbol] = -(portfolio_value * weight)  # Negative = sell

        entry_trades = {}  # Buy new positions
        for symbol, weight in new_allocation.target_weights.items():
            entry_trades[symbol] = portfolio_value * weight  # Positive = buy

        # Business validation
        total_exit_value = sum(abs(amount) for amount in exit_trades.values())
        total_entry_value = sum(entry_trades.values())

        assert total_exit_value == portfolio_value
        assert total_entry_value == portfolio_value
        assert abs(total_exit_value - total_entry_value) < Decimal("0.01")

    def test_cash_injection_scenario(self):
        """Test business logic when cash is added to account."""
        # Existing portfolio
        existing_portfolio_value = Decimal("25000.00")
        existing_allocation = {
            "VTI": Decimal("0.6"),
            "VXUS": Decimal("0.4"),
        }

        # Cash injection
        cash_injection = Decimal("10000.00")
        new_total_value = existing_portfolio_value + cash_injection

        # Strategy maintains same allocation percentages
        target_allocation = StrategyAllocation(
            target_weights=existing_allocation,
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Calculate how to invest new cash while maintaining allocation
        current_positions = {
            "VTI": existing_portfolio_value * existing_allocation["VTI"],
            "VXUS": existing_portfolio_value * existing_allocation["VXUS"],
        }

        target_positions = {}
        trades_needed = {}

        for symbol, weight in target_allocation.target_weights.items():
            target_positions[symbol] = new_total_value * weight
            trades_needed[symbol] = target_positions[symbol] - current_positions[symbol]

        # Business validation
        assert trades_needed["VTI"] == Decimal("6000.00")  # Buy $6K more VTI
        assert trades_needed["VXUS"] == Decimal("4000.00")  # Buy $4K more VXUS

        # Total new purchases should equal cash injection
        total_purchases = sum(trades_needed.values())
        assert total_purchases == cash_injection

    def test_tax_loss_harvesting_scenario(self):
        """Test business logic for tax loss harvesting."""
        portfolio_value = Decimal("100000.00")

        # Some positions have losses, others have gains
        positions_with_pnl = {
            "AAPL": {
                "value": Decimal("20000.00"),
                "unrealized_pnl": Decimal("5000.00"),
            },  # Gain
            "MSFT": {
                "value": Decimal("15000.00"),
                "unrealized_pnl": Decimal("-2000.00"),
            },  # Loss
            "GOOGL": {
                "value": Decimal("18000.00"),
                "unrealized_pnl": Decimal("3000.00"),
            },  # Gain
            "AMZN": {
                "value": Decimal("12000.00"),
                "unrealized_pnl": Decimal("-3000.00"),
            },  # Loss
            "TSLA": {
                "value": Decimal("10000.00"),
                "unrealized_pnl": Decimal("-5000.00"),
            },  # Loss
            "Cash": {"value": Decimal("25000.00"), "unrealized_pnl": Decimal("0.00")},
        }

        # Tax loss harvesting strategy: realize losses, maintain similar exposure
        tax_loss_threshold = Decimal("-1000.00")  # Harvest losses > $1K

        losses_to_harvest = {}
        for symbol, data in positions_with_pnl.items():
            if data["unrealized_pnl"] <= tax_loss_threshold:
                losses_to_harvest[symbol] = data["unrealized_pnl"]

        # Business validation
        assert "MSFT" in losses_to_harvest
        assert "AMZN" in losses_to_harvest
        assert "TSLA" in losses_to_harvest
        assert "AAPL" not in losses_to_harvest  # Has gains

        total_losses_harvested = sum(losses_to_harvest.values())
        assert total_losses_harvested == Decimal("-10000.00")  # $10K in losses

    def test_market_volatility_response_scenario(self):
        """Test business logic response to market volatility."""
        # Market drops 20%, portfolio reacts
        pre_drop_value = Decimal("100000.00")
        post_drop_value = Decimal("80000.00")  # 20% decline

        # Volatility-adjusted allocation (more defensive)
        high_vol_allocation = StrategyAllocation(
            target_weights={
                "VTI": Decimal("0.3"),  # Reduce equity from 60% to 30%
                "BND": Decimal("0.4"),  # Increase bonds from 20% to 40%
                "VMOT": Decimal("0.2"),  # Add treasury bills
                "CASH": Decimal("0.1"),  # Hold more cash
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"volatility_regime": "high"},
        )

        # Calculate defensive positioning
        defensive_targets = {}
        for symbol, weight in high_vol_allocation.target_weights.items():
            defensive_targets[symbol] = post_drop_value * weight

        # Business validation - more conservative allocation
        equity_allocation = defensive_targets["VTI"] / post_drop_value
        bond_allocation = defensive_targets["BND"] / post_drop_value
        cash_allocation = (defensive_targets["VMOT"] + defensive_targets["CASH"]) / post_drop_value

        assert equity_allocation == Decimal("0.3")  # 30% equity
        assert bond_allocation == Decimal("0.4")  # 40% bonds
        assert cash_allocation == Decimal("0.3")  # 30% cash/short-term

    def test_position_sizing_limits_scenario(self):
        """Test business logic for position sizing limits."""
        portfolio_value = Decimal("500000.00")  # Large portfolio

        # Strategy wants concentrated positions
        concentrated_strategy = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.5"),  # 50% in one stock
                "MSFT": Decimal("0.3"),  # 30% in another
                "GOOGL": Decimal("0.2"),  # 20% in third
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"max_single_position": 0.25},  # 25% limit
        )

        # Apply position size limits
        max_position_size = Decimal("0.25")
        risk_adjusted_weights = {}

        for symbol, weight in concentrated_strategy.target_weights.items():
            if weight > max_position_size:
                risk_adjusted_weights[symbol] = max_position_size
            else:
                risk_adjusted_weights[symbol] = weight

        # Redistribute excess weight
        total_capped_weight = sum(risk_adjusted_weights.values())
        excess_weight = Decimal("1.0") - total_capped_weight

        # Business validation
        assert risk_adjusted_weights["AAPL"] == Decimal("0.25")  # Capped
        assert risk_adjusted_weights["MSFT"] == Decimal("0.25")  # Capped
        assert risk_adjusted_weights["GOOGL"] == Decimal("0.2")  # Unchanged
        assert excess_weight == Decimal("0.3")  # 30% excess to redistribute

    def test_fractional_shares_scenario(self):
        """Test business logic for fractional share handling."""
        small_portfolio_value = Decimal("1000.00")
        high_price_stock = Decimal("3000.00")  # e.g., BRK.A

        # Strategy wants exposure to expensive stock
        allocation = StrategyAllocation(
            target_weights={
                "BRK.A": Decimal("0.3"),  # Want $300 of BRK.A
                "VTI": Decimal("0.7"),  # Rest in index fund
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Calculate share quantities
        target_value_brk = small_portfolio_value * allocation.target_weights["BRK.A"]
        target_shares_brk = target_value_brk / high_price_stock

        # Business validation
        assert target_value_brk == Decimal("300.00")
        assert target_shares_brk == Decimal("0.1")  # 0.1 shares = fractional

        # Fractional shares enable small portfolio diversification
        assert target_shares_brk < Decimal("1.0")
        assert target_shares_brk > Decimal("0.0")

    def test_dividend_reinvestment_scenario(self):
        """Test business logic for dividend reinvestment."""
        # Receive dividends
        dividend_payments = {
            "AAPL": Decimal("150.00"),
            "MSFT": Decimal("120.00"),
            "JNJ": Decimal("80.00"),
        }

        total_dividends = sum(dividend_payments.values())
        assert total_dividends == Decimal("350.00")

        # Current allocation
        current_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.4"),
                "MSFT": Decimal("0.3"),
                "JNJ": Decimal("0.2"),
                "Cash": Decimal("0.1"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Reinvest dividends proportionally
        reinvestment_allocation = {}
        for symbol, weight in current_allocation.target_weights.items():
            if symbol != "CASH":  # Don't reinvest into cash
                reinvestment_allocation[symbol] = total_dividends * weight

        # Business validation
        total_reinvested = sum(reinvestment_allocation.values())
        expected_reinvested = total_dividends * Decimal("0.9")  # 90% (excluding cash weight)

        assert abs(total_reinvested - expected_reinvested) < Decimal("0.01")
        assert reinvestment_allocation["AAPL"] == Decimal("140.00")
        assert reinvestment_allocation["MSFT"] == Decimal("105.00")
        assert reinvestment_allocation["JNJ"] == Decimal("70.00")
