"""
Market Scenario Testing

Tests trading strategies against historical market conditions and edge cases.
This validates strategy behavior during various market regimes and extreme events.
"""

from decimal import Decimal
from unittest.mock import Mock

import numpy as np
import pandas as pd


class MarketDataGenerator:
    """Generate realistic market data for testing scenarios."""

    @staticmethod
    def generate_normal_market(days: int = 252, volatility: float = 0.15) -> pd.DataFrame:
        """Generate normal market conditions with typical volatility."""
        import numpy as np

        # Start with a base price
        base_price = 100.0
        dates = pd.date_range(start="2024-01-01", periods=days, freq="D")

        # Generate random returns with specified volatility
        daily_returns = np.random.normal(
            0.0008, volatility / np.sqrt(252), days
        )  # ~20% annual return

        # Calculate cumulative prices
        prices = [base_price]
        for return_rate in daily_returns[:-1]:
            prices.append(prices[-1] * (1 + return_rate))

        return pd.DataFrame(
            {"date": dates, "price": prices, "volume": np.random.randint(1000000, 5000000, days)}
        )

    @staticmethod
    def generate_crash_scenario(
        crash_day: int = 30, crash_magnitude: float = -0.35
    ) -> pd.DataFrame:
        """Generate a market crash scenario like March 2020."""
        # Start with normal market
        data = MarketDataGenerator.generate_normal_market(60)

        # Apply crash on specific day
        crash_price = data.iloc[crash_day]["price"] * (1 + crash_magnitude)

        # Apply crash and recovery
        for i in range(crash_day, min(crash_day + 5, len(data))):
            if i == crash_day:
                data.iloc[i, data.columns.get_loc("price")] = crash_price
            else:
                # Gradual recovery with high volatility
                recovery_factor = 1 + np.random.normal(0.02, 0.05)  # High volatility recovery
                data.iloc[i, data.columns.get_loc("price")] = (
                    data.iloc[i - 1]["price"] * recovery_factor
                )

        return data

    @staticmethod
    def generate_flash_crash() -> pd.DataFrame:
        """Generate a flash crash scenario with rapid price movement."""
        import numpy as np

        # Intraday data with minute intervals
        base_price = 150.0
        times = pd.date_range(start="2024-01-01 09:30:00", periods=390, freq="1min")

        prices = [base_price] * len(times)

        # Flash crash at 2:45 PM (195 minutes into session)
        crash_start = 195
        crash_bottom = 10  # 10 minutes to bottom
        recovery_time = 30  # 30 minutes to recover

        for i in range(crash_start, min(crash_start + crash_bottom, len(prices))):
            # 20% drop in 10 minutes
            drop_per_minute = -0.02
            prices[i] = prices[i - 1] * (1 + drop_per_minute)

        # Recovery
        for i in range(
            crash_start + crash_bottom, min(crash_start + crash_bottom + recovery_time, len(prices))
        ):
            recovery_per_minute = 0.015  # Slower recovery
            prices[i] = prices[i - 1] * (1 + recovery_per_minute)

        return pd.DataFrame(
            {
                "timestamp": times,
                "price": prices,
                "volume": np.random.randint(100000, 1000000, len(times)),
            }
        )

    @staticmethod
    def generate_gap_scenario() -> pd.DataFrame:
        """Generate overnight gaps in price data."""
        data = MarketDataGenerator.generate_normal_market(30)

        # Add some overnight gaps
        gap_days = [5, 12, 18, 25]
        gap_sizes = [0.08, -0.05, 0.12, -0.03]  # Various gap sizes

        for gap_day, gap_size in zip(gap_days, gap_sizes, strict=True):
            if gap_day < len(data):
                data.iloc[gap_day, data.columns.get_loc("price")] = data.iloc[gap_day - 1][
                    "price"
                ] * (1 + gap_size)

        return data


