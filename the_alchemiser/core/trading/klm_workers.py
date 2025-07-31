"""
KLM Strategy Variant Workers

Individual strategy variants implementing different configurations of the KLM ensemble.
Each variant represents a different parameter set and strategy logic from the original
Clojure implementation.

This module contains 8 strategy variants:
- KLMVariant506_38: Standard overbought detection
- KLMVariant1280_26: Parameter variant with different thresholds
- KLMVariant1200_28: Another parameter configuration
- KLMVariant520_22: "Original" baseline variant
- KLMVariant530_18: Scale-In strategy (most complex)
- KLMVariant410_38: MonkeyBusiness Simons variant
- KLMVariantNova: Short backtest optimization variant
- KLMVariant830_21: MonkeyBusiness Simons V2

Each variant follows the BaseKLMVariant interface for ensemble compatibility.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any
from abc import ABC, abstractmethod

from the_alchemiser.core.utils.common import ActionType


class BaseKLMVariant(ABC):
    """Base class for all KLM strategy variants"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = "Base KLM variant"
        self.logger = logging.getLogger(f"KLM.{self.name}")
        
        # Performance tracking for ensemble selection
        self.historical_returns = []
        self.trade_count = 0
        self.last_signal = None
        
    @abstractmethod
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate the strategy variant and return recommendation.
        
        Args:
            indicators: Calculated technical indicators for all symbols
            market_data: Raw market data for all symbols
            
        Returns:
            Tuple of (symbol_or_allocation, action, reason)
        """
        pass
    
    def calculate_performance_metric(self, window: int = 5) -> float:
        """
        Calculate 5-day standard deviation of returns for ensemble selection.
        
        This implements the (stdev-return {:window 5}) filter from Clojure.
        """
        if len(self.historical_returns) < window:
            # Default performance for new variants
            return np.random.uniform(0.1, 0.9)
        
        recent_returns = self.historical_returns[-window:]
        return float(np.std(recent_returns))
    
    def update_performance(self, return_value: float):
        """Update performance tracking with new return"""
        self.historical_returns.append(return_value)
        # Keep only last 100 returns for memory efficiency
        if len(self.historical_returns) > 100:
            self.historical_returns = self.historical_returns[-100:]
    
    def _check_rsi_threshold(self, indicators: Dict[str, Dict[str, float]], 
                            symbol: str, rsi_period: int, threshold: float, 
                            above: bool = True) -> bool:
        """Helper to check RSI thresholds"""
        if symbol not in indicators:
            return False
        
        rsi_key = f'rsi_{rsi_period}'
        if rsi_key not in indicators[symbol]:
            return False
        
        rsi_value = indicators[symbol][rsi_key]
        if above:
            return rsi_value > threshold
        else:
            return rsi_value < threshold
    
    def _get_rsi_value(self, indicators: Dict[str, Dict[str, float]], 
                      symbol: str, period: int = 10) -> float:
        """Safely get RSI value"""
        if symbol not in indicators:
            return 50.0
        
        rsi_key = f'rsi_{period}'
        return indicators[symbol].get(rsi_key, 50.0)


class KLMVariant506_38(BaseKLMVariant):
    """506/38 KMLM - Standard overbought detection variant"""
    
    def __init__(self):
        super().__init__()
        self.description = "Standard overbought detection with VIX positioning"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 506/38 variant: Focus on overbought conditions and VIX rotation
        """
        
        # Check major overbought conditions (single pops)
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [79, 79, 79, 79, 79, 79, 75]
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[506/38] {symbol} overbought (RSI={self._get_rsi_value(indicators, symbol, 10):.1f} > {threshold})"
                reason += f" -> VIX positioning for volatility protection"
                return 'UVXY', ActionType.BUY.value, reason
        
        # Check UVXY conditions for BSC vs Combined Pop Bot
        uvxy_rsi_21 = self._get_rsi_value(indicators, 'UVXY', 21)
        spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
        
        if uvxy_rsi_21 > 65:
            if spy_rsi_21 > 30:
                reason = f"[506/38] UVXY popped (RSI={uvxy_rsi_21:.1f}) + SPY strong (RSI={spy_rsi_21:.1f})"
                reason += f" -> Bond positioning (VIXM)"
                return 'VIXM', ActionType.BUY.value, reason
            else:
                reason = f"[506/38] UVXY popped (RSI={uvxy_rsi_21:.1f}) + SPY weak (RSI={spy_rsi_21:.1f})"
                reason += f" -> Equity positioning (SPXL)"
                return 'SPXL', ActionType.BUY.value, reason
        
        # Combined Pop Bot logic - check for oversold 3x ETFs
        oversold_checks = [
            ('TQQQ', 30, 'TECL'),
            ('SOXL', 30, 'SOXL'), 
            ('SPXL', 30, 'SPXL'),
            ('LABU', 25, 'LABU')
        ]
        
        for check_symbol, threshold, target_symbol in oversold_checks:
            if self._check_rsi_threshold(indicators, check_symbol, 10, threshold, above=False):
                reason = f"[506/38] {check_symbol} oversold (RSI={self._get_rsi_value(indicators, check_symbol, 10):.1f} < {threshold})"
                reason += f" -> Buy the dip ({target_symbol})"
                return target_symbol, ActionType.BUY.value, reason
        
        # KMLM Switcher logic
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi:
            # Technology stronger than materials -> select best tech
            tech_options = ['TECL', 'SOXL', 'SVIX']
            min_rsi = float('inf')
            best_tech = 'TECL'
            
            for tech in tech_options:
                tech_rsi = self._get_rsi_value(indicators, tech, 10)
                if tech_rsi < min_rsi:
                    min_rsi = tech_rsi
                    best_tech = tech
            
            reason = f"[506/38] XLK > KMLM ({xlk_rsi:.1f} > {kmlm_rsi:.1f})"
            reason += f" -> Tech leadership, buy {best_tech} (RSI={min_rsi:.1f})"
            return best_tech, ActionType.BUY.value, reason
        else:
            # Materials stronger -> Long/Short rotator
            reason = f"[506/38] KMLM > XLK ({kmlm_rsi:.1f} > {xlk_rsi:.1f})"
            reason += f" -> Materials leadership, defensive positioning"
            return 'FTLS', ActionType.BUY.value, reason


