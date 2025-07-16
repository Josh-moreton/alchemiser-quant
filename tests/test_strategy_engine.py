import pytest
from core.strategy_engine import BullMarketStrategy, BearMarketStrategy, OverboughtStrategy, SecondaryOverboughtStrategy, VoxOverboughtStrategy

def test_bull_market_strategy():
    def fake_get_nuclear_portfolio(indicators, market_data=None):
        return {'SMR': {'weight': 1.0, 'performance': 0.5}}
    strat = BullMarketStrategy(fake_get_nuclear_portfolio)
    indicators = {'SPY': {'current_price': 500, 'ma_200': 400}}
    result = strat.recommend(indicators)
    assert result[0] == 'NUCLEAR_PORTFOLIO'
    assert result[1] == 'BUY'

def test_bear_market_strategy():
    def fake_bear1(ind): return ('SQQQ', 'BUY', 'Bear1')
    def fake_bear2(ind): return ('SQQQ', 'BUY', 'Bear2')
    def fake_combine(b1, b2, ind): return None
    strat = BearMarketStrategy(fake_bear1, fake_bear2, fake_combine)
    indicators = {}
    result = strat.recommend(indicators)
    assert result[0] == 'SQQQ'
    assert result[1] == 'BUY'

def test_overbought_strategy():
    strat = OverboughtStrategy()
    indicators = {'SPY': {'rsi_10': 82}}
    result = strat.recommend(indicators)
    assert result[0] == 'UVXY'
    assert result[1] == 'BUY'

def test_secondary_overbought_strategy():
    strat = SecondaryOverboughtStrategy()
    indicators = {'TQQQ': {'rsi_10': 82}}
    result = strat.recommend(indicators, 'TQQQ')
    assert result[0] == 'UVXY'
    assert result[1] == 'BUY'

def test_vox_overbought_strategy():
    strat = VoxOverboughtStrategy()
    indicators = {'XLF': {'rsi_10': 82}}
    result = strat.recommend(indicators)
    assert result[0] == 'UVXY'
    assert result[1] == 'BUY'
