"""
Nuclear Trading Strategy Scenario Classes

This module contains scenario classes for the nuclear energy trading strategy,
focusing on signal logic and portfolio construction without execution or data management.
Each scenario handles specific mark        for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF']:
            if symbol in indicators:
                logging.debug(f"SecondaryOverboughtStrategy: {symbol} RSI(10) = {indicators[symbol]['rsi_10']:.2f}")
                if indicators[symbol]['rsi_10'] > 81:onditions and provides pure strategy recommendations.

This module now contains all the pure strategy logic for Nuclear energy trading,
including portfolio construction, bear market subgroup strategies, and overbought conditions.
"""

import logging
import numpy as np
import pandas as pd
from enum import Enum

# Import action types from common module
from the_alchemiser.core.common import ActionType


class NuclearStrategyEngine:
    """Pure Nuclear Strategy Logic - No data fetching or execution"""
    
    def __init__(self):
        # Nuclear energy stocks (the core of this strategy)
        self.nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
        logging.debug("NuclearStrategyEngine initialized")
    
    def get_nuclear_portfolio(self, indicators, market_data=None, top_n=3):
        """
        Get nuclear energy portfolio with top N stocks and their allocations using inverse volatility weighting.
        Returns a dict: {symbol: {weight, performance}}
        """
        nuclear_performance = []
        for symbol in self.nuclear_symbols:
            if symbol in indicators:
                perf = indicators[symbol].get('ma_return_90', 0)
                nuclear_performance.append((symbol, perf))
        # Sort by performance, descending
        nuclear_performance.sort(key=lambda x: x[1], reverse=True)
        top_stocks = nuclear_performance[:top_n]
        # If not enough, pad with available
        if len(top_stocks) < top_n:
            available = [s for s in self.nuclear_symbols if s in indicators]
            for s in available:
                if s not in [x[0] for x in top_stocks]:
                    top_stocks.append((s, 0.0))
                if len(top_stocks) >= top_n:
                    break
        # Calculate 90-day volatility for each stock
        volatilities = []
        for symbol, _ in top_stocks:
            if market_data and symbol in market_data:
                close = market_data[symbol]['Close']
                returns = close.pct_change().dropna()
                if len(returns) >= 90:
                    vol = returns[-90:].std() * np.sqrt(252)
                    # Ensure vol is a scalar, not a Series
                    if hasattr(vol, 'item'):
                        vol = vol.item()
                    vol = float(vol) if pd.notna(vol) else 0.3
                else:
                    vol = 0.3
            else:
                vol = 0.3  # fallback
            volatilities.append(max(vol, 0.01))
        # Inverse volatility weighting
        inv_vols = [1/v for v in volatilities]
        total_inv = sum(inv_vols)
        portfolio = {}
        for i, (symbol, perf) in enumerate(top_stocks):
            weight = inv_vols[i] / total_inv if total_inv > 0 else 1.0/top_n
            portfolio[symbol] = {'weight': weight, 'performance': perf}
        return portfolio

    def bear_subgroup_1(self, indicators):
        """Bear market subgroup 1 strategy logic"""
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', ActionType.BUY.value, "PSQ oversold, aggressive short position (Bear 1)"
        if 'QQQ' in indicators and indicators['QQQ']['cum_return_60'] < -10:
            if self._bonds_stronger_than_psq(indicators):
                return 'TQQQ', ActionType.BUY.value, "Bonds strong vs PSQ, contrarian TQQQ buy (Bear 1)"
            return 'PSQ', ActionType.BUY.value, "QQQ weak, defensive short position (Bear 1)"
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            if tqqq_price > tqqq_ma_20:
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', ActionType.BUY.value, "TQQQ trending up, bonds strong (Bear 1)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ up but bonds weak, short position (Bear 1)"
            else:
                if self._ief_stronger_than_psq(indicators):
                    return 'SQQQ', ActionType.BUY.value, "TQQQ weak, IEF strong, short position (Bear 1)"
                elif self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', ActionType.BUY.value, "TQQQ weak but bonds strong, neutral QQQ (Bear 1)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ weak, bonds weak, short position (Bear 1)"
        return 'SQQQ', ActionType.BUY.value, "Bear market conditions, short tech (Bear 1)"

    def bear_subgroup_2(self, indicators):
        """Bear market subgroup 2 strategy logic"""
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', ActionType.BUY.value, "PSQ oversold, aggressive short position (Bear 2)"
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            if tqqq_price > tqqq_ma_20:
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', ActionType.BUY.value, "TQQQ trending up, bonds strong (Bear 2)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ up but bonds weak, short position (Bear 2)"
            else:
                if self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', ActionType.BUY.value, "TQQQ weak but bonds strong, neutral QQQ (Bear 2)"
                return 'SQQQ', ActionType.BUY.value, "TQQQ weak, bonds weak, short position (Bear 2)"
        return 'SQQQ', ActionType.BUY.value, "Bear market conditions, short tech (Bear 2)"
    
    def _bonds_stronger_than_psq(self, indicators):
        """Check if TLT RSI(20) > PSQ RSI(20)"""
        if 'TLT' in indicators and 'PSQ' in indicators:
            tlt_rsi_20 = indicators['TLT']['rsi_20']
            psq_rsi_20 = indicators['PSQ']['rsi_20']
            return tlt_rsi_20 > psq_rsi_20
        return False
    
    def _ief_stronger_than_psq(self, indicators):
        """Check if IEF RSI(10) > PSQ RSI(20)"""
        if 'IEF' in indicators and 'PSQ' in indicators:
            ief_rsi_10 = indicators['IEF']['rsi_10']
            psq_rsi_20 = indicators['PSQ']['rsi_20']
            return ief_rsi_10 > psq_rsi_20
        return False
    
    def combine_bear_strategies_with_inverse_volatility(self, bear1_symbol, bear2_symbol, indicators):
        """
        Combine two bear strategy symbols using inverse volatility weighting (14-day window)
        Returns portfolio allocation dictionary or None if calculation fails
        """
        try:
            # Get 14-day volatility for both symbols
            vol1 = self._get_14_day_volatility(bear1_symbol, indicators)
            vol2 = self._get_14_day_volatility(bear2_symbol, indicators)
            
            if vol1 is None or vol2 is None or vol1 <= 0 or vol2 <= 0:
                return None
            
            # Calculate inverse volatility weights
            inv_vol1 = 1.0 / vol1
            inv_vol2 = 1.0 / vol2
            total_inv_vol = inv_vol1 + inv_vol2
            
            # Normalize to get portfolio weights
            weight1 = inv_vol1 / total_inv_vol
            weight2 = inv_vol2 / total_inv_vol
            
            # Return portfolio allocation
            portfolio = {}
            if weight1 > 0.01:  # Only include if weight > 1%
                portfolio[bear1_symbol] = {'weight': weight1, 'performance': 0.0}
            if weight2 > 0.01:  # Only include if weight > 1%
                portfolio[bear2_symbol] = {'weight': weight2, 'performance': 0.0}
            
            return portfolio if portfolio else None
            
        except Exception as e:
            # If anything goes wrong, fall back to None
            return None
    
    def _get_14_day_volatility(self, symbol, indicators):
        """
        Calculate 14-day volatility for a symbol
        Returns volatility or None if not available
        """
        try:
            if symbol in indicators:
                # Use historical data if available
                if 'price_history' in indicators[symbol] and len(indicators[symbol]['price_history']) >= 14:
                    prices = indicators[symbol]['price_history'][-14:]  # Last 14 days
                    returns = pd.Series(prices).pct_change().dropna()
                    vol = returns.std() * np.sqrt(252)  # Annualized volatility
                    return float(vol) if pd.notna(vol) else None
                
                # Fallback: use RSI-based volatility estimate if price history not available
                if 'rsi_10' in indicators[symbol]:
                    rsi = indicators[symbol]['rsi_10']
                    # RSI-based volatility estimate (higher RSI variability = higher volatility)
                    rsi_volatility = abs(50 - rsi) / 100.0  # Normalize RSI deviation
                    estimated_vol = 0.2 + (rsi_volatility * 0.3)  # 20-50% range
                    return estimated_vol
                
                # Last resort: use fixed volatility estimates based on symbol type
                volatility_estimates = {
                    'SQQQ': 0.8,  # High volatility leveraged short ETF
                    'TQQQ': 0.7,  # High volatility leveraged long ETF
                    'QQQ': 0.25,  # Medium volatility index ETF
                    'PSQ': 0.4,   # Medium-high volatility short ETF
                    'TLT': 0.2,   # Lower volatility bond ETF
                    'IEF': 0.15   # Low volatility bond ETF
                }
                return volatility_estimates.get(symbol, 0.3)  # Default 30% volatility
            
            return None
            
        except Exception as e:
            return None


