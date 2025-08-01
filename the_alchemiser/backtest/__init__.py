#!/usr/bin/env python3
"""
Refactored Backtest Package

This package provides a modular backtest engine with clean separation of concerns:

- engine.py: Core BacktestEngine orchestrating all operations
- data_loader.py: Data loading and caching functionality  
- metrics.py: Performance metrics calculations
- cli.py: Command-line interface
- strategies/: Strategy adapters and wrappers

Usage:
    from the_alchemiser.backtest import BacktestEngine
    
    engine = BacktestEngine()
    result = engine.run_individual_strategy('nuclear', start_date, end_date)
"""

# Import main classes for easy access
from .engine import BacktestEngine, BacktestResult
from .data_loader import DataLoader
from .metrics import MetricsCalculator, PerformanceMetrics
from .strategies import StrategyAdapter, MultiStrategyAdapter

# Version info
__version__ = "2.0.0"
__author__ = "The Alchemiser Team"

# Default configuration
DEFAULT_INITIAL_EQUITY = 1000.0
DEFAULT_SLIPPAGE_BPS = 8
DEFAULT_NOISE_FACTOR = 0.0015

__all__ = [
    'BacktestEngine',
    'BacktestResult', 
    'DataLoader',
    'MetricsCalculator',
    'PerformanceMetrics',
    'StrategyAdapter',
    'MultiStrategyAdapter',
    'DEFAULT_INITIAL_EQUITY',
    'DEFAULT_SLIPPAGE_BPS',
    'DEFAULT_NOISE_FACTOR'
]
