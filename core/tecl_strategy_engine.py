#!/usr/bin/env python3
"""
TECL Strategy Engine

Implements the "TECL For The Long Term (v7)" strategy from Composer.trade.
This strategy is designed for long-term technology leverage (TECL) with volatility protection.

Strategy Logic (translated from Clojure):
1. Market Regime Detection: SPY vs 200-day MA (bull vs bear market)
2. Volatility Protection: Multiple RSI-based triggers for defensive positions
3. Technology Focus: TECL as primary growth vehicle in appropriate conditions
4. Bond Hedge: BIL as defensive cash equivalent
5. Sector Rotation: XLK vs KMLM comparison for technology timing

Key Symbols:
- TECL: 3x leveraged technology ETF (primary growth vehicle)
- BIL: Short-term treasury bills (defensive cash equivalent)  
- UVXY: Volatility hedge for extreme overbought conditions
- XLK: Technology sector ETF (timing signal)
- KMLM: Materials sector ETF (comparative signal)
- TQQQ, SPXL, SPY: Market timing indicators
- SQQQ: Inverse NASDAQ for bear market conditions
- BSV: Short-term bond ETF alternative
"""

import logging
import warnings
import pandas as pd
import numpy as np
from enum import Enum

from .indicators import TechnicalIndicators
from .data_provider import UnifiedDataProvider
from .config import Config
from .logging_utils import setup_logging  # Centralized logging setup

warnings.filterwarnings('ignore')
setup_logging()


