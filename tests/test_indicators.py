import pytest
import pandas as pd
from core.indicators import TechnicalIndicators

# Test data for coverage
@pytest.mark.parametrize("data", [
    pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
    pd.Series([5] * 20),
])
def test_rsi_no_error(data):
    result = TechnicalIndicators.rsi(data, window=5)
    assert isinstance(result, pd.Series)
    assert len(result) == len(data)

@pytest.mark.parametrize("data", [
    pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
    pd.Series([5] * 20),
])
def test_moving_average_no_error(data):
    result = TechnicalIndicators.moving_average(data, window=5)
    assert isinstance(result, pd.Series)
    assert len(result) == len(data)

@pytest.mark.parametrize("data", [
    pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
    pd.Series([5] * 20),
])
def test_moving_average_return_no_error(data):
    result = TechnicalIndicators.moving_average_return(data, window=5)
    assert isinstance(result, pd.Series)
    assert len(result) == len(data)

@pytest.mark.parametrize("data", [
    pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
    pd.Series([5] * 20),
])
def test_cumulative_return_no_error(data):
    result = TechnicalIndicators.cumulative_return(data, window=5)
    assert isinstance(result, pd.Series)
    assert len(result) == len(data)