class BullMarketStrategy:
    def __init__(self, nuclear_strategy_engine):
        self.nuclear_strategy_engine = nuclear_strategy_engine

    def recommend(self, indicators, market_data=None):
        nuclear_portfolio = self.nuclear_strategy_engine.get_nuclear_portfolio(indicators, market_data)
        if nuclear_portfolio:
            portfolio_stocks = list(nuclear_portfolio.keys())
            portfolio_desc = ", ".join([
                f"{s} ({nuclear_portfolio[s]['weight']:.1%})" for s in portfolio_stocks
            ])
            return 'NUCLEAR_PORTFOLIO', 'BUY', f"Bull market - Nuclear portfolio: {portfolio_desc}"
        return 'SMR', 'BUY', "Bull market - default nuclear energy play"

class BearMarketStrategy:
    def __init__(self, nuclear_strategy_engine):
        self.nuclear_strategy_engine = nuclear_strategy_engine

    def recommend(self, indicators):
        bear1_signal = self.nuclear_strategy_engine.bear_subgroup_1(indicators)
        bear2_signal = self.nuclear_strategy_engine.bear_subgroup_2(indicators)
        bear1_symbol = bear1_signal[0]
        bear2_symbol = bear2_signal[0]
        if bear1_symbol == bear2_symbol:
            return bear1_signal
        bear_portfolio = self.nuclear_strategy_engine.combine_bear_strategies_with_inverse_volatility(
            bear1_symbol, bear2_symbol, indicators
        )
        if bear_portfolio:
            portfolio_desc = ", ".join([
                f"{s} ({bear_portfolio[s]['weight']:.1%})" for s in bear_portfolio.keys()
            ])
            return 'BEAR_PORTFOLIO', 'BUY', f"Bear market portfolio: {portfolio_desc}"
        return bear1_signal