class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TECLStrategyEngine:
    """TECL Strategy Engine - Long-term technology leverage with volatility protection"""
    
    def __init__(self, data_provider=None):
        if data_provider is None:
            raise ValueError("data_provider is required for TECLStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()
        
        # Core symbols used in TECL strategy
        self.market_symbols = ['SPY', 'TQQQ', 'SPXL']
        self.tech_symbols = ['TECL', 'XLK', 'KMLM']
        self.volatility_symbols = ['UVXY']
        self.bond_symbols = ['BIL', 'BSV']
        self.inverse_symbols = ['SQQQ']
        
        # All symbols needed for the strategy
        self.all_symbols = (
            self.market_symbols + self.tech_symbols + 
            self.volatility_symbols + self.bond_symbols + self.inverse_symbols
        )
        
        logging.debug("TECLStrategyEngine initialized")
    
    def get_market_data(self):
        """Fetch data for all symbols"""
        market_data = {}
        for symbol in self.all_symbols:
            data = self.data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        return market_data
    
    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
        """Safely get indicator value, logging exceptions to surface data problems."""
        try:
            result = indicator_func(data, *args, **kwargs)
            if hasattr(result, 'iloc') and len(result) > 0:
                value = result.iloc[-1]
                # Check if value is NaN - if so, try to find the last valid value
                if pd.isna(value):
                    # Find the last non-NaN value
                    valid_values = result.dropna()
                    if len(valid_values) > 0:
                        value = valid_values.iloc[-1]
                    else:
                        logging.error(f"No valid values for indicator {indicator_func.__name__} on data: {data}")
                        return 50.0  # Fallback only if no valid values
                return float(value)
            logging.error(f"Indicator {indicator_func.__name__} returned no results for data: {data}")
            return 50.0
        except Exception as e:
            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}\nData: {data}")
            return 50.0
    
    def calculate_indicators(self, market_data):
        """Calculate all technical indicators needed for TECL strategy"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df['Close']
            indicators[symbol] = {
                'rsi_9': self.safe_get_indicator(close, self.indicators.rsi, 9),
                'rsi_10': self.safe_get_indicator(close, self.indicators.rsi, 10),
                'ma_200': self.safe_get_indicator(close, self.indicators.moving_average, 200),
                'current_price': float(close.iloc[-1]),
            }
        return indicators
    
    def evaluate_tecl_strategy(self, indicators, market_data=None):
        """
        Evaluate the TECL strategy using hierarchical logic from Clojure implementation.
        
        Returns: (recommended_symbol_or_allocation, action, reason)
        - For single symbols: returns symbol string
        - For multi-asset allocations: returns dict with symbol:weight pairs
        """
        if 'SPY' not in indicators:
            return 'BIL', ActionType.HOLD.value, "Missing SPY data for market regime detection"
        
        # Primary market regime detection: SPY vs 200 MA
        spy_price = indicators['SPY']['current_price']
        spy_ma_200 = indicators['SPY']['ma_200']
        
        if spy_price > spy_ma_200:
            # BULL MARKET PATH
            return self._evaluate_bull_market_path(indicators)
        else:
            # BEAR MARKET PATH  
            return self._evaluate_bear_market_path(indicators)
    
    def _evaluate_bull_market_path(self, indicators):
        """Evaluate strategy when SPY is above 200-day MA (bull market)"""
        
        # First check: TQQQ overbought > 79 - Mixed allocation (25% UVXY + 75% BIL)
        if 'TQQQ' in indicators and indicators['TQQQ']['rsi_10'] > 79:
            return {'UVXY': 0.25, 'BIL': 0.75}, ActionType.BUY.value, "Bull market: TQQQ overbought (RSI > 79), UVXY+BIL hedge"
        
        # Second check: SPY overbought > 80 - Mixed allocation (25% UVXY + 75% BIL)
        if indicators['SPY']['rsi_10'] > 80:
            return {'UVXY': 0.25, 'BIL': 0.75}, ActionType.BUY.value, "Bull market: SPY overbought (RSI > 80), UVXY+BIL hedge"
        
        # Third check: KMLM Switcher logic
        return self._evaluate_kmlm_switcher(indicators, "Bull market")
    
    def _evaluate_bear_market_path(self, indicators):
        """Evaluate strategy when SPY is below 200-day MA (bear market)"""
        
        # First check: TQQQ oversold < 31 (buy the dip even in bear market)
        if 'TQQQ' in indicators and indicators['TQQQ']['rsi_10'] < 31:
            return 'TECL', ActionType.BUY.value, "Bear market: TQQQ oversold (RSI < 31), buying tech dip"
        
        # Second check: SPXL oversold < 29 
        if 'SPXL' in indicators and indicators['SPXL']['rsi_10'] < 29:
            return 'SPXL', ActionType.BUY.value, "Bear market: SPXL oversold (RSI < 29), buying S&P dip"
        
        # Third check: UVXY volatility conditions
        if 'UVXY' in indicators:
            uvxy_rsi = indicators['UVXY']['rsi_10']
            
            if uvxy_rsi > 84:
                # Extreme UVXY spike - mixed position (15% UVXY + 85% BIL)
                return {'UVXY': 0.15, 'BIL': 0.85}, ActionType.BUY.value, "Bear market: UVXY extremely high (RSI > 84), UVXY+BIL volatility trade"
            elif uvxy_rsi > 74:
                # High UVXY - defensive
                return 'BIL', ActionType.BUY.value, "Bear market: UVXY high (RSI > 74), defensive cash position"
        
        # Fourth check: KMLM Switcher for bear market
        return self._evaluate_kmlm_switcher(indicators, "Bear market")
    
    def _evaluate_kmlm_switcher(self, indicators, market_regime):
        """
        KMLM Switcher logic: Compare XLK vs KMLM RSI to determine technology timing
        
        This is the core technology timing mechanism of the strategy.
        """
        if 'XLK' not in indicators or 'KMLM' not in indicators:
            return 'BIL', ActionType.BUY.value, f"{market_regime}: Missing XLK/KMLM data, defensive position"
        
        xlk_rsi = indicators['XLK']['rsi_10']
        kmlm_rsi = indicators['KMLM']['rsi_10']
        
        # Debug logging for RSI comparison
        logging.debug(f"KMLM Switcher - XLK RSI(10) = {xlk_rsi:.2f}, KMLM RSI(10) = {kmlm_rsi:.2f}")
        
        if xlk_rsi > kmlm_rsi:
            # Technology (XLK) is stronger than materials (KMLM)
            
            if xlk_rsi > 81:
                # XLK extremely overbought - defensive
                logging.debug(f"XLK extremely overbought: {xlk_rsi:.2f} > 81")
                return 'BIL', ActionType.BUY.value, f"{market_regime}: XLK extremely overbought (RSI > 81), defensive"
            else:
                # XLK strong but not extreme - buy technology
                logging.debug(f"XLK stronger than KMLM: {xlk_rsi:.2f} > {kmlm_rsi:.2f}")
                return 'TECL', ActionType.BUY.value, f"{market_regime}: XLK stronger than KMLM, technology favored"
        
        else:
            # Materials (KMLM) is stronger than technology (XLK) 
            
            if xlk_rsi < 29:
                # XLK oversold - buy the dip
                logging.debug(f"XLK oversold: {xlk_rsi:.2f} < 29")
                return 'TECL', ActionType.BUY.value, f"{market_regime}: XLK oversold (RSI < 29), buying tech dip"
            else:
                # XLK weak - return BIL directly in bull market, use selection in bear market
                logging.debug(f"KMLM stronger than XLK: {kmlm_rsi:.2f} > {xlk_rsi:.2f}")
                if market_regime == "Bull market":
                    return 'BIL', ActionType.BUY.value, f"{market_regime}: XLK weaker than KMLM, defensive cash position"
                else:
                    # Bear market - use bond vs short selection
                    return self._evaluate_bond_vs_short_selection(indicators, market_regime)
    
    def _evaluate_bond_vs_short_selection(self, indicators, market_regime):
        """
        Final selection between bonds and short positions using RSI filter mechanism.
        This implements the filter/select-top logic from the Clojure version.
        """
        # Create candidate list with their RSI(9) values
        candidates = []
        
        if 'SQQQ' in indicators:
            candidates.append(('SQQQ', indicators['SQQQ']['rsi_9']))
        
        if 'BSV' in indicators:
            candidates.append(('BSV', indicators['BSV']['rsi_9']))
        
        if not candidates:
            return 'BIL', ActionType.BUY.value, f"{market_regime}: No candidates available, default cash"
        
        # Select the candidate with the highest RSI(9) - "select-top 1" from Clojure
        best_candidate = max(candidates, key=lambda x: x[1])
        symbol, rsi_value = best_candidate
        
        return symbol, ActionType.BUY.value, f"{market_regime}: Selected {symbol} (RSI 9: {rsi_value:.1f}) via bond/short filter"
    
    def get_strategy_summary(self) -> str:
        """Get a summary description of the TECL strategy"""
        return """
        TECL Strategy Summary:
        
        Bull Market (SPY > 200 MA):
        1. If TQQQ RSI > 79 → 25% UVXY + 75% BIL (volatility hedge)
        2. If SPY RSI > 80 → 25% UVXY + 75% BIL (volatility hedge) 
        3. KMLM Switcher:
           - If XLK RSI > KMLM RSI:
             * XLK RSI > 81 → BIL (defensive)
             * Else → TECL (technology growth)
           - If KMLM RSI > XLK RSI:
             * XLK RSI < 29 → TECL (buy dip)
             * Else → BIL (defensive cash)
        
        Bear Market (SPY < 200 MA):
        1. If TQQQ RSI < 31 → TECL (buy tech dip)
        2. If SPXL RSI < 29 → SPXL (buy S&P dip)
        3. If UVXY RSI > 84 → 15% UVXY + 85% BIL (volatility spike)
        4. If UVXY RSI > 74 → BIL (defensive)
        5. KMLM Switcher:
           - If XLK RSI > KMLM RSI:
             * XLK RSI > 81 → BIL (defensive)
             * Else → TECL (technology growth)
           - If KMLM RSI > XLK RSI:
             * XLK RSI < 29 → TECL (buy dip)
             * Else → Bond/Short selection
        
        Bond/Short Selection (Bear Market Only):
        - Compare SQQQ vs BSV using RSI(9)
        - Select highest RSI candidate
        """


def main():
    """Test the TECL strategy engine"""
    
    print("🚀 TECL Strategy Engine Test")
    print("=" * 50)
    
    # Initialize engine
    engine = TECLStrategyEngine()
    
    # Get market data
    print("📊 Fetching market data...")
    market_data = engine.get_market_data()
    print(f"✅ Fetched data for {len(market_data)} symbols")
    
    # Calculate indicators
    print("🔬 Calculating technical indicators...")
    indicators = engine.calculate_indicators(market_data)
    print(f"✅ Calculated indicators for {len(indicators)} symbols")
    
    # Evaluate strategy
    print("⚡ Evaluating TECL strategy...")
    symbol_or_allocation, action, reason = engine.evaluate_tecl_strategy(indicators, market_data)
    
    print(f"\n🎯 TECL STRATEGY RESULT:")
    print(f"   Action: {action}")
    if isinstance(symbol_or_allocation, dict):
        print(f"   Allocation: {symbol_or_allocation}")
    else:
        print(f"   Symbol: {symbol_or_allocation}")
    print(f"   Reason: {reason}")
    
    # Print key indicators
    print(f"\n🔬 Key Technical Indicators:")
    key_symbols = ['SPY', 'XLK', 'KMLM', 'TQQQ', 'UVXY']
    for sym in key_symbols:
        if sym in indicators:
            print(f"   {sym}: RSI(10)={indicators[sym]['rsi_10']:.1f}")
    
    print(f"\n📈 Strategy Summary:")
    print(engine.get_strategy_summary())


if __name__ == "__main__":
    main()