class KLMVariant1280_26(BaseKLMVariant):
    """1280/26 KMLM - Parameter variant with different thresholds"""
    
    def __init__(self):
        super().__init__()
        self.description = "Parameter variant with modified thresholds"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 1280/26 variant: Similar to 506/38 but with different parameters
        """
        
        # Similar structure to 506/38 but with modified thresholds
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [80, 80, 80, 80, 80, 80, 77]  # Slightly higher thresholds
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[1280/26] {symbol} overbought (RSI={self._get_rsi_value(indicators, symbol, 10):.1f} > {threshold})"
                reason += f" -> VIX positioning (higher threshold variant)"
                return 'UVXY', ActionType.BUY.value, reason
        
        # UVXY check with different threshold
        uvxy_rsi_21 = self._get_rsi_value(indicators, 'UVXY', 21)
        spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
        
        if uvxy_rsi_21 > 67:  # Higher threshold
            if spy_rsi_21 > 32:  # Higher threshold
                reason = f"[1280/26] UVXY strong pop (RSI={uvxy_rsi_21:.1f}) + SPY resilient"
                return 'VIXM', ActionType.BUY.value, reason
            else:
                reason = f"[1280/26] UVXY strong pop + SPY weak -> Equity opportunity"
                return 'SPXL', ActionType.BUY.value, reason
        
        # Oversold checks with tighter thresholds
        oversold_checks = [
            ('TQQQ', 28, 'TECL'),   # Tighter threshold
            ('SOXL', 28, 'SOXL'), 
            ('SPXL', 28, 'SPXL'),
            ('LABU', 23, 'LABU')    # Tighter threshold
        ]
        
        for check_symbol, threshold, target_symbol in oversold_checks:
            if self._check_rsi_threshold(indicators, check_symbol, 10, threshold, above=False):
                reason = f"[1280/26] {check_symbol} deeply oversold (RSI={self._get_rsi_value(indicators, check_symbol, 10):.1f} < {threshold})"
                return target_symbol, ActionType.BUY.value, reason
        
        # KMLM Switcher with slight modification
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi + 2:  # Require stronger signal
            reason = f"[1280/26] Strong tech leadership (XLK {xlk_rsi:.1f} >> KMLM {kmlm_rsi:.1f})"
            return 'TECL', ActionType.BUY.value, reason
        elif kmlm_rsi > xlk_rsi + 2:
            reason = f"[1280/26] Strong materials leadership -> Defensive"
            return 'KMLM', ActionType.BUY.value, reason
        else:
            reason = f"[1280/26] Neutral positioning -> Low volatility"
            return 'FTLS', ActionType.BUY.value, reason


class KLMVariant1200_28(BaseKLMVariant):
    """1200/28 KMLM - Another parameter configuration"""
    
    def __init__(self):
        super().__init__()
        self.description = "Alternative parameter configuration focusing on momentum"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 1200/28 variant: Focus on momentum and trend following
        """
        
        # Check for extreme overbought with scale-in approach
        scale_in_symbols = ['SPY', 'QQQ', 'IOO', 'VTV', 'XLP', 'RETL']
        scale_in_base = [80, 79, 80, 79, 77, 82]
        scale_in_extreme = [82.5, 82.5, 82.5, 85, 85, 85]
        
        for i, symbol in enumerate(scale_in_symbols):
            rsi_val = self._get_rsi_value(indicators, symbol, 10)
            
            if rsi_val > scale_in_extreme[i]:
                reason = f"[1200/28] {symbol} extremely overbought (RSI={rsi_val:.1f})"
                reason += f" -> VIX Blend++ (double UVXY allocation)"
                return {'UVXY': 0.67, 'VIXM': 0.33}, ActionType.BUY.value, reason
            elif rsi_val > scale_in_base[i]:
                reason = f"[1200/28] {symbol} overbought (RSI={rsi_val:.1f})"
                reason += f" -> VIX Blend+ positioning"
                return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        
        # SPY RSI(70) check for long-term positioning
        spy_rsi_70 = self._get_rsi_value(indicators, 'SPY', 70)
        if spy_rsi_70 > 63:
            reason = f"[1200/28] SPY long-term overbought (RSI70={spy_rsi_70:.1f})"
            return 'VIXY', ActionType.BUY.value, reason
        
        # QQQ multi-timeframe checks
        qqq_rsi_90 = self._get_rsi_value(indicators, 'QQQ', 90) if 'QQQ' in indicators else 50
        qqq_rsi_14 = self._get_rsi_value(indicators, 'QQQ', 14) if 'QQQ' in indicators else 50
        qqq_rsi_5 = self._get_rsi_value(indicators, 'QQQ', 5) if 'QQQ' in indicators else 50
        qqq_rsi_3 = self._get_rsi_value(indicators, 'QQQ', 3) if 'QQQ' in indicators else 50
        
        if qqq_rsi_90 > 60:
            reason = f"[1200/28] QQQ long-term momentum (RSI90={qqq_rsi_90:.1f}) -> VIX hedge"
            return 'VIXY', ActionType.BUY.value, reason
        elif qqq_rsi_14 > 80:
            reason = f"[1200/28] QQQ short-term overbought (RSI14={qqq_rsi_14:.1f})"
            return 'VIXY', ActionType.BUY.value, reason
        elif qqq_rsi_5 > 90:
            reason = f"[1200/28] QQQ very short-term extreme (RSI5={qqq_rsi_5:.1f})"
            return 'VIXY', ActionType.BUY.value, reason
        elif qqq_rsi_3 > 95:
            reason = f"[1200/28] QQQ ultra short-term extreme (RSI3={qqq_rsi_3:.1f})"
            return 'VIXY', ActionType.BUY.value, reason
        
        # AGG vs QQQ comparison for regime detection
        agg_rsi_15 = self._get_rsi_value(indicators, 'AGG', 15) if 'AGG' in indicators else 50
        qqq_rsi_15 = self._get_rsi_value(indicators, 'QQQ', 15) if 'QQQ' in indicators else 50
        
        if agg_rsi_15 > qqq_rsi_15:
            # Bonds stronger than stocks -> Risk-on
            tech_basket = {'TQQQ': 0.2, 'SPXL': 0.2, 'SOXL': 0.2, 'FNGU': 0.2, 'ERX': 0.2}
            reason = f"[1200/28] Bonds > Stocks (AGG RSI15={agg_rsi_15:.1f} > QQQ={qqq_rsi_15:.1f})"
            reason += f" -> All 3x Tech allocation"
            return tech_basket, ActionType.BUY.value, reason
        else:
            # Commodities positioning
            commodities = {'GLD': 0.5, 'SLV': 0.25, 'PDBC': 0.25}
            reason = f"[1200/28] Stocks > Bonds -> Commodities positioning"
            return commodities, ActionType.BUY.value, reason


