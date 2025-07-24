import pandas as pd
import numpy as np
import pytest
from the_alchemiser.core.indicators import TechnicalIndicators

def test_rsi_basic():
    # Create a simple price series
    prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115])
    rsi = TechnicalIndicators.rsi(prices, window=14)
    # Check output shape and reasonable values
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(prices)
    assert rsi.max() <= 100 and rsi.min() >= 0

def test_moving_average_basic():
    prices = pd.Series(np.arange(1, 21))
    ma = TechnicalIndicators.moving_average(prices, window=5)
    assert isinstance(ma, pd.Series)
    assert len(ma) == len(prices)
    # The first 4 values should be NaN (min_periods=window)
    assert ma[:4].isna().all()
    # The 5th value should be the mean of first 5 numbers
    assert np.isclose(ma[4], np.mean(prices[:5]))

def test_moving_average_return_basic():
    prices = pd.Series(np.linspace(100, 120, 21))
    ma_return = TechnicalIndicators.moving_average_return(prices, window=5)
    assert isinstance(ma_return, pd.Series)
    assert len(ma_return) == len(prices)
    # Should be finite values
    assert np.isfinite(ma_return[5:]).all()

def test_cumulative_return_basic():
    prices = pd.Series(np.linspace(100, 120, 21))
    cum_return = TechnicalIndicators.cumulative_return(prices, window=5)
    assert isinstance(cum_return, pd.Series)
    assert len(cum_return) == len(prices)
    # Should be finite values
    assert np.isfinite(cum_return[5:]).all()
