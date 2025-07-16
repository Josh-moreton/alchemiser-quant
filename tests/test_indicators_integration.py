import pytest
from src.core.nuclear_trading_bot import NuclearStrategyEngine
import pandas as pd
import numpy as np

def test_indicators_integration():
    # Create fake market data for a nuclear symbol
    fake_close = pd.Series(np.random.rand(100) * 100)
    market_data = {'SMR': pd.DataFrame({'Close': fake_close})}
    engine = NuclearStrategyEngine()
    indicators = engine.calculate_indicators(market_data)
    assert 'SMR' in indicators
    # Check that all expected indicator keys exist
    for key in ['rsi_10', 'rsi_20', 'ma_200', 'ma_20', 'ma_return_90', 'cum_return_60', 'current_price']:
        assert key in indicators['SMR']
    # Check that values are floats (except current_price)
    for key in ['rsi_10', 'rsi_20', 'ma_200', 'ma_20', 'ma_return_90', 'cum_return_60']:
        assert isinstance(indicators['SMR'][key], float)
    assert isinstance(indicators['SMR']['current_price'], float)
