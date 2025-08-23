"""Tests for TECL strategy confidence calculation."""

from decimal import Decimal
from unittest.mock import Mock

from the_alchemiser.domain.strategies.config import TECLConfidenceConfig
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence


class TestTECLConfidenceCalculation:
    """Test TECL strategy confidence calculation methods."""

    def test_calculate_confidence_with_oversold_buy(self):
        """Test confidence calculation for oversold BUY signal."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        # Mock data provider
        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Mock indicators with oversold RSI
        indicators = {
            "TECL": {"rsi_9": 25.0, "current_price": 100.0},
            "SPY": {"current_price": 400.0, "ma_200": 390.0}
        }

        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Buy signal")

        # Should have higher confidence for oversold BUY
        assert isinstance(confidence, Confidence)
        assert confidence.value > Decimal("0.6")  # Above base confidence

    def test_calculate_confidence_with_overbought_sell(self):
        """Test confidence calculation for overbought SELL signal."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Mock indicators with overbought RSI
        indicators = {
            "TECL": {"rsi_9": 75.0, "current_price": 100.0},
            "SPY": {"current_price": 400.0, "ma_200": 390.0}
        }

        confidence = engine._calculate_confidence("TECL", "SELL", indicators, "Sell signal")

        # Should have higher confidence for overbought SELL
        assert isinstance(confidence, Confidence)
        assert confidence.value > Decimal("0.6")

    def test_calculate_confidence_defensive_position_penalty(self):
        """Test confidence penalty for defensive positions."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        indicators = {
            "BIL": {"rsi_9": 50.0, "current_price": 100.0},
            "SPY": {"current_price": 400.0, "ma_200": 390.0}
        }

        confidence = engine._calculate_confidence("BIL", "BUY", indicators, "Defensive BIL position")

        # Should have penalty for defensive position
        config = TECLConfidenceConfig()
        expected_max = config.base_confidence - config.defensive_position_penalty
        assert confidence.value <= expected_max

    def test_calculate_confidence_bull_market_bonus(self):
        """Test confidence bonus in bull market."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Bull market: price > MA200
        indicators = {
            "TECL": {"rsi_9": 50.0, "current_price": 100.0},
            "SPY": {"current_price": 420.0, "ma_200": 400.0}  # Bull market
        }

        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Bull market signal")

        # Should have bull market bonus
        config = TECLConfidenceConfig()
        expected_min = config.base_confidence + config.bull_market_bonus
        assert confidence.value >= expected_min

    def test_calculate_confidence_bear_market_penalty(self):
        """Test confidence penalty in bear market."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Bear market: price < MA200
        indicators = {
            "TECL": {"rsi_9": 50.0, "current_price": 100.0},
            "SPY": {"current_price": 380.0, "ma_200": 400.0}  # Bear market
        }

        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Bear market signal")

        # Should have bear market penalty
        config = TECLConfidenceConfig()
        expected_max = config.base_confidence - config.bear_market_penalty
        assert confidence.value <= expected_max

    def test_calculate_confidence_portfolio_allocation(self):
        """Test confidence calculation for portfolio allocation."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Portfolio allocation with TECL as highest weight
        symbol_allocation = {"TECL": 0.6, "UVXY": 0.4}
        indicators = {
            "TECL": {"rsi_9": 50.0, "current_price": 100.0},
            "UVXY": {"rsi_9": 50.0, "current_price": 20.0},
            "SPY": {"current_price": 400.0, "ma_200": 390.0}
        }

        confidence = engine._calculate_confidence(symbol_allocation, "BUY", indicators, "Portfolio signal")

        # Should calculate confidence based on primary symbol (TECL)
        assert isinstance(confidence, Confidence)
        assert Decimal("0.3") <= confidence.value <= Decimal("0.9")

    def test_confidence_bounds_enforcement(self):
        """Test that confidence is clamped to valid bounds."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Extreme indicators that might push confidence out of bounds
        indicators = {
            "TECL": {"rsi_9": 5.0, "current_price": 100.0},  # Extremely oversold
            "SPY": {"current_price": 450.0, "ma_200": 400.0}  # Strong bull market
        }

        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Extreme signal")

        # Should be within valid bounds
        config = TECLConfidenceConfig()
        assert config.min_confidence <= confidence.value <= config.max_confidence

    def test_missing_indicators_fallback(self):
        """Test graceful handling when indicators are missing."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)

        # Empty indicators
        indicators = {}

        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Signal with missing data")

        # Should fall back to base confidence
        config = TECLConfidenceConfig()
        assert confidence.value == config.base_confidence


class TestTECLRSIConfidenceAdjustment:
    """Test RSI-specific confidence adjustments."""

    def test_rsi_adjustment_for_buy_oversold(self):
        """Test RSI confidence adjustment for oversold BUY signals."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)
        config = TECLConfidenceConfig()

        # Test various oversold levels
        test_cases = [
            (25.0, "moderately_oversold"),
            (20.0, "very_oversold"),
            (15.0, "extremely_oversold"),
        ]

        for rsi_value, case_name in test_cases:
            symbol_indicators = {"rsi_9": rsi_value}
            adjustment = engine._adjust_confidence_for_rsi(
                config.base_confidence, symbol_indicators, "BUY", config
            )

            # More oversold should give higher confidence boost
            assert adjustment >= config.base_confidence, f"Failed for {case_name}"

    def test_rsi_adjustment_for_sell_overbought(self):
        """Test RSI confidence adjustment for overbought SELL signals."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)
        config = TECLConfidenceConfig()

        # Test overbought SELL signals
        symbol_indicators = {"rsi_9": 75.0}
        adjustment = engine._adjust_confidence_for_rsi(
            config.base_confidence, symbol_indicators, "SELL", config
        )

        # Overbought SELL should get confidence boost
        assert adjustment >= config.base_confidence

    def test_rsi_adjustment_neutral_range(self):
        """Test that neutral RSI doesn't affect confidence."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine

        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)
        config = TECLConfidenceConfig()

        # Neutral RSI (between oversold and overbought)
        symbol_indicators = {"rsi_9": 50.0}

        buy_adjustment = engine._adjust_confidence_for_rsi(
            config.base_confidence, symbol_indicators, "BUY", config
        )
        sell_adjustment = engine._adjust_confidence_for_rsi(
            config.base_confidence, symbol_indicators, "SELL", config
        )

        # Neutral RSI should not change confidence
        assert buy_adjustment == config.base_confidence
        assert sell_adjustment == config.base_confidence