class OverboughtStrategy:
    def recommend(self, indicators):
        spy_rsi_10 = indicators['SPY']['rsi_10']
        logging.debug(f"OverboughtStrategy: SPY RSI(10) = {spy_rsi_10:.2f}")
        if spy_rsi_10 > 81:
            return 'UVXY', 'BUY', "SPY extremely overbought (RSI > 81)"
        
        # Check each symbol in order - first match wins
        for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF']:
            if symbol in indicators:
                logging.debug(f"OverboughtStrategy: {symbol} RSI(10) = {indicators[symbol]['rsi_10']:.2f}")
                if indicators[symbol]['rsi_10'] > 81:
                    return 'UVXY', 'BUY', f"{symbol} extremely overbought (RSI > 81)"
        
        # If SPY is overbought (79-81), return hedge portfolio 
        if spy_rsi_10 > 79:
            return 'UVXY_BTAL_PORTFOLIO', 'BUY', "SPY overbought (79-81), UVXY 75% + BTAL 25% allocation"
            
        # This should not be reached if called correctly from main strategy
        return None

class SecondaryOverboughtStrategy:
    def recommend(self, indicators, overbought_symbol):
        # First check if the overbought symbol is extremely overbought (> 81)
        logging.info(f"DEBUG SecondaryOverboughtStrategy: {overbought_symbol} RSI(10) = {indicators[overbought_symbol]['rsi_10']:.2f}")
        if indicators[overbought_symbol]['rsi_10'] > 81:
            return 'UVXY', 'BUY', f"{overbought_symbol} extremely overbought (RSI > 81)"
        
        # Then check other symbols for extreme overbought
        for symbol in ['TQQQ', 'VTV', 'XLF']:
            if symbol != overbought_symbol and symbol in indicators:
                logging.info(f"DEBUG SecondaryOverboughtStrategy: {symbol} RSI(10) = {indicators[symbol]['rsi_10']:.2f}")
                if indicators[symbol]['rsi_10'] > 81:
                    return 'UVXY', 'BUY', f"{symbol} extremely overbought (RSI > 81)"
        
        # If overbought symbol is moderately overbought (79-81), return hedge portfolio
        if indicators[overbought_symbol]['rsi_10'] > 79:
            return 'UVXY_BTAL_PORTFOLIO', 'BUY', f"{overbought_symbol} overbought (79-81), UVXY 75% + BTAL 25% allocation"
            
        return None

class VoxOverboughtStrategy:
    def recommend(self, indicators):
        # Check if XLF is extremely overbought 
        if 'XLF' in indicators and indicators['XLF']['rsi_10'] > 81:
            return 'UVXY', 'BUY', "XLF extremely overbought (RSI > 81)"
        
        # If VOX is moderately overbought (79-81), return hedge portfolio
        if 'VOX' in indicators and indicators['VOX']['rsi_10'] > 79:
            return 'UVXY_BTAL_PORTFOLIO', 'BUY', "VOX overbought (79-81), UVXY 75% + BTAL 25% allocation"
            
        return None

# Additional scenario classes can be added here as needed
