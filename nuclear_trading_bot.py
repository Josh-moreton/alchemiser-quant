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
        logging.FileHandler('nuclear_alerts.log'),
        logging.StreamHandler()
    ]
)

class Alert:
    """Simple alert class"""
    def __init__(self, symbol, action, confidence, reason, timestamp, price):
        self.symbol = symbol
        self.action = action
        self.confidence = confidence
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
    
    def get_best_nuclear_stocks(self, indicators, top_n=3):
        """Get top performing nuclear stocks based on 90-day moving average return"""
        nuclear_performance = []
        
        for symbol in self.nuclear_symbols:
            if symbol in indicators:
                performance = indicators[symbol]['ma_return_90']
                nuclear_performance.append((symbol, performance))
        
        # Sort by performance and get top N
        nuclear_performance.sort(key=lambda x: x[1], reverse=True)
        top_stocks = [stock[0] for stock in nuclear_performance[:top_n]]
        
        if not top_stocks:
            # Default to first available nuclear stocks
            available = [s for s in self.nuclear_symbols if s in indicators]
            top_stocks = available[:top_n] if available else ['SMR']
        
        return top_stocks
    
    def evaluate_nuclear_strategy(self, indicators):
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
            return self._evaluate_normal_conditions(indicators)
    
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
        
        # Default to UVXY 75% + BTAL 25% allocation (simplified to UVXY)
        return 'UVXY', 'BUY', "Market overbought, volatility protection mode"
    
    def _evaluate_normal_conditions(self, indicators):
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
        return self._evaluate_main_trading_logic(indicators)
    
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
        
        # Default to UVXY protection
        return 'UVXY', 'BUY', f"{overbought_symbol} overbought, protective positioning"
    
    def _evaluate_vox_overbought(self, indicators):
        """Handle when VOX (communications) is overbought"""
        
        # Check XLF for extreme overbought
        if 'XLF' in indicators and indicators['XLF']['rsi_10'] > 81:
            return 'UVXY', 'BUY', "XLF extremely overbought"
        
        # Default to UVXY protection
        return 'UVXY', 'BUY', "VOX overbought, protective positioning"
    
    def _evaluate_main_trading_logic(self, indicators):
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
                # Bull market - go with nuclear energy portfolio
                top_nuclear = self.get_best_nuclear_stocks(indicators, top_n=1)
                if top_nuclear:
                    nuclear_symbol = top_nuclear[0]
                    return nuclear_symbol, 'BUY', f"Bull market - top nuclear stock: {nuclear_symbol}"
                else:
                    return 'SMR', 'BUY', "Bull market - default nuclear energy play"
            else:
                # Bear market - evaluate bear market logic
                return self._evaluate_bear_market_logic(indicators)
        
        # Default fallback
        return 'SPY', 'HOLD', "No clear signal, holding cash equivalent"
    
    def _evaluate_bear_market_logic(self, indicators):
        """Handle bear market conditions (SPY below 200-day MA)"""
        
        # Check PSQ RSI for oversold bear ETF
        if 'PSQ' in indicators and indicators['PSQ']['rsi_10'] < 35:
            return 'SQQQ', 'BUY', "PSQ oversold, aggressive short position"
        
        # Check QQQ 60-day performance
        if 'QQQ' in indicators and indicators['QQQ']['cum_return_60'] < -10:
            # QQQ down more than 10% in 60 days - check bond vs PSQ strength
            if self._bonds_stronger_than_psq(indicators):
                return 'TQQQ', 'BUY', "Bonds strong vs PSQ, contrarian TQQQ buy"
            else:
                return 'PSQ', 'BUY', "QQQ weak, defensive short position"
        
        # Check TQQQ trend
        if 'TQQQ' in indicators:
            tqqq_price = indicators['TQQQ']['current_price']
            tqqq_ma_20 = indicators['TQQQ']['ma_20']
            
            if tqqq_price > tqqq_ma_20:
                # TQQQ above 20-day MA
                if self._bonds_stronger_than_psq(indicators):
                    return 'TQQQ', 'BUY', "TQQQ trending up, bonds strong"
                else:
                    return 'SQQQ', 'BUY', "TQQQ up but bonds weak, short position"
            else:
                # TQQQ below 20-day MA
                if self._ief_stronger_than_psq(indicators):
                    return 'SQQQ', 'BUY', "TQQQ weak, IEF strong, short position"
                elif self._bonds_stronger_than_psq(indicators):
                    return 'QQQ', 'BUY', "TQQQ weak but bonds strong, neutral QQQ"
                else:
                    return 'SQQQ', 'BUY', "TQQQ weak, bonds weak, short position"
        
        # Default bear market position
        return 'SQQQ', 'BUY', "Bear market conditions, short tech"
    
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
                    "min_confidence": 0.6,
                    "cooldown_minutes": 30
                }
            }
    
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
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators)
        
        # Get current price
        current_price = self.strategy.data_provider.get_current_price(symbol)
        
        # Create alert (no confidence score - pure strategy decision)
        alert = Alert(
            symbol=symbol,
            action=action,
            confidence=1.0,  # Always 100% since it's a deterministic strategy
            reason=reason,
            timestamp=dt.datetime.now(),
            price=current_price
        )
        
        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alert
    
    def log_alert(self, alert):
        """Log alert to file"""
        alert_data = {
            'timestamp': alert.timestamp.isoformat(),
            'symbol': alert.symbol,
            'action': alert.action,
            'price': alert.price,
            'confidence': alert.confidence,
            'reason': alert.reason
        }
        
        try:
            with open('nuclear_alerts.json', 'a') as f:
                f.write(json.dumps(alert_data) + '\n')
        except Exception as e:
            logging.error(f"Failed to log alert: {e}")
    
    def run_once(self):
        """Run analysis once"""
        alert = self.run_analysis()
        
        if alert:
            # Always log the alert
            self.log_alert(alert)
            
            # Display result
            if alert.action != 'HOLD':
                print(f"🚨 NUCLEAR TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                print(f"   Reason: {alert.reason}")
                print(f"   [Deterministic Strategy - No Confidence Scoring]")
            else:
                print(f"📊 Nuclear Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                print(f"   Reason: {alert.reason}")
            
            return alert
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
