#!/usr/bin/env python3
"""
Data Loading and Caching Module for Backtest Engine

This module handles:
- Historical data loading with intelligent symbol detection
- Optimized lookback calculations
- Data caching and sharing across workers
- Symbol-specific data requirements
"""
import os
import sys
import datetime as dt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager
from the_alchemiser.utils.symbol_lookback_calculator import SymbolLookbackCalculator
from the_alchemiser.backtest.data_cache import get_global_cache, BacktestDataCache

console = Console()

# Sensible defaults
DEFAULT_LOOKBACK_DAYS = 1200
DEFAULT_SAFETY_BUFFER_DAYS = 30


class DataLoader:
    """Handles data loading and caching for backtest operations"""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize the data loader
        
        Args:
            use_cache: Whether to use the global data cache
        """
        self.use_cache = use_cache
        self.data_provider: Optional[UnifiedDataProvider] = None
        self.cache: Optional[BacktestDataCache] = None
        
        if self.use_cache:
            self.cache = get_global_cache()
    
    def get_data_provider(self) -> UnifiedDataProvider:
        """Get or create data provider instance"""
        if self.data_provider is None:
            self.data_provider = UnifiedDataProvider(
                paper_trading=True, 
                cache_duration=3600
            )
        return self.data_provider
    
    def calculate_optimized_lookback(self, symbols: List[str], 
                                   use_minute_candles: bool = False, 
                                   strategies: Optional[List[str]] = None) -> int:
        """
        Calculate optimized lookback period based on symbol-specific requirements
        
        Args:
            symbols: List of symbols to analyze
            use_minute_candles: Whether minute data is being used
            strategies: List of strategies to consider ('nuclear', 'tecl', 'klm')
            
        Returns:
            Optimized lookback days required
        """
        if use_minute_candles:
            # For minute data, use shorter lookback to prevent memory issues
            console.print(f"[yellow]🕐 Using minute data - shorter lookback recommended[/yellow]")
            return 90  # 3 months for minute data
        
        # Use the symbol lookback calculator for strategy-aware optimization
        calculator = SymbolLookbackCalculator()
        
        # Calculate symbol-specific lookbacks with strategy awareness
        max_lookback = 0
        for symbol in symbols:
            try:
                symbol_lookback = calculator.get_symbol_lookback_days(symbol, strategies)
                max_lookback = max(max_lookback, symbol_lookback)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not calculate lookback for {symbol}: {e}[/yellow]")
                # Fallback to default for problematic symbols
                max_lookback = max(max_lookback, DEFAULT_LOOKBACK_DAYS // 2)
        
        # Add safety buffer for backtest reliability
        safety_buffer = max(DEFAULT_SAFETY_BUFFER_DAYS, int(max_lookback * 0.2))
        total_lookback = max_lookback + safety_buffer
        
        console.print(f"[green]📊 Optimized lookback: {total_lookback} days (vs {DEFAULT_LOOKBACK_DAYS} default)[/green]")
        console.print(f"[dim]   Max symbol requirement: {max_lookback} days + {safety_buffer} day buffer[/dim]")
        
        # Show optimization details
        try:
            optimization = calculator.optimize_data_fetching(symbols, strategies)
            old_approach_days = len(symbols) * DEFAULT_LOOKBACK_DAYS
            new_approach_days = optimization['efficiency_metrics']['optimized_total_days']
            savings_pct = ((old_approach_days - new_approach_days) / old_approach_days * 100)
            console.print(f"[dim]   Data reduction: {savings_pct:.1f}% ({old_approach_days:,} → {new_approach_days:,} symbol-days)[/dim]")
        except Exception as e:
            console.print(f"[dim]   Optimization details unavailable: {e}[/dim]")
        
        return total_lookback
    
    def get_all_strategy_symbols(self) -> Set[str]:
        """
        Get comprehensive list of all symbols used across strategies
        
        Returns:
            Set of all symbols that might be needed
        """
        symbols = set()
        
        # Core strategy symbols
        strategy_symbols = {
            # Nuclear strategy
            'OKLO', 'SMR', 'LEU', 'URA', 'URNM', 'DNN', 'CCJ', 'NXE',
            
            # TECL strategy  
            'TECL', 'TECS', 'XLK', 'QQQ', 'TQQQ', 'SQQQ',
            
            # KLM strategy (leveraged ETFs)
            'FNGU', 'FNGD', 'TECL', 'TECS', 'TQQQ', 'SQQQ', 'UVXY', 'SVXY',
            'SPXU', 'SPXL', 'TNA', 'TZA', 'FAS', 'FAZ', 'NUGT', 'DUST',
            'LABU', 'LABD', 'CURE', 'SH', 'UPRO', 'SPDN',
            
            # Sector ETFs
            'XLK', 'KMLM', 'XLE', 'XLF', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE',
            
            # Benchmark symbols
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VEA', 'VWO',
            'TLT', 'SHY', 'GLD', 'SLV', 'VIX', 'BIL', 'BSV'
        }
        symbols.update(strategy_symbols)
        
        return symbols
    
    def preload_data(self, start_date: dt.datetime, end_date: dt.datetime,
                    symbols: Optional[List[str]] = None,
                    include_minute_data: bool = False,
                    force_refresh: bool = False) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """
        Pre-load historical data for backtesting
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            symbols: Specific symbols to load (None = auto-detect)
            include_minute_data: Whether to fetch minute data
            force_refresh: Force refresh even if cached
            
        Returns:
            Tuple of (daily_data, minute_data) dictionaries
        """
        # Auto-detect symbols if not provided
        if symbols is None:
            console.print("[yellow]🔍 Auto-detecting symbols for all strategies...[/yellow]")
            symbols = sorted(list(self.get_all_strategy_symbols()))
            console.print(f"[green]📊 Detected {len(symbols)} symbols to load[/green]")
        
        # Use cache if available
        if self.use_cache and self.cache:
            return self.cache.preload_all_data(
                start_date, end_date, symbols, include_minute_data, force_refresh
            )
        
        # Fallback to direct loading
        return self._load_data_direct(start_date, end_date, symbols, include_minute_data)
    
    def _load_data_direct(self, start_date: dt.datetime, end_date: dt.datetime,
                         symbols: List[str], include_minute_data: bool) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """
        Load data directly without caching (fallback method)
        
        Args:
            start_date: Start date
            end_date: End date
            symbols: List of symbols
            include_minute_data: Whether to include minute data
            
        Returns:
            Tuple of (daily_data, minute_data) dictionaries
        """
        console.print(f"[yellow]⚠️ Loading data directly without cache[/yellow]")
        
        data_provider = self.get_data_provider()
        daily_data = {}
        minute_data = {}
        
        # Load daily data
        console.print(f"[blue]📊 Loading daily data for {len(symbols)} symbols...[/blue]")
        
        for i, symbol in enumerate(symbols):
            try:
                if i % 10 == 0:
                    console.print(f"[dim]Processing {i+1}/{len(symbols)}: {symbol}[/dim]")
                
                bars = data_provider.get_historical_data(symbol, start_date, end_date, timeframe="1d")
                
                if bars:
                    # Convert to DataFrame
                    data_rows = []
                    timestamps = []
                    
                    for bar in bars:
                        try:
                            data_rows.append({
                                'open': float(bar.open),
                                'high': float(bar.high),
                                'low': float(bar.low),
                                'close': float(bar.close),
                                'volume': int(bar.volume)
                            })
                            timestamps.append(bar.timestamp)
                        except Exception as bar_error:
                            console.print(f"[red]❌ Error processing bar for {symbol}: {bar_error}[/red]")
                            continue
                    
                    if data_rows and timestamps:
                        df = pd.DataFrame(data_rows)
                        df.index = pd.to_datetime(timestamps)
                        df.index.name = 'Date'
                        daily_data[symbol] = df
                    else:
                        console.print(f"[yellow]⚠️ No valid data for {symbol}[/yellow]")
                else:
                    console.print(f"[yellow]⚠️ No data returned for {symbol}[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Failed to load {symbol}: {e}[/red]")
        
        # Load minute data if requested
        if include_minute_data:
            console.print(f"[blue]⏱️ Loading minute data for {len(symbols)} symbols...[/blue]")
            
            for symbol in symbols:
                if symbol not in daily_data:
                    continue  # Skip symbols that failed daily loading
                
                try:
                    bars = data_provider.get_historical_data(symbol, start_date, end_date, timeframe="1m")
                    
                    if bars:
                        # Convert to DataFrame (same logic as daily)
                        data_rows = []
                        timestamps = []
                        
                        for bar in bars:
                            try:
                                data_rows.append({
                                    'open': float(bar.open),
                                    'high': float(bar.high),
                                    'low': float(bar.low),
                                    'close': float(bar.close),
                                    'volume': int(bar.volume)
                                })
                                timestamps.append(bar.timestamp)
                            except Exception:
                                continue
                        
                        if data_rows:
                            df = pd.DataFrame(data_rows)
                            df.index = pd.to_datetime(timestamps)
                            df.index.name = 'DateTime'
                            minute_data[symbol] = df
                            
                except Exception as e:
                    console.print(f"[red]❌ Failed to load minute data for {symbol}: {e}[/red]")
        
        console.print(f"[green]✅ Loaded {len(daily_data)} symbols with daily data[/green]")
        if include_minute_data:
            console.print(f"[green]✅ Loaded {len(minute_data)} symbols with minute data[/green]")
        
        return daily_data, minute_data
    
    def get_cached_symbol_data(self, symbols: List[str], start: dt.datetime, end: dt.datetime,
                              fetch_minute_data: bool = False) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """
        Get symbol data from cache (compatibility method)
        
        Args:
            symbols: List of symbols to retrieve
            start: Start date
            end: End date  
            fetch_minute_data: Whether to fetch minute data
            
        Returns:
            Tuple of (daily_data, minute_data) dictionaries
        """
        if not self.use_cache or not self.cache:
            console.print("[yellow]⚠️ Cache not available, loading directly[/yellow]")
            return self._load_data_direct(start, end, symbols, fetch_minute_data)
        
        console.print(f"[green]📂 Loading {len(symbols)} symbols from cache...[/green]")
        
        symbol_data = {}
        symbol_minute_data = {}
        missing_symbols = []
        
        for symbol in symbols:
            daily_df = self.cache.get_symbol_data(symbol, 'daily')
            if daily_df is not None:
                # Filter to date range
                mask = (daily_df.index >= start) & (daily_df.index <= end)
                symbol_data[symbol] = daily_df[mask]
                
                if fetch_minute_data:
                    minute_df = self.cache.get_symbol_data(symbol, 'minute')
                    if minute_df is not None:
                        minute_mask = (minute_df.index >= start) & (minute_df.index <= end)
                        symbol_minute_data[symbol] = minute_df[minute_mask]
            else:
                missing_symbols.append(symbol)
        
        console.print(f"[green]✅ Loaded {len(symbol_data)} symbols from cache[/green]")
        if missing_symbols:
            console.print(f"[yellow]⚠️ Missing from cache: {missing_symbols[:5]}{'...' if len(missing_symbols) > 5 else ''}[/yellow]")
        
        return symbol_data, symbol_minute_data
    
    def clear_cache(self):
        """Clear the data cache"""
        if self.cache:
            self.cache.clear_cache()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_cache_stats()
        return {}