class KLMVariant520_22(BaseKLMVariant):
    """520/22 KMLM - "Original" baseline variant"""
    
    def __init__(self):
        super().__init__()
        self.description = "Original baseline configuration"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 520/22 variant: The "original" baseline implementation
        """
        
        # Simple overbought detection
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [79, 79, 79, 79, 79, 79, 75]
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[520/22-Original] {symbol} overbought (RSI={self._get_rsi_value(indicators, symbol, 10):.1f})"
                return 'UVXY', ActionType.BUY.value, reason
        
        # UVXY pop check
        uvxy_rsi_21 = self._get_rsi_value(indicators, 'UVXY', 21)
        if uvxy_rsi_21 > 65:
            spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
            if spy_rsi_21 > 30:
                reason = f"[520/22-Original] UVXY popped + SPY strong -> VIXM"
                return 'VIXM', ActionType.BUY.value, reason
            else:
                reason = f"[520/22-Original] UVXY popped + SPY weak -> SPXL"
                return 'SPXL', ActionType.BUY.value, reason
        
        # Combined Pop Bot - original thresholds
        if self._check_rsi_threshold(indicators, 'TQQQ', 10, 30, above=False):
            reason = f"[520/22-Original] TQQQ oversold -> TECL"
            return 'TECL', ActionType.BUY.value, reason
        
        if self._check_rsi_threshold(indicators, 'SOXL', 10, 30, above=False):
            reason = f"[520/22-Original] SOXL oversold -> SOXL"
            return 'SOXL', ActionType.BUY.value, reason
        
        if self._check_rsi_threshold(indicators, 'SPXL', 10, 30, above=False):
            reason = f"[520/22-Original] SPXL oversold -> SPXL"
            return 'SPXL', ActionType.BUY.value, reason
        
        if self._check_rsi_threshold(indicators, 'LABU', 10, 25, above=False):
            reason = f"[520/22-Original] LABU oversold -> LABU"
            return 'LABU', ActionType.BUY.value, reason
        
        # KMLM Switcher - original logic
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi:
            # Tech stronger -> pick lowest RSI between TECL and SVIX
            tecl_rsi = self._get_rsi_value(indicators, 'TECL', 10)
            svix_rsi = self._get_rsi_value(indicators, 'SVIX', 10)
            
            if tecl_rsi < svix_rsi:
                reason = f"[520/22-Original] Tech leading, TECL cheaper (RSI={tecl_rsi:.1f})"
                return 'TECL', ActionType.BUY.value, reason
            else:
                reason = f"[520/22-Original] Tech leading, SVIX cheaper (RSI={svix_rsi:.1f})"
                return 'SVIX', ActionType.BUY.value, reason
        else:
            # Materials stronger -> defensive
            defensive_options = ['SQQQ', 'TLT']
            sqqq_rsi = self._get_rsi_value(indicators, 'SQQQ', 10)
            tlt_rsi = self._get_rsi_value(indicators, 'TLT', 10)
            
            if sqqq_rsi > tlt_rsi:
                reason = f"[520/22-Original] Materials leading, TLT defensive (RSI={tlt_rsi:.1f})"
                return 'TLT', ActionType.BUY.value, reason
            else:
                reason = f"[520/22-Original] Materials leading, SQQQ defensive (RSI={sqqq_rsi:.1f})"
                return 'SQQQ', ActionType.BUY.value, reason


class KLMVariant530_18(BaseKLMVariant):
    """530/18 - Scale-In strategy (most complex)"""
    
    def __init__(self):
        super().__init__()
        self.description = "Scale-In strategy with progressive VIX allocation"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 530/18 variant: Complex scale-in approach with progressive allocation
        """
        
        # Progressive scale-in for SPY
        spy_rsi = self._get_rsi_value(indicators, 'SPY', 10)
        
        if spy_rsi > 82.5:
            reason = f"[530/18-ScaleIn] SPY extremely overbought (RSI={spy_rsi:.1f})"
            reason += f" -> VIX Blend++ (concentrated UVXY)"
            return {'UVXY': 0.67, 'VIXM': 0.33}, ActionType.BUY.value, reason
        elif spy_rsi > 80:
            reason = f"[530/18-ScaleIn] SPY overbought (RSI={spy_rsi:.1f})"
            reason += f" -> VIX Blend+ scale-in"
            return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        
        # Progressive scale-in for QQQ
        qqq_rsi = self._get_rsi_value(indicators, 'QQQ', 10)
        
        if qqq_rsi > 82.5:
            reason = f"[530/18-ScaleIn] QQQ extremely overbought (RSI={qqq_rsi:.1f})"
            return {'UVXY': 0.67, 'VIXM': 0.33}, ActionType.BUY.value, reason
        elif qqq_rsi > 79:
            reason = f"[530/18-ScaleIn] QQQ overbought (RSI={qqq_rsi:.1f})"
            return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        
        # Progressive scale-in for VTV
        vtv_rsi = self._get_rsi_value(indicators, 'VTV', 10)
        
        if vtv_rsi > 85:
            reason = f"[530/18-ScaleIn] VTV extremely overbought (RSI={vtv_rsi:.1f})"
            return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        elif vtv_rsi > 81:
            reason = f"[530/18-ScaleIn] VTV overbought (RSI={vtv_rsi:.1f})"
            return {'VIXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        
        # Progressive scale-in for XLP
        xlp_rsi = self._get_rsi_value(indicators, 'XLP', 10)
        
        if xlp_rsi > 85:
            reason = f"[530/18-ScaleIn] XLP extremely overbought (RSI={xlp_rsi:.1f})"
            return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        elif xlp_rsi > 77:
            reason = f"[530/18-ScaleIn] XLP overbought (RSI={xlp_rsi:.1f})"
            return {'UVXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        
        # Progressive scale-in for RETL
        retl_rsi = self._get_rsi_value(indicators, 'RETL', 10)
        
        if retl_rsi > 85:
            reason = f"[530/18-ScaleIn] RETL extremely overbought (RSI={retl_rsi:.1f})"
            return {'VIXY': 0.33, 'VXX': 0.33, 'VIXM': 0.34}, ActionType.BUY.value, reason
        elif retl_rsi > 82:
            reason = f"[530/18-ScaleIn] RETL overbought (RSI={retl_rsi:.1f})"
            return {'BTAL': 0.5, 'BIL': 0.5}, ActionType.BUY.value, reason
        
        # SPY RSI(70) long-term check
        spy_rsi_70 = self._get_rsi_value(indicators, 'SPY', 70)
        if spy_rsi_70 > 63:
            reason = f"[530/18-ScaleIn] SPY long-term overbought (RSI70={spy_rsi_70:.1f})"
            return 'VIXY', ActionType.BUY.value, reason
        
        # No overbought conditions -> Look for oversold opportunities
        if self._check_rsi_threshold(indicators, 'QQQ', 10, 31, above=False):
            reason = f"[530/18-ScaleIn] QQQ oversold -> TECL"
            return 'TECL', ActionType.BUY.value, reason
        
        if self._check_rsi_threshold(indicators, 'SPY', 10, 30, above=False):
            reason = f"[530/18-ScaleIn] SPY oversold -> UPRO"
            return 'UPRO', ActionType.BUY.value, reason
        
        # Default to low volatility positioning
        reason = f"[530/18-ScaleIn] No extremes detected -> Low volatility positioning"
        return 'FTLS', ActionType.BUY.value, reason


class KLMVariant410_38(BaseKLMVariant):
    """410/38 - MonkeyBusiness Simons variant"""
    
    def __init__(self):
        super().__init__()
        self.description = "MonkeyBusiness Simons variant with enhanced logic"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 410/38 variant: MonkeyBusiness Simons approach
        """
        
        # Standard overbought checks
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [79, 79, 79, 79, 79, 79, 75]
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[410/38-MonkeyBiz] {symbol} overbought (RSI={self._get_rsi_value(indicators, symbol, 10):.1f})"
                return 'UVXY', ActionType.BUY.value, reason
        
        # Enhanced UVXY check with different threshold
        uvxy_rsi_21 = self._get_rsi_value(indicators, 'UVXY', 21)
        if uvxy_rsi_21 > 65:
            spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
            if spy_rsi_21 > 30:
                return 'VIXM', ActionType.BUY.value, f"[410/38-MonkeyBiz] UVXY popped + SPY strong"
            else:
                return 'SPXL', ActionType.BUY.value, f"[410/38-MonkeyBiz] UVXY popped + SPY weak"
        
        # Combined Pop Bot with MonkeyBusiness modifications
        pop_checks = [
            ('TQQQ', 30, 'TECL'),
            ('SOXL', 30, 'SOXL'),
            ('SPXL', 30, 'SPXL'),
            ('LABU', 25, 'LABU')
        ]
        
        for check_symbol, threshold, target in pop_checks:
            if self._check_rsi_threshold(indicators, check_symbol, 10, threshold, above=False):
                reason = f"[410/38-MonkeyBiz] {check_symbol} oversold pop -> {target}"
                return target, ActionType.BUY.value, reason
        
        # Enhanced KMLM Switcher with FNGU integration
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi:
            # Tech stronger - MonkeyBusiness logic with FNGU
            fngu_rsi = self._get_rsi_value(indicators, 'FNGU', 10)
            tecl_rsi = self._get_rsi_value(indicators, 'TECL', 10)
            svix_rsi = self._get_rsi_value(indicators, 'SVIX', 10)
            
            # Find lowest RSI among tech options
            tech_options = [('FNGU', fngu_rsi), ('TECL', tecl_rsi), ('SVIX', svix_rsi)]
            best_tech = min(tech_options, key=lambda x: x[1])
            
            reason = f"[410/38-MonkeyBiz] Tech leading (XLK={xlk_rsi:.1f} > KMLM={kmlm_rsi:.1f})"
            reason += f" -> {best_tech[0]} (RSI={best_tech[1]:.1f})"
            return best_tech[0], ActionType.BUY.value, reason
        else:
            # Materials stronger -> Long/Short rotator
            rotator_options = ['FTLS', 'KMLM', 'UUP']
            min_volatility = float('inf')
            best_rotator = 'FTLS'
            
            for option in rotator_options:
                # Use RSI as proxy for volatility (lower RSI = lower volatility)
                vol_proxy = self._get_rsi_value(indicators, option, 10)
                if vol_proxy < min_volatility:
                    min_volatility = vol_proxy
                    best_rotator = option
            
            reason = f"[410/38-MonkeyBiz] Materials leading -> Low volatility rotator ({best_rotator})"
            return best_rotator, ActionType.BUY.value, reason


class KLMVariantNova(BaseKLMVariant):
    """Nerfed 2900/8 - Nova - Short BT optimization"""
    
    def __init__(self):
        super().__init__()
        self.description = "Nova variant optimized for short backtests"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate Nova variant: Optimized for short-term performance
        """
        
        # Aggressive overbought detection
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [77, 77, 77, 77, 77, 77, 73]  # Lower thresholds for faster signals
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[Nova-ShortBT] {symbol} overbought (RSI={self._get_rsi_value(indicators, symbol, 10):.1f})"
                reason += f" -> Aggressive VIX positioning"
                return 'UVXY', ActionType.BUY.value, reason
        
        # Faster UVXY response
        uvxy_rsi_21 = self._get_rsi_value(indicators, 'UVXY', 21)
        if uvxy_rsi_21 > 60:  # Lower threshold for faster response
            spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
            if spy_rsi_21 > 28:  # Lower threshold
                return 'VIXM', ActionType.BUY.value, f"[Nova-ShortBT] Fast UVXY response + SPY"
            else:
                return 'SPXL', ActionType.BUY.value, f"[Nova-ShortBT] Fast UVXY response - SPY"
        
        # Aggressive oversold detection
        aggressive_oversold = [
            ('TQQQ', 35, 'TECL'),   # Higher threshold for faster signals
            ('SOXL', 35, 'SOXL'),
            ('SPXL', 35, 'SPXL'),
            ('LABU', 30, 'LABU')
        ]
        
        for check_symbol, threshold, target in aggressive_oversold:
            if self._check_rsi_threshold(indicators, check_symbol, 10, threshold, above=False):
                reason = f"[Nova-ShortBT] {check_symbol} early oversold signal -> {target}"
                return target, ActionType.BUY.value, reason
        
        # Quick KMLM Switcher
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi:
            # Tech preferred -> Quick TECL allocation
            reason = f"[Nova-ShortBT] Quick tech signal (XLK={xlk_rsi:.1f} > KMLM={kmlm_rsi:.1f})"
            return 'TECL', ActionType.BUY.value, reason
        else:
            # Quick defensive
            reason = f"[Nova-ShortBT] Quick defensive signal"
            return 'BIL', ActionType.BUY.value, reason


class KLMVariant830_21(BaseKLMVariant):
    """830/21 - MonkeyBusiness Simons variant V2"""
    
    def __init__(self):
        super().__init__()
        self.description = "MonkeyBusiness Simons V2 with enhanced selectivity"
    
    def evaluate(self, indicators: Dict[str, Dict[str, float]], 
                market_data: Dict[str, pd.DataFrame]) -> Tuple[Union[str, Dict[str, float]], str, str]:
        """
        Evaluate 830/21 variant: Enhanced MonkeyBusiness approach
        """
        
        # Standard overbought checks
        overbought_symbols = ['QQQE', 'VTV', 'VOX', 'TECL', 'VOOG', 'VOOV', 'XLP']
        overbought_thresholds = [79, 79, 79, 79, 79, 79, 75]
        
        for symbol, threshold in zip(overbought_symbols, overbought_thresholds):
            if self._check_rsi_threshold(indicators, symbol, 10, threshold, above=True):
                reason = f"[830/21-MonkeyBizV2] {symbol} overbought -> VIX"
                return 'UVXY', ActionType.BUY.value, reason
        
        # Enhanced UVXY logic with different symbol
        uvix_rsi_21 = self._get_rsi_value(indicators, 'UVIX', 21)  # Using UVIX instead of UVXY
        if uvix_rsi_21 > 65:
            spy_rsi_21 = self._get_rsi_value(indicators, 'SPY', 21)
            if spy_rsi_21 > 30:
                return 'VIXM', ActionType.BUY.value, f"[830/21-MonkeyBizV2] UVIX popped + SPY strong"
            else:
                return 'SPXL', ActionType.BUY.value, f"[830/21-MonkeyBizV2] UVIX popped + SPY weak"
        
        # Combined Pop Bot
        if self._check_rsi_threshold(indicators, 'TQQQ', 10, 30, above=False):
            return 'TECL', ActionType.BUY.value, f"[830/21-MonkeyBizV2] TQQQ oversold"
        
        if self._check_rsi_threshold(indicators, 'SOXL', 10, 30, above=False):
            return 'SOXL', ActionType.BUY.value, f"[830/21-MonkeyBizV2] SOXL oversold"
        
        if self._check_rsi_threshold(indicators, 'SPXL', 10, 30, above=False):
            return 'SPXL', ActionType.BUY.value, f"[830/21-MonkeyBizV2] SPXL oversold"
        
        # Enhanced KMLM Switcher with top selection logic
        xlk_rsi = self._get_rsi_value(indicators, 'XLK', 10)
        kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
        
        if xlk_rsi > kmlm_rsi:
            # Tech stronger -> Enhanced selection logic
            tech_options = ['TECL', 'SOXL', 'SVIX']
            
            # Calculate moving average returns (if available) for selection
            # For now, use RSI as proxy for momentum
            tech_scores = []
            for tech in tech_options:
                tech_rsi = self._get_rsi_value(indicators, tech, 10)
                # Higher RSI = better momentum for selection
                tech_scores.append((tech, tech_rsi))
            
            # Select top performer
            best_tech = max(tech_scores, key=lambda x: x[1])
            
            reason = f"[830/21-MonkeyBizV2] Tech leading, {best_tech[0]} selected (RSI={best_tech[1]:.1f})"
            return best_tech[0], ActionType.BUY.value, reason
        else:
            # Materials stronger -> Bond check and defensive selection
            bnd_ma_return = indicators.get('BND', {}).get('ma_return_20', 0)
            
            if bnd_ma_return > 0:
                # Bonds positive -> Low volatility selection
                low_vol_options = ['KMLM', 'SPLV']
                kmlm_rsi = self._get_rsi_value(indicators, 'KMLM', 10)
                splv_rsi = self._get_rsi_value(indicators, 'SPLV', 10)
                
                if kmlm_rsi < splv_rsi:
                    return 'KMLM', ActionType.BUY.value, f"[830/21-MonkeyBizV2] Bonds positive, KMLM selected"
                else:
                    return 'SPLV', ActionType.BUY.value, f"[830/21-MonkeyBizV2] Bonds positive, SPLV selected"
            else:
                # Bonds negative -> Defensive bonds
                bond_options = ['TLT', 'SQQQ']
                tlt_rsi = self._get_rsi_value(indicators, 'TLT', 10)
                sqqq_rsi = self._get_rsi_value(indicators, 'SQQQ', 10)
                
                if tlt_rsi > sqqq_rsi:
                    return 'TLT', ActionType.BUY.value, f"[830/21-MonkeyBizV2] Bonds negative, TLT selected"
                else:
                    return 'SQQQ', ActionType.BUY.value, f"[830/21-MonkeyBizV2] Bonds negative, SQQQ selected"
