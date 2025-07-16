import pytest
from core.data_provider import DataProvider

def test_get_data_returns_dataframe():
    provider = DataProvider()
    df = provider.get_data('SPY', period='1mo')
    assert hasattr(df, 'columns')
    assert 'Close' in df.columns

def test_get_current_price_returns_float():
    provider = DataProvider()
    price = provider.get_current_price('SPY')
    assert isinstance(price, float) or isinstance(price, int)
    assert price > 0
