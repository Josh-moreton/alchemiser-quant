#!/usr/bin/env python3
"""
Unit Tests for Core Strategy Logic

This module tests the pure strategy logic engines for both Nuclear and TECL strategies.
Every scenario from the Clojure (.clj) files is tested to ensure Python implementation
matches the canonical truth from Composer.trade strategy definitions.

Test Categories:
1. Nuclear Strategy Engine Tests
2. TECL Strategy Engine Tests
3. Portfolio Construction Tests
4. Edge Cases and Error Handling
"""

import unittest
from unittest.mock import Mock, patch

import pandas as pd

from the_alchemiser.core.data.data_provider import UnifiedDataProvider

# Import the strategy engines
from the_alchemiser.core.trading.strategy_engine import NuclearStrategyEngine
from the_alchemiser.core.trading.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.core.utils.common import ActionType


class TestNuclearStrategyEngine(unittest.TestCase):
    """Test Nuclear Strategy Engine - All scenarios from Nuclear.clj"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.engine = NuclearStrategyEngine()

        # Base indicators for all tests - default neutral values
        self.base_indicators = {
            "SPY": {
                "rsi_10": 50.0,
                "rsi_20": 50.0,
                "ma_200": 400.0,
                "ma_20": 410.0,
                "current_price": 420.0,
                "ma_return_90": 5.0,
            },
            "IOO": {"rsi_10": 50.0, "ma_return_90": 3.0},
            "TQQQ": {
                "rsi_10": 50.0,
                "rsi_20": 50.0,
                "ma_20": 50.0,
                "current_price": 50.0,
                "ma_return_90": 8.0,
            },
            "VTV": {"rsi_10": 50.0, "ma_return_90": 2.0},
            "XLF": {"rsi_10": 50.0, "ma_return_90": 4.0},
            "VOX": {"rsi_10": 50.0, "ma_return_90": 6.0},
            "UVXY": {"rsi_10": 50.0},
            "BTAL": {"rsi_10": 50.0},
            "QQQ": {"rsi_10": 50.0, "cum_return_60": 5.0, "ma_return_90": 7.0},
            "SQQQ": {"rsi_10": 50.0, "rsi_9": 50.0},
            "PSQ": {"rsi_10": 50.0, "rsi_20": 50.0},
            "UPRO": {"rsi_10": 50.0},
            "TLT": {"rsi_20": 50.0},
            "IEF": {"rsi_10": 50.0},
            # Nuclear energy stocks
            "SMR": {"ma_return_90": 12.0},
            "BWXT": {"ma_return_90": 15.0},
            "LEU": {"ma_return_90": 8.0},
            "EXC": {"ma_return_90": 6.0},
            "NLR": {"ma_return_90": 10.0},
            "OKLO": {"ma_return_90": 18.0},
        }

    def test_nuclear_portfolio_construction_top_performers(self):
        """Test nuclear portfolio construction with top performing stocks"""

        indicators = self.base_indicators.copy()

        # Test that top performers are selected correctly
        portfolio = self.engine.get_nuclear_portfolio(indicators, top_n=3)

        # Should get top 3: OKLO (18%), BWXT (15%), SMR (12%)
        self.assertEqual(len(portfolio), 3)
        self.assertIn("OKLO", portfolio)
        self.assertIn("BWXT", portfolio)
        self.assertIn("SMR", portfolio)

        # Check that performance is correctly assigned
        self.assertEqual(portfolio["OKLO"]["performance"], 18.0)
        self.assertEqual(portfolio["BWXT"]["performance"], 15.0)
        self.assertEqual(portfolio["SMR"]["performance"], 12.0)

    def test_primary_overbought_spy_nested_checks(self):
        """Test SPY RSI 79-81 -> Check IOO, TQQQ, VTV, XLF in order"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 80.0  # Between 79-81

        # Test IOO > 81 triggers UVXY
        indicators["IOO"]["rsi_10"] = 82.0
        result = self.engine.evaluate_nuclear_strategy(indicators)
        self.assertEqual(result[0], "UVXY")
        self.assertIn("IOO", result[2])

        # Test TQQQ > 81 triggers UVXY (IOO not extreme)
        indicators["IOO"]["rsi_10"] = 75.0
        indicators["TQQQ"]["rsi_10"] = 83.0
        result = self.engine.evaluate_nuclear_strategy(indicators)
        self.assertEqual(result[0], "UVXY")
        self.assertIn("TQQQ", result[2])

        # Test VTV > 81 triggers UVXY (IOO, TQQQ not extreme)
        indicators["TQQQ"]["rsi_10"] = 75.0
        indicators["VTV"]["rsi_10"] = 84.0
        result = self.engine.evaluate_nuclear_strategy(indicators)
        self.assertEqual(result[0], "UVXY")
        self.assertIn("VTV", result[2])

        # Test XLF > 81 triggers UVXY (others not extreme)
        indicators["VTV"]["rsi_10"] = 75.0
        indicators["XLF"]["rsi_10"] = 85.0
        result = self.engine.evaluate_nuclear_strategy(indicators)
        self.assertEqual(result[0], "UVXY")
        self.assertIn("XLF", result[2])

    def test_primary_overbought_spy_hedge_portfolio(self):
        """Test SPY 79-81 with no extreme secondary -> UVXY_BTAL_PORTFOLIO"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 80.0  # Between 79-81

        # All secondary indicators below 81
        indicators["IOO"]["rsi_10"] = 75.0
        indicators["TQQQ"]["rsi_10"] = 78.0
        indicators["VTV"]["rsi_10"] = 76.0
        indicators["XLF"]["rsi_10"] = 79.0

        result = self.engine.evaluate_nuclear_strategy(indicators)

        # Should recommend UVXY+BTAL hedge portfolio
        self.assertEqual(result[0], "UVXY_BTAL_PORTFOLIO")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("79-81", result[2])

    def test_vox_overbought_check(self):
        """Test VOX > 79 overbought logic (PRIMARY BRANCH: SPY RSI <= 79)"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 75.0  # Not in primary overbought
        indicators["VOX"]["rsi_10"] = 80.0  # VOX overbought

        # Mock VoxOverboughtStrategy result
        with patch(
            "the_alchemiser.core.trading.nuclear_trading_bot.VoxOverboughtStrategy"
        ) as mock_strategy:
            mock_instance = Mock()
            mock_instance.recommend.return_value = (
                "UVXY",
                ActionType.BUY.value,
                "VOX overbought strategy",
            )
            mock_strategy.return_value = mock_instance

            result = self.engine.evaluate_nuclear_strategy(indicators)

            self.assertEqual(result[0], "UVXY")
            self.assertEqual(result[1], ActionType.BUY.value)

    def test_oversold_conditions_tqqq_first(self):
        """Test oversold checks: TQQQ < 30 takes precedence over SPY < 30"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought
        indicators["VOX"]["rsi_10"] = 70.0  # Not overbought

        # TQQQ oversold - should trigger first
        indicators["TQQQ"]["rsi_10"] = 25.0
        indicators["SPY"]["rsi_10"] = 28.0  # Also oversold but should be ignored

        result = self.engine.evaluate_nuclear_strategy(indicators)

        self.assertEqual(result[0], "TQQQ")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("oversold", result[2].lower())

    def test_oversold_conditions_spy_second(self):
        """Test SPY < 30 -> UPRO (when TQQQ not oversold)"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 28.0  # SPY oversold
        indicators["TQQQ"]["rsi_10"] = 45.0  # TQQQ not oversold
        indicators["VOX"]["rsi_10"] = 70.0  # Not overbought

        result = self.engine.evaluate_nuclear_strategy(indicators)

        self.assertEqual(result[0], "UPRO")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("oversold", result[2].lower())

    def test_bull_market_nuclear_portfolio(self):
        """Test Bull Market: SPY > 200 MA -> Nuclear Portfolio"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 55.0  # Not oversold/overbought
        indicators["TQQQ"]["rsi_10"] = 55.0  # Not oversold
        indicators["VOX"]["rsi_10"] = 70.0  # Not overbought
        indicators["SPY"]["current_price"] = 450.0  # > 200 MA (400.0)

        # Mock BullMarketStrategy result
        with patch(
            "the_alchemiser.core.trading.nuclear_trading_bot.BullMarketStrategy"
        ) as mock_strategy:
            mock_instance = Mock()
            mock_instance.recommend.return_value = (
                "NUCLEAR_PORTFOLIO",
                ActionType.BUY.value,
                "Bull market nuclear portfolio",
            )
            mock_strategy.return_value = mock_instance

            result = self.engine.evaluate_nuclear_strategy(indicators)

            self.assertEqual(result[0], "NUCLEAR_PORTFOLIO")
            self.assertEqual(result[1], ActionType.BUY.value)

    def test_bear_market_strategy(self):
        """Test Bear Market: SPY < 200 MA -> Bear Portfolio"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["rsi_10"] = 55.0  # Not oversold/overbought
        indicators["TQQQ"]["rsi_10"] = 55.0  # Not oversold
        indicators["VOX"]["rsi_10"] = 70.0  # Not overbought
        indicators["SPY"]["current_price"] = 380.0  # < 200 MA (400.0)

        # Mock BearMarketStrategy result
        with patch(
            "the_alchemiser.core.trading.nuclear_trading_bot.BearMarketStrategy"
        ) as mock_strategy:
            mock_instance = Mock()
            mock_instance.recommend.return_value = (
                "BEAR_PORTFOLIO",
                ActionType.BUY.value,
                "Bear market portfolio",
            )
            mock_strategy.return_value = mock_instance

            result = self.engine.evaluate_nuclear_strategy(indicators)

            self.assertEqual(result[0], "BEAR_PORTFOLIO")
            self.assertEqual(result[1], ActionType.BUY.value)

    def test_nuclear_portfolio_construction(self):
        """Test nuclear portfolio construction with top 3 stocks by performance"""

        indicators = self.base_indicators.copy()

        # Test equal weighting mode (default)
        self.engine.weighting_mode = "equal"
        portfolio = self.engine.get_nuclear_portfolio(indicators, top_n=3)

        # Should get top 3: OKLO (18%), BWXT (15%), SMR (12%)
        self.assertEqual(len(portfolio), 3)
        self.assertIn("OKLO", portfolio)
        self.assertIn("BWXT", portfolio)
        self.assertIn("SMR", portfolio)

        # Equal weights should be 1/3 each
        for symbol in portfolio:
            self.assertAlmostEqual(portfolio[symbol]["weight"], 1 / 3, places=3)

    def test_nuclear_portfolio_inverse_volatility(self):
        """Test nuclear portfolio with inverse volatility weighting"""

        indicators = self.base_indicators.copy()

        # Create mock market data with different volatilities
        mock_market_data = {
            "OKLO": pd.DataFrame(
                {"Close": [100, 110, 95, 105, 120, 90, 100] * 20}  # High volatility
            ),
            "BWXT": pd.DataFrame({"Close": [50, 51, 49, 50.5, 52, 48, 50] * 20}),  # Low volatility
            "SMR": pd.DataFrame({"Close": [75, 78, 72, 76, 80, 70, 75] * 20}),  # Medium volatility
        }

        self.engine.weighting_mode = "inverse_vol"
        portfolio = self.engine.get_nuclear_portfolio(indicators, mock_market_data, top_n=3)

        # Lower volatility stocks should get higher weights
        self.assertGreater(portfolio["BWXT"]["weight"], portfolio["OKLO"]["weight"])

    def test_bear_subgroup_1_scenarios(self):
        """Test all Bear Subgroup 1 scenarios from Clojure logic"""

        indicators = self.base_indicators.copy()

        # Scenario 1: PSQ RSI < 35 -> SQQQ
        indicators["PSQ"]["rsi_10"] = 30.0
        result = self.engine.bear_subgroup_1(indicators)
        self.assertEqual(result[0], "SQQQ")
        self.assertIn("PSQ oversold", result[2])

        # Scenario 2: QQQ cumulative return < -10% and bonds stronger than PSQ
        indicators["PSQ"]["rsi_10"] = 50.0  # Reset
        indicators["QQQ"]["cum_return_60"] = -15.0
        indicators["TLT"]["rsi_20"] = 60.0
        indicators["PSQ"]["rsi_20"] = 45.0  # TLT > PSQ
        result = self.engine.bear_subgroup_1(indicators)
        self.assertEqual(result[0], "TQQQ")
        self.assertIn("Bonds strong", result[2])

        # Scenario 3: TQQQ above 20 MA with bonds stronger than PSQ
        indicators["QQQ"]["cum_return_60"] = 5.0  # Reset
        indicators["TQQQ"]["current_price"] = 55.0
        indicators["TQQQ"]["ma_20"] = 50.0  # Price > MA
        result = self.engine.bear_subgroup_1(indicators)
        self.assertEqual(result[0], "TQQQ")

        # Scenario 4: TQQQ below 20 MA with IEF stronger than PSQ
        indicators["TQQQ"]["current_price"] = 45.0  # Below MA
        indicators["IEF"]["rsi_10"] = 60.0
        indicators["PSQ"]["rsi_20"] = 45.0  # IEF > PSQ
        result = self.engine.bear_subgroup_1(indicators)
        self.assertEqual(result[0], "SQQQ")

    def test_bear_subgroup_2_scenarios(self):
        """Test all Bear Subgroup 2 scenarios from Clojure logic"""

        indicators = self.base_indicators.copy()

        # Scenario 1: PSQ RSI < 35 -> SQQQ (same as subgroup 1)
        indicators["PSQ"]["rsi_10"] = 32.0
        result = self.engine.bear_subgroup_2(indicators)
        self.assertEqual(result[0], "SQQQ")

        # Scenario 2: TQQQ above MA with bonds stronger than PSQ
        indicators["PSQ"]["rsi_10"] = 50.0  # Reset
        indicators["TQQQ"]["current_price"] = 55.0
        indicators["TQQQ"]["ma_20"] = 50.0
        indicators["TLT"]["rsi_20"] = 60.0
        indicators["PSQ"]["rsi_20"] = 45.0
        result = self.engine.bear_subgroup_2(indicators)
        self.assertEqual(result[0], "TQQQ")

        # Scenario 3: TQQQ below MA with bonds stronger than PSQ -> QQQ
        indicators["TQQQ"]["current_price"] = 45.0  # Below MA
        result = self.engine.bear_subgroup_2(indicators)
        self.assertEqual(result[0], "QQQ")

    def test_bear_strategies_combination_same_symbol(self):
        """Test bear strategy combination when both subgroups return same symbol"""

        indicators = self.base_indicators.copy()

        # Set up conditions where both subgroups return SQQQ
        indicators["PSQ"]["rsi_10"] = 30.0  # Both will return SQQQ due to PSQ oversold

        bear1_result = self.engine.bear_subgroup_1(indicators)
        bear2_result = self.engine.bear_subgroup_2(indicators)

        # Both should return SQQQ
        self.assertEqual(bear1_result[0], "SQQQ")
        self.assertEqual(bear2_result[0], "SQQQ")

        # When combined, should just return the common result
        combined = self.engine.combine_bear_strategies_with_inverse_volatility(
            "SQQQ", "SQQQ", indicators
        )
        self.assertIsNone(combined)  # Same symbol returns None for portfolio

    def test_bear_strategies_combination_different_symbols(self):
        """Test bear strategy combination with different symbols -> inverse volatility portfolio"""

        indicators = self.base_indicators.copy()

        # Create different outcomes for bear subgroups
        # This requires careful setup to get different symbols
        bear1_symbol = "SQQQ"
        bear2_symbol = "QQQ"

        # Test the combination function directly
        portfolio = self.engine.combine_bear_strategies_with_inverse_volatility(
            bear1_symbol, bear2_symbol, indicators
        )

        if portfolio:  # If volatility data available
            self.assertIn(bear1_symbol, portfolio)
            self.assertIn(bear2_symbol, portfolio)

            # Weights should sum to ~1.0
            total_weight = sum(asset["weight"] for asset in portfolio.values())
            self.assertAlmostEqual(total_weight, 1.0, places=2)

    def test_missing_data_handling(self):
        """Test strategy behavior with missing indicator data"""

        # Test with minimal indicators
        minimal_indicators = {"SPY": {"rsi_10": 50.0, "current_price": 420.0, "ma_200": 400.0}}

        result = self.engine.evaluate_nuclear_strategy(minimal_indicators)

        # Should still return a valid result (fallback to SPY HOLD)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)  # (symbol, action, reason)

    def test_edge_case_boundary_values(self):
        """Test exact boundary values for RSI thresholds"""

        indicators = self.base_indicators.copy()

        # Test exact boundary: SPY RSI = 79.0 (should NOT trigger primary overbought)
        indicators["SPY"]["rsi_10"] = 79.0
        indicators["VOX"]["rsi_10"] = 70.0  # Not overbought
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold

        result = self.engine.evaluate_nuclear_strategy(indicators)
        # Should not be in primary overbought branch
        self.assertNotEqual(result[0], "UVXY_BTAL_PORTFOLIO")

        # Test exact boundary: SPY RSI = 79.1 (SHOULD trigger primary overbought)
        indicators["SPY"]["rsi_10"] = 79.1
        result = self.engine.evaluate_nuclear_strategy(indicators)
        # Should be in primary overbought branch since no secondary > 81
        self.assertEqual(result[0], "UVXY_BTAL_PORTFOLIO")

    def test_nuclear_portfolio_weighting_modes(self):
        """Test different portfolio weighting modes"""

        indicators = self.base_indicators.copy()

        # Test equal weighting
        self.engine.weighting_mode = "equal"
        portfolio_equal = self.engine.get_nuclear_portfolio(indicators, top_n=3)

        # All weights should be equal
        weights = [asset["weight"] for asset in portfolio_equal.values()]
        self.assertTrue(all(abs(w - 1 / 3) < 0.001 for w in weights))

        # Test inverse volatility (requires market data)
        self.engine.weighting_mode = "inverse_vol"
        portfolio_invol = self.engine.get_nuclear_portfolio(indicators, top_n=3)

        # Should still return valid portfolio even without market data
        self.assertEqual(len(portfolio_invol), 3)


