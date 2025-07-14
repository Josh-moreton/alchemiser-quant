#!/usr/bin/env python3
"""
Nuclear Energy Trading Alert Bot
Based on the "Nuclear Energy with Feaver Frontrunner V5" Composer.trade strategy

This strategy focuses on:
1. Market regime detection via RSI levels
2. Volatility protection with UVXY
3. Nuclear energy stocks in bull markets
4. Tech/bond dynamics in bear markets
"""

import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import json
import logging
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/nuclear_alerts.log'),
        logging.StreamHandler()
    ]
)

class Alert:
    """Simple alert class"""
    def __init__(self, symbol, action, reason, timestamp, price):
        self.symbol = symbol
        self.action = action
        self.reason = reason
        self.timestamp = timestamp
        self.price = price

class TechnicalIndicators:
    """Calculate technical indicators"""
    
    @staticmethod
    def rsi(data, window=14):
        """Calculate RSI"""
        try:
            delta = data.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(data), index=data.index)
    
    @staticmethod
    def moving_average(data, window):
        """Calculate moving average"""
        try:
            return data.rolling(window=window).mean()
        except:
            return data
    
    @staticmethod
    def moving_average_return(data, window):
        """Calculate moving average return"""
        try:
            returns = data.pct_change()
            return returns.rolling(window=window).mean() * 100
        except:
            return pd.Series([0] * len(data), index=data.index)
    
    @staticmethod
    def cumulative_return(data, window):
        """Calculate cumulative return over window"""
        try:
            return ((data / data.shift(window)) - 1) * 100
        except:
            return pd.Series([0] * len(data), index=data.index)

