#!/usr/bin/env python3
"""
Unit Tests for TECL Strategy Engine

This module tests the TECL strategy engine logic against every scenario defined in 
the TECL_for_the_long_term.clj file from Composer.trade. 

The Clojure strategy defines a hierarchical decision tree:
1. Market Regime Detection: SPY vs 200 MA (bull vs bear)
2. Bull Market Path: Volatility protection + KMLM switcher
3. Bear Market Path: Oversold checks + volatility protection + KMLM switcher
4. KMLM Switcher: XLK vs KMLM RSI comparison for tech timing
5. Bond/Short Selection: RSI(9) filter for SQQQ vs BSV

Test Categories:
- Market Regime Detection Tests
- Bull Market Scenario Tests  
- Bear Market Scenario Tests
- KMLM Switcher Logic Tests
- Volatility Protection Tests
- Edge Cases and Error Handling
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
from typing import Dict, Any

# Import the TECL strategy engine
from the_alchemiser.core.trading.tecl_strategy_engine import TECLStrategyEngine
from the_alchemiser.core.utils.common import ActionType
from the_alchemiser.core.data.data_provider import UnifiedDataProvider


class TestTECLStrategyEngine(unittest.TestCase):
    """
    Test TECL Strategy Engine - Every scenario from TECL_for_the_long_term.clj
    
    Clojure Strategy Structure:
    (if (> SPY_price SPY_200MA)
        BULL_MARKET_PATH
        BEAR_MARKET_PATH)
        
    Bull Market Path:
    1. TQQQ RSI > 79 -> 25% UVXY + 75% BIL
    2. SPY RSI > 80 -> 25% UVXY + 75% BIL  
    3. KMLM Switcher -> XLK vs KMLM comparison
    
    Bear Market Path:
    1. TQQQ RSI < 31 -> TECL
    2. SPXL RSI < 29 -> SPXL
    3. UVXY RSI > 84 -> 15% UVXY + 85% BIL
    4. UVXY RSI > 74 -> BIL
    5. KMLM Switcher -> XLK vs KMLM with bond/short selection
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock data provider
        self.mock_data_provider = Mock(spec=UnifiedDataProvider)
        self.engine = TECLStrategyEngine(data_provider=self.mock_data_provider)
        
        # Base indicators representing neutral market conditions
        self.base_indicators = {
            'SPY': {
                'rsi_10': 50.0,
                'ma_200': 400.0,
                'current_price': 420.0  # Bull market default (420 > 400)
            },
            'TQQQ': {'rsi_10': 50.0},
            'SPXL': {'rsi_10': 50.0},
            'XLK': {'rsi_10': 60.0},    # Make XLK stronger than KMLM by default
            'KMLM': {'rsi_10': 40.0},   # Make KMLM weaker than XLK by default
            'UVXY': {'rsi_10': 50.0},
            'TECL': {'rsi_10': 50.0},
            'BIL': {'rsi_10': 50.0},
            'SQQQ': {'rsi_9': 50.0},
            'BSV': {'rsi_9': 50.0}
        }

    # ==================== MARKET REGIME DETECTION TESTS ====================
    
    def test_market_regime_detection_bull(self):
        """Test bull market detection: SPY > 200 MA"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # > 200 MA (400.0)
        indicators['SPY']['ma_200'] = 400.0
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # Should enter bull market path - since no overbought conditions,
        # should reach KMLM switcher and recommend TECL (XLK > KMLM by default)
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)

    def test_market_regime_detection_bear(self):
        """Test bear market detection: SPY < 200 MA"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # < 200 MA (400.0)
        indicators['SPY']['ma_200'] = 400.0
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # Should enter bear market path - since no oversold/volatility conditions,
        # should reach KMLM switcher and recommend TECL (XLK > KMLM by default)
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)

    def test_missing_spy_data_error_handling(self):
        """Test error handling when SPY data is missing"""
        indicators = {}  # No SPY data
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertEqual(result[1], ActionType.HOLD.value)
        self.assertIn('Missing SPY', result[2])

    # ==================== BULL MARKET SCENARIO TESTS ====================
    
    def test_bull_market_tqqq_overbought_protection(self):
        """Test Bull Market: TQQQ RSI > 79 -> 25% UVXY + 75% BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 82.0  # Overbought (> 79)
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # Should return mixed allocation dictionary
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]['UVXY'], 0.25, places=3)
        self.assertAlmostEqual(result[0]['BIL'], 0.75, places=3)
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('TQQQ overbought', result[2])

    def test_bull_market_spy_overbought_protection(self):
        """Test Bull Market: SPY RSI > 80 -> 25% UVXY + 75% BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['SPY']['rsi_10'] = 82.0  # Overbought (> 80)
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # Should return mixed allocation dictionary
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]['UVXY'], 0.25, places=3)
        self.assertAlmostEqual(result[0]['BIL'], 0.75, places=3)
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('SPY overbought', result[2])

    def test_bull_market_both_overbought_tqqq_priority(self):
        """Test Bull Market: Both TQQQ and SPY overbought - TQQQ should trigger first"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 85.0  # Overbought
        indicators['SPY']['rsi_10'] = 83.0   # Also overbought
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # TQQQ check comes first in the hierarchy
        self.assertIn('TQQQ overbought', result[2])

    # ==================== BULL MARKET KMLM SWITCHER TESTS ====================
    
    def test_bull_market_kmlm_switcher_xlk_stronger_normal(self):
        """Test Bull Market KMLM Switcher: XLK > KMLM RSI, XLK <= 81 -> TECL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        indicators['XLK']['rsi_10'] = 65.0   # Stronger than KMLM
        indicators['KMLM']['rsi_10'] = 55.0  # Weaker than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('technology favored', result[2])

    def test_bull_market_kmlm_switcher_xlk_extremely_overbought(self):
        """Test Bull Market KMLM Switcher: XLK > KMLM but XLK > 81 -> BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        indicators['XLK']['rsi_10'] = 85.0   # Extremely overbought (> 81)
        indicators['KMLM']['rsi_10'] = 55.0  # Weaker than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('extremely overbought', result[2])

    def test_bull_market_kmlm_switcher_kmlm_stronger_xlk_oversold(self):
        """Test Bull Market KMLM Switcher: KMLM > XLK, XLK < 29 -> TECL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        indicators['XLK']['rsi_10'] = 25.0   # Oversold (< 29)
        indicators['KMLM']['rsi_10'] = 55.0  # Stronger than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('buying tech dip', result[2])

    def test_bull_market_kmlm_switcher_kmlm_stronger_xlk_normal(self):
        """Test Bull Market KMLM Switcher: KMLM > XLK, XLK normal -> BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        indicators['XLK']['rsi_10'] = 45.0   # Normal (>= 29, not oversold)
        indicators['KMLM']['rsi_10'] = 55.0  # Stronger than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('defensive cash', result[2])

    def test_bull_market_kmlm_switcher_missing_data(self):
        """Test Bull Market KMLM Switcher with missing XLK or KMLM data"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 75.0  # Not overbought
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        
        # Remove KMLM data
        del indicators['KMLM']
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertIn('Missing XLK/KMLM', result[2])

    # ==================== BEAR MARKET SCENARIO TESTS ====================
    
    def test_bear_market_tqqq_oversold_buy_dip(self):
        """Test Bear Market: TQQQ RSI < 31 -> TECL (buy the dip)"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market (< 400 MA)
        indicators['TQQQ']['rsi_10'] = 28.0  # Oversold (< 31)
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('TQQQ oversold', result[2])

    def test_bear_market_spxl_oversold_buy_dip(self):
        """Test Bear Market: SPXL RSI < 29 -> SPXL (buy the dip)"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0  # Not oversold
        indicators['SPXL']['rsi_10'] = 26.0  # Oversold (< 29)
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'SPXL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('SPXL oversold', result[2])

    def test_bear_market_oversold_priority_tqqq_first(self):
        """Test Bear Market: TQQQ oversold takes priority over SPXL oversold"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 28.0  # Oversold
        indicators['SPXL']['rsi_10'] = 26.0  # Also oversold
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # TQQQ check comes first in the hierarchy
        self.assertEqual(result[0], 'TECL')
        self.assertIn('TQQQ oversold', result[2])

    # ==================== BEAR MARKET VOLATILITY PROTECTION TESTS ====================
    
    def test_bear_market_uvxy_extreme_spike(self):
        """Test Bear Market: UVXY RSI > 84 -> 15% UVXY + 85% BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0  # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0  # Not oversold
        indicators['UVXY']['rsi_10'] = 88.0  # Extreme spike (> 84)
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # Should return mixed allocation dictionary
        self.assertIsInstance(result[0], dict)
        self.assertAlmostEqual(result[0]['UVXY'], 0.15, places=3)
        self.assertAlmostEqual(result[0]['BIL'], 0.85, places=3)
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('extremely high', result[2])

    def test_bear_market_uvxy_high_defensive(self):
        """Test Bear Market: UVXY RSI > 74 (but <= 84) -> BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0  # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0  # Not oversold
        indicators['UVXY']['rsi_10'] = 78.0  # High but not extreme (74 < RSI <= 84)
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('defensive', result[2])

    def test_bear_market_uvxy_boundary_conditions(self):
        """Test Bear Market UVXY boundary conditions (exactly 74, 84)"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0  # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0  # Not oversold
        
        # Test exactly 74.0 (should NOT trigger high UVXY condition)
        indicators['UVXY']['rsi_10'] = 74.0
        result = self.engine.evaluate_tecl_strategy(indicators)
        # Should proceed to KMLM switcher - with XLK(60) > KMLM(40), expect TECL
        self.assertEqual(result[0], 'TECL')
        
        # Test exactly 74.1 (SHOULD trigger high UVXY condition)
        indicators['UVXY']['rsi_10'] = 74.1
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertEqual(result[0], 'BIL')
        
        # Test exactly 84.0 (should trigger high UVXY, not extreme)
        indicators['UVXY']['rsi_10'] = 84.0
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertEqual(result[0], 'BIL')
        
        # Test exactly 84.1 (SHOULD trigger extreme UVXY)
        indicators['UVXY']['rsi_10'] = 84.1
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertIsInstance(result[0], dict)  # Mixed allocation

    # ==================== BEAR MARKET KMLM SWITCHER TESTS ====================
    
    def test_bear_market_kmlm_switcher_xlk_stronger_normal(self):
        """Test Bear Market KMLM Switcher: XLK > KMLM, XLK <= 81 -> TECL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 65.0    # Stronger than KMLM
        indicators['KMLM']['rsi_10'] = 55.0   # Weaker than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('technology favored', result[2])

    def test_bear_market_kmlm_switcher_xlk_extremely_overbought(self):
        """Test Bear Market KMLM Switcher: XLK > KMLM but XLK > 81 -> BIL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 85.0    # Extremely overbought
        indicators['KMLM']['rsi_10'] = 55.0   # Weaker than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('defensive', result[2])

    def test_bear_market_kmlm_switcher_kmlm_stronger_xlk_oversold(self):
        """Test Bear Market KMLM Switcher: KMLM > XLK, XLK < 29 -> TECL"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 25.0    # Oversold (< 29)
        indicators['KMLM']['rsi_10'] = 55.0   # Stronger than XLK
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'TECL')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('buying tech dip', result[2])

    # ==================== BEAR MARKET BOND/SHORT SELECTION TESTS ====================
    
    def test_bear_market_bond_short_selection_sqqq_higher_rsi(self):
        """Test Bear Market Bond/Short Selection: SQQQ RSI(9) > BSV RSI(9) -> SQQQ"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 45.0    # Normal (not oversold, >= 29)
        indicators['KMLM']['rsi_10'] = 55.0   # Stronger than XLK
        
        # SQQQ has higher RSI(9) -> should select SQQQ
        indicators['SQQQ']['rsi_9'] = 65.0
        indicators['BSV']['rsi_9'] = 45.0
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'SQQQ')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('filter', result[2])

    def test_bear_market_bond_short_selection_bsv_higher_rsi(self):
        """Test Bear Market Bond/Short Selection: BSV RSI(9) > SQQQ RSI(9) -> BSV"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 45.0    # Normal (not oversold)
        indicators['KMLM']['rsi_10'] = 55.0   # Stronger than XLK
        
        # BSV has higher RSI(9) -> should select BSV
        indicators['SQQQ']['rsi_9'] = 35.0
        indicators['BSV']['rsi_9'] = 55.0
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BSV')
        self.assertEqual(result[1], ActionType.BUY.value)
        self.assertIn('filter', result[2])

    def test_bear_market_bond_short_selection_missing_candidates(self):
        """Test Bear Market Bond/Short Selection with missing SQQQ or BSV data"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0   # Not oversold
        indicators['SPXL']['rsi_10'] = 40.0   # Not oversold
        indicators['UVXY']['rsi_10'] = 50.0   # Normal volatility
        indicators['XLK']['rsi_10'] = 45.0    # Normal
        indicators['KMLM']['rsi_10'] = 55.0   # Stronger than XLK
        
        # Remove both candidates
        del indicators['SQQQ']
        del indicators['BSV']
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'BIL')
        self.assertIn('No candidates', result[2])

    def test_bear_market_bond_short_selection_single_candidate(self):
        """Test Bear Market Bond/Short Selection with only one candidate available"""
        indicators = self.base_indicators.copy()
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 40.0
        indicators['SPXL']['rsi_10'] = 40.0
        indicators['UVXY']['rsi_10'] = 50.0
        indicators['XLK']['rsi_10'] = 45.0
        indicators['KMLM']['rsi_10'] = 55.0
        
        # Only SQQQ available
        del indicators['BSV']
        indicators['SQQQ']['rsi_9'] = 60.0
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        self.assertEqual(result[0], 'SQQQ')

    # ==================== EDGE CASES AND BOUNDARY TESTS ====================
    
    def test_rsi_boundary_conditions_exact_thresholds(self):
        """Test exact RSI threshold boundaries for all conditions"""
        indicators = self.base_indicators.copy()
        
        # Bull market TQQQ boundary: 79.0 vs 79.1
        indicators['SPY']['current_price'] = 450.0  # Bull market
        indicators['TQQQ']['rsi_10'] = 79.0  # Exactly 79 (should NOT trigger)
        indicators['SPY']['rsi_10'] = 75.0   # Not overbought
        # With our base setup, XLK(60) > KMLM(40), so should get TECL
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        # Should proceed to KMLM switcher, not overbought protection
        self.assertEqual(result[0], 'TECL')
        
        indicators['TQQQ']['rsi_10'] = 79.1  # Just above 79 (SHOULD trigger)
        result = self.engine.evaluate_tecl_strategy(indicators)
        self.assertIsInstance(result[0], dict)  # Mixed allocation

    def test_complex_scenario_multiple_conditions_hierarchy(self):
        """Test complex scenario with multiple competing conditions to verify hierarchy"""
        indicators = self.base_indicators.copy()
        
        # Bear market with multiple potential triggers
        indicators['SPY']['current_price'] = 350.0  # Bear market
        indicators['TQQQ']['rsi_10'] = 28.0   # Oversold (should trigger first)
        indicators['SPXL']['rsi_10'] = 26.0   # Also oversold
        indicators['UVXY']['rsi_10'] = 85.0   # Also extreme
        indicators['XLK']['rsi_10'] = 25.0    # Also oversold
        
        result = self.engine.evaluate_tecl_strategy(indicators)
        
        # TQQQ oversold should trigger first in the hierarchy
        self.assertEqual(result[0], 'TECL')
        self.assertIn('TQQQ oversold', result[2])

    def test_strategy_summary_generation(self):
        """Test strategy summary generation"""
        summary = self.engine.get_strategy_summary()
        
        self.assertIsInstance(summary, str)
        self.assertIn('Bull Market', summary)
        self.assertIn('Bear Market', summary)
        self.assertIn('KMLM Switcher', summary)
        self.assertIn('TECL', summary)
        self.assertIn('UVXY', summary)
        self.assertIn('BIL', summary)

    def test_indicator_calculation_safety(self):
        """Test safe indicator calculation with invalid data"""
        # Test with mock market data
        mock_data = pd.DataFrame({'Close': [100, 110, 90, 105, 95]})
        
        # Test safe_get_indicator with valid data
        result = self.engine.safe_get_indicator(mock_data['Close'], self.engine.indicators.rsi, 10)
        self.assertIsInstance(result, float)
        
        # Test safe_get_indicator with insufficient data (only 2 points for RSI)
        short_data = pd.DataFrame({'Close': [100, 110]})
        result = self.engine.safe_get_indicator(short_data['Close'], self.engine.indicators.rsi, 10)
        # RSI might still calculate something with 2 points, so just check it's a float
        self.assertIsInstance(result, float)
        
        # Test with empty data
        empty_data = pd.DataFrame({'Close': []})
        result = self.engine.safe_get_indicator(empty_data['Close'], self.engine.indicators.rsi, 10)
        self.assertEqual(result, 50.0)  # Should return default

    def test_engine_initialization_requirements(self):
        """Test engine initialization requirements"""
        # Should require data provider
        with self.assertRaises(ValueError):
            TECLStrategyEngine(data_provider=None)
        
        # Should initialize with valid data provider
        mock_provider = Mock(spec=UnifiedDataProvider)
        engine = TECLStrategyEngine(data_provider=mock_provider)
        self.assertIsNotNone(engine)


if __name__ == '__main__':
    # Run the tests with detailed output
    unittest.main(verbosity=2)