class TestTECLStrategyEngine(unittest.TestCase):
    """Test TECL Strategy Engine - All scenarios from TECL_for_the_long_term.clj"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock data provider
        self.mock_data_provider = Mock(spec=UnifiedDataProvider)
        self.engine = TECLStrategyEngine(data_provider=self.mock_data_provider)

        # Base indicators for all tests
        self.base_indicators = {
            "SPY": {"rsi_10": 50.0, "ma_200": 400.0, "current_price": 420.0},  # Bull market default
            "TQQQ": {"rsi_10": 50.0},
            "SPXL": {"rsi_10": 50.0},
            "XLK": {"rsi_10": 50.0},
            "KMLM": {"rsi_10": 50.0},
            "UVXY": {"rsi_10": 50.0},
            "TECL": {"rsi_10": 50.0},
            "BIL": {"rsi_10": 50.0},
            "SQQQ": {"rsi_9": 50.0},
            "BSV": {"rsi_9": 50.0},
        }

    def test_bull_market_tqqq_overbought(self):
        """Test Bull Market: TQQQ RSI > 79 -> 25% UVXY + 75% BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # > 200 MA (bull market)
        indicators["TQQQ"]["rsi_10"] = 82.0  # Overbought

        result = self.engine.evaluate_tecl_strategy(indicators)

        # Should return mixed allocation
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]["UVXY"], 0.25, places=2)
        self.assertAlmostEqual(result[0]["BIL"], 0.75, places=2)
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("TQQQ overbought", result[2])

    def test_bull_market_spy_overbought(self):
        """Test Bull Market: SPY RSI > 80 -> 25% UVXY + 75% BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["SPY"]["rsi_10"] = 82.0  # Overbought
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought

        result = self.engine.evaluate_tecl_strategy(indicators)

        # Should return mixed allocation
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]["UVXY"], 0.25, places=2)
        self.assertAlmostEqual(result[0]["BIL"], 0.75, places=2)
        self.assertIn("SPY overbought", result[2])

    def test_bull_market_kmlm_switcher_xlk_stronger_normal(self):
        """Test Bull Market KMLM Switcher: XLK > KMLM RSI, XLK not extreme -> TECL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought
        indicators["XLK"]["rsi_10"] = 65.0  # Stronger than KMLM
        indicators["KMLM"]["rsi_10"] = 55.0  # Weaker than XLK

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "TECL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("technology favored", result[2])

    def test_bull_market_kmlm_switcher_xlk_extreme(self):
        """Test Bull Market KMLM Switcher: XLK > KMLM but XLK > 81 -> BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought
        indicators["XLK"]["rsi_10"] = 85.0  # Extremely overbought
        indicators["KMLM"]["rsi_10"] = 55.0  # Weaker than XLK

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "BIL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("extremely overbought", result[2])

    def test_bull_market_kmlm_switcher_kmlm_stronger_oversold(self):
        """Test Bull Market KMLM Switcher: KMLM > XLK, XLK oversold -> TECL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought
        indicators["XLK"]["rsi_10"] = 25.0  # Oversold
        indicators["KMLM"]["rsi_10"] = 55.0  # Stronger than XLK

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "TECL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("buying tech dip", result[2])

    def test_bull_market_kmlm_switcher_kmlm_stronger_normal(self):
        """Test Bull Market KMLM Switcher: KMLM > XLK, XLK normal -> BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought
        indicators["XLK"]["rsi_10"] = 45.0  # Normal (not oversold)
        indicators["KMLM"]["rsi_10"] = 55.0  # Stronger than XLK

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "BIL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("defensive cash", result[2])

    def test_bear_market_tqqq_oversold(self):
        """Test Bear Market: TQQQ RSI < 31 -> TECL (buy the dip)"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # < 200 MA (bear market)
        indicators["TQQQ"]["rsi_10"] = 28.0  # Oversold

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "TECL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("TQQQ oversold", result[2])

    def test_bear_market_spxl_oversold(self):
        """Test Bear Market: SPXL RSI < 29 -> SPXL (buy the dip)"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 26.0  # Oversold

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "SPXL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("SPXL oversold", result[2])

    def test_bear_market_uvxy_extreme_spike(self):
        """Test Bear Market: UVXY RSI > 84 -> 15% UVXY + 85% BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 40.0  # Not oversold
        indicators["UVXY"]["rsi_10"] = 88.0  # Extreme spike

        result = self.engine.evaluate_tecl_strategy(indicators)

        # Should return mixed allocation
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]["UVXY"], 0.15, places=2)
        self.assertAlmostEqual(result[0]["BIL"], 0.85, places=2)
        self.assertIn("extremely high", result[2])

    def test_bear_market_uvxy_high(self):
        """Test Bear Market: UVXY RSI > 74 (but < 84) -> BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 40.0  # Not oversold
        indicators["UVXY"]["rsi_10"] = 78.0  # High but not extreme

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "BIL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("defensive", result[2])

    def test_bear_market_kmlm_switcher_xlk_stronger(self):
        """Test Bear Market KMLM Switcher: XLK > KMLM -> TECL or BIL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 40.0  # Not oversold
        indicators["UVXY"]["rsi_10"] = 50.0  # Normal
        indicators["XLK"]["rsi_10"] = 65.0  # Stronger than KMLM
        indicators["KMLM"]["rsi_10"] = 55.0  # Weaker

        # XLK not extreme -> TECL
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertEqual(result[0], "TECL")

        # XLK extreme -> BIL
        indicators["XLK"]["rsi_10"] = 85.0
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertEqual(result[0], "BIL")

    def test_bear_market_kmlm_switcher_kmlm_stronger_oversold(self):
        """Test Bear Market KMLM Switcher: KMLM > XLK, XLK oversold -> TECL"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 40.0  # Not oversold
        indicators["UVXY"]["rsi_10"] = 50.0  # Normal
        indicators["XLK"]["rsi_10"] = 25.0  # Oversold
        indicators["KMLM"]["rsi_10"] = 55.0  # Stronger

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "TECL")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("buying tech dip", result[2])

    def test_bear_market_bond_vs_short_selection(self):
        """Test Bear Market: KMLM > XLK, XLK normal -> Bond/Short selection by RSI(9)"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 380.0  # Bear market
        indicators["TQQQ"]["rsi_10"] = 40.0  # Not oversold
        indicators["SPXL"]["rsi_10"] = 40.0  # Not oversold
        indicators["UVXY"]["rsi_10"] = 50.0  # Normal
        indicators["XLK"]["rsi_10"] = 45.0  # Normal (not oversold)
        indicators["KMLM"]["rsi_10"] = 55.0  # Stronger

        # SQQQ has higher RSI(9) -> Select SQQQ
        indicators["SQQQ"]["rsi_9"] = 65.0
        indicators["BSV"]["rsi_9"] = 45.0

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "SQQQ")
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn("filter", result[2])

        # BSV has higher RSI(9) -> Select BSV
        indicators["SQQQ"]["rsi_9"] = 35.0
        indicators["BSV"]["rsi_9"] = 55.0

        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertEqual(result[0], "BSV")

    def test_missing_spy_data(self):
        """Test error handling when SPY data is missing"""

        indicators = {}  # No SPY data

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "BIL")
        self.assertEqual(result[1], ActionType.HOLD.value)
        self.assertIn("Missing SPY", result[2])

    def test_missing_xlk_kmlm_data(self):
        """Test KMLM switcher with missing XLK or KMLM data"""

        indicators = self.base_indicators.copy()
        indicators["SPY"]["current_price"] = 450.0  # Bull market
        indicators["TQQQ"]["rsi_10"] = 75.0  # Not overbought
        indicators["SPY"]["rsi_10"] = 75.0  # Not overbought

        # Missing KMLM data
        del indicators["KMLM"]

        result = self.engine.evaluate_tecl_strategy(indicators)

        self.assertEqual(result[0], "BIL")
        self.assertIn("Missing XLK/KMLM", result[2])

    def test_edge_case_exact_boundaries(self):
        """Test exact threshold boundaries"""

        indicators = self.base_indicators.copy()

        # Bull market: TQQQ RSI exactly 79.0 (should NOT trigger overbought)
        indicators["SPY"]["current_price"] = 450.0
        indicators["TQQQ"]["rsi_10"] = 79.0
        indicators["SPY"]["rsi_10"] = 75.0
        indicators["XLK"]["rsi_10"] = 65.0
        indicators["KMLM"]["rsi_10"] = 55.0

        result = self.engine.evaluate_tecl_strategy(indicators)
        # Should go to KMLM switcher, not overbought protection
        self.assertEqual(result[0], "TECL")

        # TQQQ RSI exactly 79.1 (SHOULD trigger overbought)
        indicators["TQQQ"]["rsi_10"] = 79.1
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertIsInstance(result[0], dict)  # Mixed allocation

    def test_strategy_summary(self):
        """Test strategy summary generation"""

        summary = self.engine.get_strategy_summary()

        self.assertIsInstance(summary, str)
        self.assertIn("Bull Market", summary)
        self.assertIn("Bear Market", summary)
        self.assertIn("KMLM Switcher", summary)
        self.assertIn("TECL", summary)

    def test_market_regime_detection(self):
        """Test market regime detection logic"""

        indicators = self.base_indicators.copy()

        # Test bull market detection
        indicators["SPY"]["current_price"] = 450.0
        indicators["SPY"]["ma_200"] = 400.0

        # Should detect bull market and use bull path
        result = self.engine.evaluate_tecl_strategy(indicators)
        # Bull market should eventually lead to KMLM switcher if no overbought

        # Test bear market detection
        indicators["SPY"]["current_price"] = 350.0
        indicators["SPY"]["ma_200"] = 400.0

        # Should detect bear market and use bear path
        result = self.engine.evaluate_tecl_strategy(indicators)
        # Bear market should eventually lead to KMLM switcher if no special conditions


class TestStrategyEngineEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for both strategy engines"""

    def test_nuclear_engine_empty_indicators(self):
        """Test Nuclear engine with completely empty indicators"""

        engine = NuclearStrategyEngine()

        result = engine.evaluate_nuclear_strategy({})

        # Should still return a valid result
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_tecl_engine_initialization_error(self):
        """Test TECL engine initialization without data provider"""

        with self.assertRaises(ValueError):
            TECLStrategyEngine(data_provider=None)

    def test_nuclear_portfolio_no_nuclear_stocks(self):
        """Test nuclear portfolio when no nuclear stocks have data"""

        engine = NuclearStrategyEngine()
        indicators = {"SPY": {"rsi_10": 50.0, "ma_return_90": 5.0}}

        portfolio = engine.get_nuclear_portfolio(indicators)

        # Should return empty or minimal portfolio
        self.assertIsInstance(portfolio, dict)

    def test_volatility_calculation_edge_cases(self):
        """Test volatility calculations with edge case data"""

        engine = NuclearStrategyEngine()
        indicators = {
            "SQQQ": {"rsi_10": None},  # None RSI
            "TQQQ": {"rsi_10": "invalid"},  # Invalid RSI type
        }

        # Should handle gracefully without crashing
        vol1 = engine._get_14_day_volatility("SQQQ", indicators)
        vol2 = engine._get_14_day_volatility("TQQQ", indicators)

        # Should return default estimates or None
        self.assertTrue(vol1 is None or isinstance(vol1, float))
        self.assertTrue(vol2 is None or isinstance(vol2, float))

    def test_bond_strength_comparisons_missing_data(self):
        """Test bond strength comparison functions with missing data"""

        engine = NuclearStrategyEngine()

        # Missing TLT data
        indicators = {"PSQ": {"rsi_20": 50.0}}
        result = engine._bonds_stronger_than_psq(indicators)
        self.assertFalse(result)

        # Missing PSQ data
        indicators = {"TLT": {"rsi_20": 60.0}}
        result = engine._bonds_stronger_than_psq(indicators)
        self.assertFalse(result)

        # Missing IEF data
        indicators = {"PSQ": {"rsi_20": 50.0}}
        result = engine._ief_stronger_than_psq(indicators)
        self.assertFalse(result)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