class DataProvider:
    """Fetch market data"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def get_data(self, symbol, period="1y"):
        """Get historical data with caching"""
        cache_key = f"{symbol}_{period}"
        current_time = dt.datetime.now()
        
        if (cache_key in self.cache and 
            (current_time - self.cache[cache_key]['timestamp']).seconds < self.cache_duration):
            return self.cache[cache_key]['data']
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                # Flatten the column MultiIndex if it exists
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [col[0] for col in data.columns]
                
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': current_time
                }
                return data
            else:
                logging.warning(f"No data found for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """Get current price"""
        data = self.get_data(symbol, period="5d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return 0.0

class NuclearStrategyEngine:
    """Nuclear Energy Strategy Engine"""
    
    def __init__(self):
        self.data_provider = DataProvider()
        self.indicators = TechnicalIndicators()
        
        # Core symbols from the Nuclear strategy
        self.market_symbols = ['SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX']
        self.volatility_symbols = ['UVXY', 'BTAL']
        self.tech_symbols = ['QQQ', 'SQQQ', 'PSQ', 'UPRO']
        self.bond_symbols = ['TLT', 'IEF']
        
        # Nuclear energy stocks (the core of this strategy)
        self.nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
        
        # All symbols
        self.all_symbols = (self.market_symbols + self.volatility_symbols + 
                           self.tech_symbols + self.bond_symbols + self.nuclear_symbols)
    
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
        """Safely get indicator value"""
        try:
            result = indicator_func(data, *args, **kwargs)
            if hasattr(result, 'iloc') and len(result) > 0:
                value = float(result.iloc[-1])
                return value if not pd.isna(value) else 50.0
            return 50.0
        except:
            return 50.0
    
    def calculate_indicators(self, market_data):
        """Calculate all technical indicators"""
        indicators = {}
        
        for symbol, df in market_data.items():
            if df.empty:
                continue
                
            close = df['Close']
            indicators[symbol] = {
                'rsi_10': self.safe_get_indicator(close, self.indicators.rsi, 10),
                'rsi_20': self.safe_get_indicator(close, self.indicators.rsi, 20),
                'ma_200': self.safe_get_indicator(close, self.indicators.moving_average, 200),
                'ma_20': self.safe_get_indicator(close, self.indicators.moving_average, 20),
                'ma_return_90': self.safe_get_indicator(close, self.indicators.moving_average_return, 90),
                'cum_return_60': self.safe_get_indicator(close, self.indicators.cumulative_return, 60),
                'current_price': float(close.iloc[-1]),
            }
        
        return indicators
    
    def get_nuclear_portfolio(self, indicators, market_data=None):
        """Get nuclear energy portfolio with top 3 stocks and their allocations"""
        nuclear_performance = []
        
        for symbol in self.nuclear_symbols:
            if symbol in indicators:
                performance = indicators[symbol]['ma_return_90']
                nuclear_performance.append((symbol, performance))
        
        # Sort by performance and get top 3
        nuclear_performance.sort(key=lambda x: x[1], reverse=True)
        top_3_stocks = nuclear_performance[:3]
        
        if len(top_3_stocks) < 3:
            # If we don't have 3 stocks, pad with available ones
            available = [s for s in self.nuclear_symbols if s in indicators]
            while len(top_3_stocks) < 3 and len(available) > len(top_3_stocks):
                missing_stock = available[len(top_3_stocks)]
                performance = indicators[missing_stock]['ma_return_90']
                top_3_stocks.append((missing_stock, performance))
        
        # Apply inverse volatility weighting (90-day window as per original strategy)
        if top_3_stocks:
            portfolio = {}
            
            # Calculate 90-day volatility for each stock
            volatilities = []
            for symbol, performance in top_3_stocks:
                # Use price data to calculate volatility
                if market_data and symbol in market_data:
                    price_data = market_data[symbol]['Close']
                    if len(price_data) >= 90:
                        returns = price_data.pct_change().dropna()
                        # Use last 90 days of returns
                        recent_returns = returns.tail(90)
                        # Calculate standard deviation (volatility)
                        volatility_val = recent_returns.std()
                        
                        # Ensure volatility is a scalar
                        if isinstance(volatility_val, pd.Series):
                            volatility_val = volatility_val.iloc[0]
                        
                        # Add minimum volatility floor to avoid division by very small numbers
                        volatility_val = max(volatility_val, 0.001)
                        
                        volatilities.append((symbol, performance, volatility_val))
            
            if volatilities and len(volatilities) == len(top_3_stocks):
                # Calculate inverse volatility weights
                inv_vols = []
                for symbol, performance, vol in volatilities:
                    inv_vol = 1.0 / vol
                    inv_vols.append((symbol, performance, inv_vol))
                
                # Calculate total inverse volatility
                total_inv_vol = sum(inv_vol for _, _, inv_vol in inv_vols)
                
                # Normalize to get portfolio weights
                for symbol, performance, inv_vol in inv_vols:
                    weight = inv_vol / total_inv_vol
                    portfolio[symbol] = {
                        'weight': weight,
                        'performance': performance
                    }
            else:
                # Fallback to equal weighting if volatility calculation fails
                weight_per_stock = 1.0 / len(top_3_stocks)
                for symbol, performance in top_3_stocks:
                    portfolio[symbol] = {
                        'weight': weight_per_stock,
                        'performance': performance
                    }
            
            return portfolio
        else:
            # Default fallback
            return {'SMR': {'weight': 1.0, 'performance': 0.0}}
    
    def get_best_nuclear_stocks(self, indicators, top_n=3):
        """Get top performing nuclear stocks based on 90-day moving average return"""
        portfolio = self.get_nuclear_portfolio(indicators)
        return list(portfolio.keys())[:top_n]
    
    def evaluate_nuclear_strategy(self, indicators, market_data=None):
        """
        Evaluate the Nuclear Energy strategy
        Returns: (recommended_symbol, action, reason)
        """
        
        # Safety check for required data
        if 'SPY' not in indicators:
            return 'SPY', 'HOLD', "Missing SPY data"
        
        spy_rsi_10 = indicators['SPY']['rsi_10']
        
        # Level 1: Check if SPY RSI > 79 (market overbought)
        if spy_rsi_10 > 79:
            return self._evaluate_overbought_conditions(indicators)
        else:
            return self._evaluate_normal_conditions(indicators, market_data)
    
    def _evaluate_overbought_conditions(self, indicators):
        """Handle overbought market conditions (SPY RSI > 79)"""
        
        spy_rsi_10 = indicators['SPY']['rsi_10']
        
        # If SPY RSI > 81, definitely go to UVXY
        if spy_rsi_10 > 81:
            return 'UVXY', 'BUY', "SPY extremely overbought (RSI > 81)"
        
        # Check other major indices for overbought conditions
        symbols_to_check = ['IOO', 'TQQQ', 'VTV', 'XLF']
        
        for symbol in symbols_to_check:
            if symbol in indicators and indicators[symbol]['rsi_10'] > 81:
                return 'UVXY', 'BUY', f"{symbol} extremely overbought (RSI > 81)"
        
        # Per original strategy: UVXY 75% + BTAL 25% allocation
        # Return as portfolio allocation signal
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', "Market overbought, UVXY 75% + BTAL 25% allocation"
    
    def _evaluate_normal_conditions(self, indicators, market_data=None):
        """Handle normal market conditions (SPY RSI <= 79)"""
        
        # Check each major index for overbought (but not extreme) conditions
        if 'IOO' in indicators and indicators['IOO']['rsi_10'] > 79:
            return self._evaluate_secondary_overbought(indicators, 'IOO')
        
        if 'TQQQ' in indicators and indicators['TQQQ']['rsi_10'] > 79:
            return self._evaluate_secondary_overbought(indicators, 'TQQQ')
        
        if 'VTV' in indicators and indicators['VTV']['rsi_10'] > 79:
            return self._evaluate_secondary_overbought(indicators, 'VTV')
        
        if 'XLF' in indicators and indicators['XLF']['rsi_10'] > 79:
            return self._evaluate_secondary_overbought(indicators, 'XLF')
        
        if 'VOX' in indicators and indicators['VOX']['rsi_10'] > 79:
            return self._evaluate_vox_overbought(indicators)
        
        # If nothing is overbought, evaluate main trading logic
        return self._evaluate_main_trading_logic(indicators, market_data)
    
    def _evaluate_secondary_overbought(self, indicators, overbought_symbol):
        """Handle when a secondary index is overbought"""
        
        # Check if the overbought symbol is extremely overbought (>81)
        if indicators[overbought_symbol]['rsi_10'] > 81:
            return 'UVXY', 'BUY', f"{overbought_symbol} extremely overbought"
        
        # Continue checking other symbols for extreme overbought
        other_symbols = ['TQQQ', 'VTV', 'XLF']
        for symbol in other_symbols:
            if symbol != overbought_symbol and symbol in indicators:
                if indicators[symbol]['rsi_10'] > 81:
                    return 'UVXY', 'BUY', f"{symbol} extremely overbought"
        
        # Default to UVXY 75% + BTAL 25% allocation per original strategy
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', f"{overbought_symbol} overbought, UVXY 75% + BTAL 25% allocation"
    
    def _evaluate_vox_overbought(self, indicators):
        """Handle when VOX (communications) is overbought"""
        
        # Check XLF for extreme overbought
        if 'XLF' in indicators and indicators['XLF']['rsi_10'] > 81:
            return 'UVXY', 'BUY', "XLF extremely overbought"
        
        # Default to UVXY 75% + BTAL 25% allocation per original strategy
        return 'UVXY_BTAL_PORTFOLIO', 'BUY', "VOX overbought, UVXY 75% + BTAL 25% allocation"
    
    def _evaluate_main_trading_logic(self, indicators, market_data=None):
        """Main trading logic when no major overbought conditions"""
        
        # Check for TQQQ oversold condition
        if 'TQQQ' in indicators and indicators['TQQQ']['rsi_10'] < 30:
            return 'TQQQ', 'BUY', "TQQQ oversold, buying dip"
        
        # Check for SPY oversold condition  
        if 'SPY' in indicators and indicators['SPY']['rsi_10'] < 30:
            return 'UPRO', 'BUY', "SPY oversold, buying dip with leverage"
        
        # Check SPY trend vs 200-day MA
        if 'SPY' in indicators:
            spy_price = indicators['SPY']['current_price']
            spy_ma_200 = indicators['SPY']['ma_200']
            
            if spy_price > spy_ma_200:
                # Bull market - return nuclear energy portfolio allocation
                nuclear_portfolio = self.get_nuclear_portfolio(indicators, market_data)
                if nuclear_portfolio:
                    # Return the nuclear portfolio allocation (not single stock)
                    portfolio_stocks = list(nuclear_portfolio.keys())
                    portfolio_desc = ", ".join([f"{s} ({nuclear_portfolio[s]['weight']:.1%})" for s in portfolio_stocks])
                    # For compliance with original strategy, return portfolio info as a special signal
                    return 'NUCLEAR_PORTFOLIO', 'BUY', f"Bull market - Nuclear portfolio: {portfolio_desc}"
                else:
                    return 'SMR', 'BUY', "Bull market - default nuclear energy play"
            else:
                # Bear market - evaluate bear market logic
                return self._evaluate_bear_market_logic(indicators)
        
        # Default fallback
        return 'SPY', 'HOLD', "No clear signal, holding cash equivalent"
    
    def _evaluate_bear_market_logic(self, indicators):
        """Handle bear market conditions (SPY below 200-day MA)"""
        
        # In the original strategy, there are two parallel "Bear" sub-strategies
        # that get weighted together with 14-day inverse volatility weighting
        # We need to evaluate both and combine them properly
        
        bear1_signal = self._evaluate_bear_subgroup_1(indicators)
        bear2_signal = self._evaluate_bear_subgroup_2(indicators)
        
        # Get the recommended symbols from each bear strategy
        bear1_symbol = bear1_signal[0]
        bear2_symbol = bear2_signal[0]
        
        # If both bear signals are the same, return that signal with full allocation
        if bear1_symbol == bear2_symbol:
            return bear1_signal
        
        # If different symbols, combine using inverse volatility weighting (14-day window)
        bear_portfolio = self._combine_bear_strategies_with_inverse_volatility(
            bear1_symbol, bear2_symbol, indicators
        )
        
        if bear_portfolio:
            # Format portfolio allocation for display
            portfolio_desc = ", ".join([f"{s} ({bear_portfolio[s]['weight']:.1%})" 
                                      for s in bear_portfolio.keys()])
            return 'BEAR_PORTFOLIO', 'BUY', f"Bear market portfolio: {portfolio_desc}"
        
        # Fallback if volatility calculation fails
        return bear1_signal
    
    def _evaluate_bear_subgroup_1(self, indicators):
        """Bear market sub-strategy 1 (mirrors original 'Bear 1' group)"""
        
        # Check PSQ RSI for oversold bear ETF
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', 'BUY', "PSQ oversold, aggressive short position (Bear 1)"
        
        # Check QQQ 60-day performance
        if 'QQQ' in indicators and indicators['QQQ']['cum_return_60'] < -10:
            # QQQ down more than 10% in 60 days - check bond vs PSQ strength
            if self._bonds_stronger_than_psq(indicators):
                return 'TQQQ', 'BUY', "Bonds strong vs PSQ, contrarian TQQQ buy (Bear 1)"
            else:
                return 'PSQ', 'BUY', "QQQ weak, defensive short position (Bear 1)"
        
        # Check TQQQ trend
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            
            if tqqq_price > tqqq_ma_20:
                # TQQQ above 20-day MA
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', 'BUY', "TQQQ trending up, bonds strong (Bear 1)"
                else:
                    return 'SQQQ', 'BUY', "TQQQ up but bonds weak, short position (Bear 1)"
            else:
                # TQQQ below 20-day MA
                if self._ief_stronger_than_psq(indicators):
                    return 'SQQQ', 'BUY', "TQQQ weak, IEF strong, short position (Bear 1)"
                elif self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', 'BUY', "TQQQ weak but bonds strong, neutral QQQ (Bear 1)"
                else:
                    return 'SQQQ', 'BUY', "TQQQ weak, bonds weak, short position (Bear 1)"
        
        # Default bear market position
        return 'SQQQ', 'BUY', "Bear market conditions, short tech (Bear 1)"
    
    def _evaluate_bear_subgroup_2(self, indicators):
        """Bear market sub-strategy 2 (mirrors original 'Bear 2' group)"""
        
        # Check PSQ RSI for oversold bear ETF
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', 'BUY', "PSQ oversold, aggressive short position (Bear 2)"
        
        # Bear 2 does NOT have the QQQ 60-day check - goes directly to TQQQ trend
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            
            if tqqq_price > tqqq_ma_20:
                # TQQQ above 20-day MA
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', 'BUY', "TQQQ trending up, bonds strong (Bear 2)"
                else:
                    return 'SQQQ', 'BUY', "TQQQ up but bonds weak, short position (Bear 2)"
            else:
                # TQQQ below 20-day MA
                if self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', 'BUY', "TQQQ weak but bonds strong, neutral QQQ (Bear 2)"
                else:
                    return 'SQQQ', 'BUY', "TQQQ weak, bonds weak, short position (Bear 2)"
        
        # Default bear market position
        return 'SQQQ', 'BUY', "Bear market conditions, short tech (Bear 2)"
    
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
    
    def _combine_bear_strategies_with_inverse_volatility(self, bear1_symbol, bear2_symbol, indicators):
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
                    returns = []
                    for i in range(1, len(prices)):
                        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                        returns.append(daily_return)
                    
                    if len(returns) >= 10:  # Need at least 10 daily returns
                        import numpy as np
                        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
                        return max(volatility, 0.01)  # Minimum volatility floor
                
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

class NuclearTradingBot:
    """Nuclear Energy Trading Bot"""
    
    def __init__(self):
        self.strategy = NuclearStrategyEngine()
        self.load_config()
        
    def load_config(self):
        """Load configuration"""
        try:
            with open('alert_config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "alerts": {
                    "cooldown_minutes": 30
                }
            }
    
    def handle_nuclear_portfolio_signal(self, symbol, action, reason, indicators, market_data=None):
        """Handle nuclear portfolio signal by creating individual alerts for each stock"""
        if symbol == 'NUCLEAR_PORTFOLIO' and action == 'BUY':
            # Get the nuclear portfolio
            nuclear_portfolio = self.strategy.get_nuclear_portfolio(indicators, market_data)
            
            # Create alerts for all nuclear stocks in the portfolio
            alerts = []
            for stock_symbol, allocation in nuclear_portfolio.items():
                current_price = self.strategy.data_provider.get_current_price(stock_symbol)
                
                portfolio_reason = f"Nuclear portfolio allocation: {allocation['weight']:.1%} ({reason})"
                
                alert = Alert(
                    symbol=stock_symbol,
                    action=action,
                    reason=portfolio_reason,
                    timestamp=dt.datetime.now(),
                    price=current_price
                )
                alerts.append(alert)
            
            return alerts
            
        elif symbol == 'UVXY_BTAL_PORTFOLIO' and action == 'BUY':
            # Handle UVXY 75% + BTAL 25% allocation
            alerts = []
            
            # UVXY 75%
            uvxy_price = self.strategy.data_provider.get_current_price('UVXY')
            uvxy_alert = Alert(
                symbol='UVXY',
                action=action,
                reason=f"Volatility hedge allocation: 75% ({reason})",
                timestamp=dt.datetime.now(),
                price=uvxy_price
            )
            alerts.append(uvxy_alert)
            
            # BTAL 25%
            btal_price = self.strategy.data_provider.get_current_price('BTAL')
            btal_alert = Alert(
                symbol='BTAL',
                action=action,
                reason=f"Anti-beta hedge allocation: 25% ({reason})",
                timestamp=dt.datetime.now(),
                price=btal_price
            )
            alerts.append(btal_alert)
            
            return alerts
            
        elif symbol == 'BEAR_PORTFOLIO' and action == 'BUY':
            # Handle bear market portfolio with inverse volatility weighting
            alerts = []
            
            # Extract portfolio allocation from reason string
            import re
            portfolio_match = re.findall(r'(\w+) \((\d+\.?\d*)%\)', reason)
            
            if portfolio_match:
                for stock_symbol, allocation_str in portfolio_match:
                    current_price = self.strategy.data_provider.get_current_price(stock_symbol)
                    
                    bear_reason = f"Bear market allocation: {allocation_str}% (inverse volatility weighted)"
                    
                    alert = Alert(
                        symbol=stock_symbol,
                        action=action,
                        reason=bear_reason,
                        timestamp=dt.datetime.now(),
                        price=current_price
                    )
                    alerts.append(alert)
                
                return alerts
            else:
                # Fallback: treat as single stock signal
                current_price = self.strategy.data_provider.get_current_price(symbol)
                alert = Alert(
                    symbol=symbol,
                    action=action,
                    reason=reason,
                    timestamp=dt.datetime.now(),
                    price=current_price
                )
                return [alert]
        else:
            # Single stock signal
            current_price = self.strategy.data_provider.get_current_price(symbol)
            alert = Alert(
                symbol=symbol,
                action=action,
                reason=reason,
                timestamp=dt.datetime.now(),
                price=current_price
            )
            return [alert]
    
    def run_analysis(self):
        """Run complete strategy analysis"""
        logging.info("Starting Nuclear Energy strategy analysis...")
        
        # Get market data
        market_data = self.strategy.get_market_data()
        if not market_data:
            logging.error("No market data available")
            return None
        
        # Calculate indicators
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            logging.error("No indicators calculated")
            return None
        
        # Evaluate strategy
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # Handle nuclear portfolio signal properly
        alerts = self.handle_nuclear_portfolio_signal(symbol, action, reason, indicators, market_data)
        
        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alerts
    
    def log_alert(self, alert):
        """Log alert to file"""
        alert_data = {
            'timestamp': alert.timestamp.isoformat(),
            'symbol': alert.symbol,
            'action': alert.action,
            'price': alert.price,
            'reason': alert.reason
        }
        
        try:
            with open('data/logs/nuclear_alerts.json', 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
        except Exception as e:
            logging.error(f"Failed to log alert: {e}")
    
    def run_once(self):
        """Run analysis once"""
        alerts = self.run_analysis()
        
        if alerts and len(alerts) > 0:
            # Log all alerts
            for alert in alerts:
                self.log_alert(alert)
            
            # Display results
            if len(alerts) > 1:
                # Nuclear portfolio signal
                print(f"🚨 NUCLEAR PORTFOLIO SIGNAL: {len(alerts)} stocks allocated")
                print(f"\n� NUCLEAR PORTFOLIO ALLOCATION:")
                for alert in alerts:
                    if alert.action != 'HOLD':
                        print(f"   🟢 {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
                    else:
                        print(f"   ⚪ {alert.action} {alert.symbol} at ${alert.price:.2f}")
                        print(f"      Reason: {alert.reason}")
                        
                # Show portfolio allocation details
                portfolio = self.get_current_portfolio_allocation()
                if portfolio:
                    print(f"\n� PORTFOLIO DETAILS:")
                    for symbol, data in portfolio.items():
                        print(f"   {symbol}: {data['weight']:.1%}")
            else:
                # Single signal
                alert = alerts[0]
                if alert.action != 'HOLD':
                    print(f"🚨 NUCLEAR TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
                else:
                    print(f"📊 Nuclear Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                    print(f"   Reason: {alert.reason}")
            
            return alerts[0]  # Return first alert for compatibility
        else:
            print("❌ Unable to generate nuclear energy signal")
            return None
    
    def run_continuous(self, interval_minutes=15):
        """Run analysis continuously"""
        import time
        
        logging.info(f"Starting continuous Nuclear Energy analysis (every {interval_minutes} minutes)")
        
        while True:
            try:
                self.run_once()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logging.info("Stopping Nuclear Energy bot...")
                break
            except Exception as e:
                logging.error(f"Error in continuous run: {e}")
                time.sleep(60)
    
    def get_current_portfolio_allocation(self):
        """Get current portfolio allocation for display purposes"""
        # Get market data and indicators
        market_data = self.strategy.get_market_data()
        if not market_data:
            return None
        
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            return None
        
        # Get strategy recommendation
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)
        
        # If we're in a bull market, show the nuclear portfolio
        if 'SPY' in indicators:
            spy_price = indicators['SPY']['current_price']
            spy_ma_200 = indicators['SPY']['ma_200']
            
            if spy_price > spy_ma_200 and action == 'BUY':
                nuclear_portfolio = self.strategy.get_nuclear_portfolio(indicators, market_data)
                if nuclear_portfolio:
                    # Add current prices and market values
                    portfolio_with_prices = {}
                    for symbol, data in nuclear_portfolio.items():
                        if symbol in indicators:
                            current_price = indicators[symbol]['current_price']
                            portfolio_with_prices[symbol] = {
                                'weight': data['weight'],
                                'performance': data['performance'],
                                'current_price': current_price,
                                'market_value': 10000 * data['weight'],  # Assuming $10k portfolio
                                'shares': (10000 * data['weight']) / current_price
                            }
                    return portfolio_with_prices
        
        return None

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nuclear Energy Trading Strategy Alert Bot')
    parser.add_argument('--mode', choices=['once', 'continuous'], default='once',
                       help='Run mode: once or continuous')
    parser.add_argument('--interval', type=int, default=15,
                       help='Interval in minutes for continuous mode')
    
    args = parser.parse_args()
    
    # Create bot
    bot = NuclearTradingBot()
    
    if args.mode == 'once':
        bot.run_once()
    else:
        bot.run_continuous(args.interval)

if __name__ == "__main__":
    main()
