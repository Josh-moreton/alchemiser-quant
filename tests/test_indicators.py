import pandas as pd
import numpy as np
import pytest
from src.core.indicators import TechnicalIndicators

def test_rsi_returns_series():
    data = pd.Series(np.random.rand(100) * 100)
    rsi = TechnicalIndicators.rsi(data, window=14)
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(data)

def test_moving_average_returns_series():
    data = pd.Series(np.random.rand(100) * 100)
    ma = TechnicalIndicators.moving_average(data, window=20)
    assert isinstance(ma, pd.Series)
    assert len(ma) == len(data)

def test_moving_average_return_returns_series():
    data = pd.Series(np.random.rand(100) * 100)
    ma_return = TechnicalIndicators.moving_average_return(data, window=20)
    assert isinstance(ma_return, pd.Series)
    assert len(ma_return) == len(data)

def test_cumulative_return_returns_series():
    data = pd.Series(np.random.rand(100) * 100)
    cum_return = TechnicalIndicators.cumulative_return(data, window=20)
    assert isinstance(cum_return, pd.Series)
    assert len(cum_return) == len(data)
