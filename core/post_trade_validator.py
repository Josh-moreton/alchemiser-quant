#!/usr/bin/env python3
"""
Post-Trade Technical Indicator Validator

This module validates technical indicators used in live trading signal evaluation
against external TwelveData API values AFTER trades are executed. This ensures
we don't delay trade execution with API rate limits while still validating
our calculation accuracy.

Only validates indicators actually used in signal generation for both strategies:
- Nuclear Strategy: RSI(10, 20), MA(20, 200), MA Return(90), Cumulative Return(60)
- TECL Strategy: RSI(9, 10), MA(200)

Rate limited to 8 requests/minute (TwelveData free tier limit).
"""

import logging
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from concurrent.futures import ThreadPoolExecutor

from .secrets_manager import SecretsManager
from .indicators import TechnicalIndicators
from .data_provider import UnifiedDataProvider

class PostTradeValidator:
    """Validates technical indicators against TwelveData API after live trades"""
    
    def __init__(self):
        self.base_url = "https://api.twelvedata.com"
        self.api_key = None
        self.secrets_manager = SecretsManager(region_name="eu-west-2")
        self.data_provider = UnifiedDataProvider(paper_trading=False)  # Use live data
        self.indicators_calc = TechnicalIndicators()
        
        # Rate limiting
        self.request_count = 0
        self.last_reset_time = datetime.now()
        self.max_requests_per_minute = 5  # Very conservative for demo (API allows 8)
        self.rate_limit_lock = threading.Lock()
        
        # Strategy-specific indicator configurations
        self.nuclear_indicators = {
            'rsi': [10, 20],      # RSI periods used in Nuclear strategy
            'sma': [20, 200],     # MA periods used in Nuclear strategy
            'custom': ['ma_return_90', 'cum_return_60']  # Custom indicators
        }
        
        self.tecl_indicators = {
            'rsi': [9, 10],       # RSI periods used in TECL strategy  
            'sma': [200],         # MA periods used in TECL strategy
            'custom': []          # No custom indicators in TECL
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _get_api_key(self) -> Optional[str]:
        """Get TwelveData API key from AWS Secrets Manager"""
        if not self.api_key:
            try:
                secrets = self.secrets_manager.get_secret("nuclear-secrets")
                if secrets:
                    self.api_key = secrets.get("TWELVEDATA_KEY")
                if not self.api_key:
                    self.logger.error("TWELVEDATA_KEY not found in nuclear-secrets")
                    return None
            except Exception as e:
                self.logger.error(f"Failed to get API key: {e}")
                return None
        return self.api_key
    
    def _rate_limit_check(self):
        """Enforce rate limiting before API calls"""
        with self.rate_limit_lock:
            current_time = datetime.now()
            
            # Reset counter if more than a minute has passed
            if current_time - self.last_reset_time >= timedelta(minutes=1):
                self.request_count = 0
                self.last_reset_time = current_time
                self.logger.debug(f"Rate limit counter reset at {current_time.strftime('%H:%M:%S')}")
            
            # If at limit, wait until next minute
            if self.request_count >= self.max_requests_per_minute:
                seconds_to_wait = 60 - (current_time - self.last_reset_time).seconds
                if seconds_to_wait > 0:
                    self.logger.info(f"Rate limit reached ({self.request_count}/{self.max_requests_per_minute}). "
                                   f"Waiting {seconds_to_wait} seconds...")
                    time.sleep(seconds_to_wait + 1)
                    self.request_count = 0
                    self.last_reset_time = datetime.now()
    
    def _get_twelvedata_indicator(self, symbol: str, indicator: str, period: int) -> Optional[float]:
        """Get indicator value from TwelveData API with rate limiting"""
        api_key = self._get_api_key()
        if not api_key:
            return None
            
        self._rate_limit_check()
        
        url = f"{self.base_url}/{indicator}"
        params = {
            "symbol": symbol,
            "interval": "1day", 
            "time_period": period,
            "apikey": api_key,
            "outputsize": 1
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            with self.rate_limit_lock:
                self.request_count += 1
            
            try:
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                if "status" in data and data["status"] == "error":
                    error_msg = data.get("message", "Unknown error")
                    if "API call frequency" in error_msg or "run out of API credits" in error_msg:
                        self.logger.warning(f"Rate limit hit for {symbol} {indicator}({period}) - attempt {attempt + 1}")
                        # Force wait and try again
                        with self.rate_limit_lock:
                            self.request_count = self.max_requests_per_minute
                        time.sleep(2)
                        continue
                    else:
                        self.logger.error(f"API Error for {symbol} {indicator}({period}): {error_msg}")
                        return None
                
                if "values" not in data or not data["values"]:
                    self.logger.warning(f"No data for {symbol} {indicator}({period})")
                    return None
                
                latest = data["values"][0]
                return float(latest[indicator])
                
            except Exception as e:
                self.logger.error(f"Request failed for {symbol} {indicator}({period}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
        
        self.logger.error(f"Failed to get {symbol} {indicator}({period}) after {max_retries} attempts")
        return None
    
    def _calculate_our_indicators(self, symbol: str, strategy: str) -> Optional[Dict[str, float]]:
        """Calculate our local indicators for the symbol"""
        try:
            # Get 1 year of data for calculation
            df = self.data_provider.get_data(symbol, period="1y", interval="1d")
            
            if df.empty:
                self.logger.warning(f"No data from data provider for {symbol}")
                return None
            
            close_prices = df['Close']
            indicators = {}
            
            # Get indicator config for this strategy
            if strategy.lower() == 'nuclear':
                config = self.nuclear_indicators
            elif strategy.lower() == 'tecl':
                config = self.tecl_indicators
            else:
                self.logger.error(f"Unknown strategy: {strategy}")
                return None
            
            # Calculate RSI indicators
            for period in config['rsi']:
                rsi = self.indicators_calc.rsi(close_prices, period)
                if not rsi.empty and not rsi.isna().iloc[-1]:
                    indicators[f'rsi_{period}'] = float(rsi.iloc[-1])
                else:
                    indicators[f'rsi_{period}'] = 50.0  # Default fallback
            
            # Calculate moving averages
            for period in config['sma']:
                ma = self.indicators_calc.moving_average(close_prices, period)
                if not ma.empty and not ma.isna().iloc[-1]:
                    indicators[f'ma_{period}'] = float(ma.iloc[-1])
                else:
                    indicators[f'ma_{period}'] = float(close_prices.iloc[-1])  # Default to current price
            
            # Calculate custom indicators for Nuclear strategy
            if strategy.lower() == 'nuclear':
                ma_return_90 = self.indicators_calc.moving_average_return(close_prices, 90)
                if not ma_return_90.empty and not ma_return_90.isna().iloc[-1]:
                    indicators['ma_return_90'] = float(ma_return_90.iloc[-1])
                else:
                    indicators['ma_return_90'] = 0.0
                
                cum_return_60 = self.indicators_calc.cumulative_return(close_prices, 60)
                if not cum_return_60.empty and not cum_return_60.isna().iloc[-1]:
                    indicators['cum_return_60'] = float(cum_return_60.iloc[-1])
                else:
                    indicators['cum_return_60'] = 0.0
            
            # Add current price for reference
            indicators['current_price'] = float(close_prices.iloc[-1])
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            return None
    
    def validate_symbol(self, symbol: str, strategy: str) -> Dict[str, Any]:
        """
        Validate indicators for a single symbol against TwelveData
        Returns validation results dict
        """
        results = {
            'symbol': symbol,
            'strategy': strategy,
            'timestamp': datetime.now(),
            'validations': {},
            'errors': [],
            'status': 'unknown'
        }
        
        try:
            # Calculate our indicators
            our_indicators = self._calculate_our_indicators(symbol, strategy)
            if not our_indicators:
                results['errors'].append(f"Failed to calculate local indicators for {symbol}")
                results['status'] = 'error'
                return results
            
            # Get strategy config
            if strategy.lower() == 'nuclear':
                config = self.nuclear_indicators
            elif strategy.lower() == 'tecl':
                config = self.tecl_indicators
            else:
                results['errors'].append(f"Unknown strategy: {strategy}")
                results['status'] = 'error'
                return results
            
            total_validations = 0
            successful_validations = 0
            
            # Validate RSI indicators
            for period in config['rsi']:
                our_rsi = our_indicators[f'rsi_{period}']
                td_rsi = self._get_twelvedata_indicator(symbol, 'rsi', period)
                
                validation = {
                    'our_value': our_rsi,
                    'twelvedata_value': td_rsi,
                    'difference': None,
                    'status': 'unavailable'
                }
                
                if td_rsi is not None:
                    diff = abs(our_rsi - td_rsi)
                    validation['difference'] = diff
                    
                    if diff < 1.0:
                        validation['status'] = 'excellent'
                    elif diff < 2.0:
                        validation['status'] = 'good'
                    else:
                        validation['status'] = 'warning'
                    
                    successful_validations += 1
                
                results['validations'][f'rsi_{period}'] = validation
                total_validations += 1
            
            # Validate moving averages
            for period in config['sma']:
                our_ma = our_indicators[f'ma_{period}']
                td_ma = self._get_twelvedata_indicator(symbol, 'sma', period)
                
                validation = {
                    'our_value': our_ma,
                    'twelvedata_value': td_ma,
                    'difference': None,
                    'percent_difference': None,
                    'status': 'unavailable'
                }
                
                if td_ma is not None:
                    diff = abs(our_ma - td_ma)
                    pct_diff = (diff / td_ma) * 100
                    validation['difference'] = diff
                    validation['percent_difference'] = pct_diff
                    
                    if pct_diff < 0.1:
                        validation['status'] = 'excellent'
                    elif pct_diff < 0.5:
                        validation['status'] = 'good'
                    else:
                        validation['status'] = 'warning'
                    
                    successful_validations += 1
                
                results['validations'][f'ma_{period}'] = validation
                total_validations += 1
            
            # Add custom indicators (no external validation available)
            if strategy.lower() == 'nuclear':
                results['validations']['ma_return_90'] = {
                    'our_value': our_indicators['ma_return_90'],
                    'status': 'custom_indicator'
                }
                results['validations']['cum_return_60'] = {
                    'our_value': our_indicators['cum_return_60'],
                    'status': 'custom_indicator'
                }
            
            # Set overall status
            if successful_validations == total_validations and total_validations > 0:
                results['status'] = 'success'
            elif successful_validations > 0:
                results['status'] = 'partial'
            else:
                results['status'] = 'failed'
            
            results['current_price'] = our_indicators['current_price']
            
        except Exception as e:
            results['errors'].append(f"Validation failed for {symbol}: {e}")
            results['status'] = 'error'
        
        return results
    
    def validate_strategy_symbols(self, symbols: List[str], strategy: str, 
                                parallel: bool = True) -> Dict[str, Any]:
        """
        Validate indicators for multiple symbols used in a strategy
        Returns comprehensive validation report
        """
        start_time = datetime.now()
        
        report = {
            'strategy': strategy,
            'start_time': start_time,
            'symbols': symbols,
            'results': {},
            'summary': {}
        }
        
        self.logger.info(f"Starting post-trade validation for {strategy} strategy ({len(symbols)} symbols)")
        
        if parallel and len(symbols) > 1:
            # Parallel validation (but still rate-limited)
            with ThreadPoolExecutor(max_workers=2) as executor:  # Limit to 2 workers to respect rate limits
                future_to_symbol = {
                    executor.submit(self.validate_symbol, symbol, strategy): symbol
                    for symbol in symbols
                }
                
                for future in future_to_symbol:
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout per symbol
                        report['results'][symbol] = result
                    except Exception as e:
                        self.logger.error(f"Validation failed for {symbol}: {e}")
                        report['results'][symbol] = {
                            'symbol': symbol,
                            'strategy': strategy,
                            'status': 'error',
                            'errors': [str(e)]
                        }
        else:
            # Sequential validation
            for symbol in symbols:
                try:
                    result = self.validate_symbol(symbol, strategy)
                    report['results'][symbol] = result
                except Exception as e:
                    self.logger.error(f"Validation failed for {symbol}: {e}")
                    report['results'][symbol] = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'status': 'error',
                        'errors': [str(e)]
                    }
        
        # Calculate summary statistics
        end_time = datetime.now()
        total_symbols = len(symbols)
        successful = sum(1 for r in report['results'].values() if r.get('status') == 'success')
        partial = sum(1 for r in report['results'].values() if r.get('status') == 'partial')
        failed = sum(1 for r in report['results'].values() if r.get('status') in ['failed', 'error'])
        
        report['summary'] = {
            'total_symbols': total_symbols,
            'successful': successful,
            'partial': partial,
            'failed': failed,
            'duration_seconds': (end_time - start_time).total_seconds(),
            'end_time': end_time
        }
        
        self.logger.info(f"Post-trade validation completed: {successful}/{total_symbols} successful, "
                        f"{partial} partial, {failed} failed in {report['summary']['duration_seconds']:.1f}s")
        
        return report

def validate_after_live_trades(nuclear_symbols: Optional[List[str]] = None, 
                             tecl_symbols: Optional[List[str]] = None,
                             async_mode: bool = True) -> Optional[Dict[str, Any]]:
    """
    Main entry point for post-trade validation after live trades are executed.
    
    Args:
        nuclear_symbols: List of symbols used in Nuclear strategy signals (if any)
        tecl_symbols: List of symbols used in TECL strategy signals (if any) 
        async_mode: If True, run validation in background thread (recommended)
    
    Returns:
        Validation report dict (if not async), None if async
    """
    validator = PostTradeValidator()
    
    def _run_validation():
        all_reports = {}
        
        if nuclear_symbols:
            nuclear_report = validator.validate_strategy_symbols(nuclear_symbols, 'nuclear')
            all_reports['nuclear'] = nuclear_report
        
        if tecl_symbols:
            tecl_report = validator.validate_strategy_symbols(tecl_symbols, 'tecl')
            all_reports['tecl'] = tecl_report
        
        # Log summary
        for strategy, report in all_reports.items():
            summary = report['summary']
            logging.info(f"Post-trade validation {strategy.upper()}: "
                        f"{summary['successful']}/{summary['total_symbols']} successful")
        
        return all_reports
    
    if async_mode:
        # Run in background thread so it doesn't block trade execution
        thread = threading.Thread(target=_run_validation, daemon=True)
        thread.start()
        return None
    else:
        # Run synchronously and return results
        return _run_validation()
