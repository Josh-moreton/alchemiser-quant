#!/usr/bin/env python3
"""
Pytest tests for TechnicalIndicators using pandas_ta
"""

import pytest
import pandas as pd
import numpy as np
from src.core.nuclear_trading_bot import TechnicalIndicators

class TestTechnicalIndicators:
    def test_rsi_basic(self):
        # Create a simple price series
        prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115])
        rsi = TechnicalIndicators.rsi(prices, window=14)
        # Should return a pd.Series of same length
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(prices)
        # The last value should be a float between 0 and 100
        assert 0 <= rsi.iloc[-1] <= 100

    def test_moving_average(self):
        prices = pd.Series(np.arange(1, 21))
        ma = TechnicalIndicators.moving_average(prices, window=5)
        assert isinstance(ma, pd.Series)
        assert len(ma) == len(prices)
        # The first 4 values should be NaN
        assert ma.iloc[0:4].isna().all()
        # The 5th value should be the mean of 1-5
        assert np.isclose(ma.iloc[4], 3.0)

    def test_moving_average_return(self):
        prices = pd.Series(np.linspace(100, 200, 20))
        ma_return = TechnicalIndicators.moving_average_return(prices, window=5)
        assert isinstance(ma_return, pd.Series)
        assert len(ma_return) == len(prices)
        # Should be mostly positive for increasing prices
        assert ma_return.dropna().iloc[-1] > 0

    def test_cumulative_return(self):
        prices = pd.Series([100, 105, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200])
        cum_return = TechnicalIndicators.cumulative_return(prices, window=5)
        assert isinstance(cum_return, pd.Series)
        assert len(cum_return) == len(prices)
        # The 6th value should be ((140/100)-1)*100 = 40
        assert np.isclose(cum_return.iloc[5], 40.0)
        # The last value should be ((200/150)-1)*100 = 33.333...
        assert np.isclose(cum_return.iloc[-1], (200/150-1)*100)