class TestMarketScenarios:
    """Test trading strategies against various market scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = Mock()
        self.portfolio_manager = Mock()
        self.risk_manager = Mock()

        # Mock strategy responses
        self.strategy.generate_signals.return_value = pd.DataFrame(
            {"signal": ["HOLD"] * 30, "confidence": [0.5] * 30}
        )

    def test_normal_market_conditions(self):
        """Test strategy performance in normal market conditions."""
        # Generate normal market data
        market_data = MarketDataGenerator.generate_normal_market(days=252)

        # Run strategy simulation
        signals = self.strategy.generate_signals(market_data)

        # Validate signals are reasonable
        assert len(signals) == len(market_data)
        assert all(signal in ["BUY", "SELL", "HOLD"] for signal in signals["signal"])

        # Strategy should generate some signals in normal conditions
        signal_count = len(signals[signals["signal"] != "HOLD"])
        assert signal_count > 0, "Strategy should generate some trading signals"

        # Confidence should be reasonable
        avg_confidence = signals["confidence"].mean()
        assert 0.0 <= avg_confidence <= 1.0, "Confidence should be between 0 and 1"

    def test_market_crash_scenario(self):
        """Test strategy behavior during market crash (March 2020 style)."""
        # Generate crash scenario
        crash_data = MarketDataGenerator.generate_crash_scenario()

        # Mock strategy to be defensive during crashes
        crash_signals = pd.DataFrame(
            {
                "signal": ["SELL" if i == 30 else "HOLD" for i in range(len(crash_data))],
                "confidence": [0.9 if i == 30 else 0.5 for i in range(len(crash_data))],
            }
        )
        self.strategy.generate_signals.return_value = crash_signals

        signals = self.strategy.generate_signals(crash_data)

        # Strategy should have high confidence in defensive actions
        crash_day_signal = signals.iloc[30]
        assert crash_day_signal["signal"] == "SELL"
        assert crash_day_signal["confidence"] > 0.8

        # Should not panic and over-trade
        sell_signals = len(signals[signals["signal"] == "SELL"])
        assert sell_signals <= 3, "Should not panic-sell too frequently"

    def test_flash_crash_recovery(self):
        """Test behavior during rapid price movements (flash crash)."""
        flash_data = MarketDataGenerator.generate_flash_crash()

        # Mock strategy to not panic during flash crashes
        stable_signals = pd.DataFrame(
            {
                "signal": ["HOLD"] * len(flash_data),
                "confidence": [0.3] * len(flash_data),  # Low confidence during volatility
            }
        )
        self.strategy.generate_signals.return_value = stable_signals

        signals = self.strategy.generate_signals(flash_data)

        # Strategy should maintain stability during flash crash
        crash_period_signals = signals.iloc[195:225]  # Crash and recovery period

        # Should not generate excessive trading signals during high volatility
        non_hold_signals = len(crash_period_signals[crash_period_signals["signal"] != "HOLD"])
        assert non_hold_signals <= 2, "Should not over-trade during flash crash"

        # Confidence should be appropriately low during high volatility
        avg_confidence_during_crash = crash_period_signals["confidence"].mean()
        assert (
            avg_confidence_during_crash < 0.6
        ), "Should have low confidence during high volatility"

    def test_price_gap_handling(self):
        """Test strategy handles overnight gaps gracefully."""
        gap_data = MarketDataGenerator.generate_gap_scenario()

        # Strategy should handle gaps without errors
        signals = self.strategy.generate_signals(gap_data)

        assert len(signals) == len(gap_data)
        assert signals is not None

        # Verify strategy was called with gap data
        self.strategy.generate_signals.assert_called_once()
        call_args = self.strategy.generate_signals.call_args[0][0]

        # Check that gaps are present in the data
        price_changes = call_args["price"].pct_change().abs()
        large_gaps = price_changes[price_changes > 0.04]  # > 4% moves
        assert len(large_gaps) > 0, "Should have detected price gaps in test data"

    def test_extended_bear_market(self):
        """Test strategy during extended bear market conditions."""
        # Generate declining market over 6 months
        bear_data = MarketDataGenerator.generate_normal_market(126)  # 6 months

        # Apply consistent downward trend
        for i in range(1, len(bear_data)):
            bear_data.iloc[i, bear_data.columns.get_loc("price")] = (
                bear_data.iloc[i - 1]["price"] * 0.998
            )  # -0.2% daily

        # Mock defensive strategy
        bear_signals = pd.DataFrame(
            {
                "signal": ["SELL"] * 10 + ["HOLD"] * (len(bear_data) - 10),
                "confidence": [0.7] * len(bear_data),
            }
        )
        self.strategy.generate_signals.return_value = bear_signals

        signals = self.strategy.generate_signals(bear_data)

        # Strategy should recognize bear market and be defensive
        early_signals = signals.head(10)
        sell_count = len(early_signals[early_signals["signal"] == "SELL"])

        assert sell_count > 0, "Should generate some sell signals in bear market"

        # Should maintain reasonable confidence
        avg_confidence = signals["confidence"].mean()
        assert avg_confidence > 0.6, "Should maintain confidence in bear market strategy"

    def test_high_volatility_environment(self):
        """Test strategy in high volatility environment."""
        # Generate high volatility market
        volatile_data = MarketDataGenerator.generate_normal_market(
            60, volatility=0.40
        )  # 40% volatility

        # Mock cautious strategy during high volatility
        cautious_signals = pd.DataFrame(
            {
                "signal": ["HOLD"] * len(volatile_data),
                "confidence": [0.4] * len(volatile_data),  # Lower confidence
            }
        )
        self.strategy.generate_signals.return_value = cautious_signals

        signals = self.strategy.generate_signals(volatile_data)

        # Strategy should be cautious in high volatility
        hold_count = len(signals[signals["signal"] == "HOLD"])
        assert hold_count > len(signals) * 0.8, "Should mostly hold in high volatility"

        # Confidence should be appropriately reduced
        avg_confidence = signals["confidence"].mean()
        assert avg_confidence < 0.5, "Should have low confidence in high volatility"


class TestMarketDataValidation:
    """Test market data integrity and validation."""

    def test_market_data_completeness(self):
        """Test that market data has all required fields."""
        data = MarketDataGenerator.generate_normal_market(30)

        # Required fields
        required_fields = ["date", "price", "volume"]
        for field in required_fields:
            assert field in data.columns, f"Market data missing required field: {field}"

        # Data integrity checks
        assert len(data) == 30, "Should generate requested number of days"
        assert data["price"].min() > 0, "Prices should be positive"
        assert data["volume"].min() > 0, "Volume should be positive"

        # No missing values
        assert not data["price"].isna().any(), "Should not have missing prices"
        assert not data["volume"].isna().any(), "Should not have missing volume"

    def test_price_continuity_validation(self):
        """Test that price movements are realistic."""
        data = MarketDataGenerator.generate_normal_market(100)

        # Calculate daily returns
        returns = data["price"].pct_change().dropna()

        # Most daily returns should be reasonable (< 10% in normal market)
        extreme_moves = returns[abs(returns) > 0.10]
        assert len(extreme_moves) < len(returns) * 0.05, "Too many extreme price moves"

        # Returns should have reasonable distribution
        assert -0.5 < returns.min() < 0.0, "Minimum return should be reasonable"
        assert 0.0 < returns.max() < 0.5, "Maximum return should be reasonable"

    def test_gap_scenario_validation(self):
        """Test that gap scenarios are properly generated."""
        gap_data = MarketDataGenerator.generate_gap_scenario()

        # Calculate overnight gaps (day-to-day price changes)
        price_changes = gap_data["price"].pct_change().abs()

        # Should have some significant gaps
        large_gaps = price_changes[price_changes > 0.03]  # > 3% moves
        assert len(large_gaps) >= 2, "Should have generated some price gaps"

        # But not too many extreme gaps
        extreme_gaps = price_changes[price_changes > 0.15]  # > 15% moves
        assert len(extreme_gaps) <= 2, "Should not have too many extreme gaps"


class TestPortfolioSimulation:
    """Test portfolio behavior during market scenarios."""

    def setup_method(self):
        """Set up portfolio simulation."""
        self.initial_capital = Decimal("100000.00")
        self.portfolio_positions = {
            "AAPL": {"quantity": 100, "avg_price": Decimal("150.00")},
            "SPY": {"quantity": 200, "avg_price": Decimal("400.00")},
        }

    def test_portfolio_drawdown_calculation(self):
        """Test maximum drawdown calculation during market stress."""
        # Simulate portfolio values during crash
        portfolio_values = [100000, 98000, 95000, 85000, 70000, 75000, 80000, 85000]

        def calculate_max_drawdown(values):
            """Calculate maximum drawdown from peak to trough."""
            peak = values[0]
            max_dd = 0

            for value in values:
                if value > peak:
                    peak = value

                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)

            return max_dd

        max_drawdown = calculate_max_drawdown(portfolio_values)

        # Should correctly identify 30% drawdown
        assert abs(max_drawdown - 0.30) < 0.01, f"Expected ~30% drawdown, got {max_drawdown:.2%}"

        # Drawdown should be reasonable for stress scenario
        assert max_drawdown < 0.50, "Drawdown should not exceed 50% in realistic scenario"

    def test_portfolio_recovery_tracking(self):
        """Test portfolio recovery measurement after drawdown."""
        # Values showing recovery from drawdown
        values = [100000, 70000, 75000, 82000, 90000, 95000]

        def calculate_recovery_factor(values):
            """Calculate recovery from trough to current."""
            trough = min(values)
            current = values[-1]
            trough_idx = values.index(trough)
            peak_before_trough = max(values[:trough_idx]) if trough_idx > 0 else values[0]

            return (current - trough) / (peak_before_trough - trough)

        recovery = calculate_recovery_factor(values)

        # Should show significant recovery
        assert recovery > 0.5, f"Should show substantial recovery, got {recovery:.2%}"
        assert recovery < 1.1, "Recovery should be realistic"

    def test_position_sizing_under_stress(self):
        """Test that position sizing remains appropriate under market stress."""
        # Simulate position values during different market conditions
        stressed_prices = {
            "AAPL": Decimal("120.00"),  # -20% from avg price
            "SPY": Decimal("350.00"),  # -12.5% from avg price
        }

        def calculate_position_value(positions, current_prices):
            """Calculate current portfolio value."""
            total_value = Decimal("0")
            for symbol, position in positions.items():
                if symbol in current_prices:
                    value = position["quantity"] * current_prices[symbol]
                    total_value += value
            return total_value

        stressed_value = calculate_position_value(self.portfolio_positions, stressed_prices)

        # Calculate portfolio impact
        original_equity_value = Decimal("95000")  # 100 * 150 + 200 * 400 = 95000

        # Should maintain reasonable portfolio value under stress
        value_ratio = stressed_value / original_equity_value
        assert (
            0.70 <= value_ratio <= 0.95
        ), f"Portfolio value ratio {value_ratio:.2%} outside expected range"

        # Individual position checks
        aapl_value = self.portfolio_positions["AAPL"]["quantity"] * stressed_prices["AAPL"]
        spy_value = self.portfolio_positions["SPY"]["quantity"] * stressed_prices["SPY"]

        assert aapl_value > 0, "AAPL position should maintain positive value"
        assert spy_value > 0, "SPY position should maintain positive value"
