import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.nuclear_trading_bot import NuclearTradingBot

# Comprehensive test scenarios based on Nuclear.clj strategy logic
MARKET_SCENARIOS = [
    # Bull Market Scenarios
    {
        "name": "bull_market_nuclear_portfolio",
        "description": "SPY above 200-day MA triggers nuclear portfolio",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 60,
        "expected_action": "BUY",
        "expected_symbol": "NUCLEAR_PORTFOLIO",
        "expected_portfolio": ["SMR", "LEU", "OKLO"],  # Top 3 nuclear stocks
    },
    
    # Overbought Scenarios (RSI > 79)
    {
        "name": "spy_overbought_79_81",
        "description": "SPY RSI between 79-81 triggers volatility protection",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 80,
        "ioo_rsi_10": 60,
        "tqqq_rsi_10": 60,
        "vtv_rsi_10": 60,
        "xlf_rsi_10": 60,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
    },
    
    {
        "name": "spy_extremely_overbought",
        "description": "SPY RSI > 81 triggers immediate UVXY",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 85,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
    },
    
    {
        "name": "secondary_overbought_ioo",
        "description": "IOO RSI > 81 triggers UVXY",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 75,
        "ioo_rsi_10": 85,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
    },
    
    {
        "name": "vox_overbought",
        "description": "VOX RSI > 79 triggers volatility protection",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 60,
        "vox_rsi_10": 85,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
    },
    
    # Oversold Scenarios (RSI < 30)
    {
        "name": "tqqq_oversold",
        "description": "TQQQ RSI < 30 triggers buying the dip",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 60,
        "tqqq_rsi_10": 25,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",
    },
    
    {
        "name": "spy_oversold",
        "description": "SPY RSI < 30 triggers leveraged SPY play",
        "spy_price": 500,
        "spy_ma_200": 400,
        "spy_rsi_10": 25,
        "tqqq_rsi_10": 60,
        "expected_action": "BUY",
        "expected_symbol": "UPRO",
    },
    
    # Bear Market Scenarios
    {
        "name": "bear_market_psq_oversold",
        "description": "Bear market with PSQ RSI < 35 triggers aggressive short",
        "spy_price": 350,
        "spy_ma_200": 400,
        "spy_rsi_10": 40,
        "psq_rsi_10": 30,
        "expected_action": "BUY",
        "expected_symbol": "SQQQ",
    },
    
    {
        "name": "bear_market_qqq_weak",
        "description": "Bear market with QQQ 60-day return < -10%",
        "spy_price": 350,
        "spy_ma_200": 400,
        "spy_rsi_10": 40,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -15,
        "tlt_rsi_20": 60,
        "psq_rsi_20": 40,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",  # TLT stronger than PSQ
    },
    
    {
        "name": "bear_market_tqqq_above_ma20",
        "description": "Bear market with TQQQ above 20-day MA",
        "spy_price": 350,
        "spy_ma_200": 400,
        "spy_rsi_10": 40,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -5,
        "tqqq_price": 25,
        "tqqq_ma_20": 20,
        "tlt_rsi_20": 60,
        "psq_rsi_20": 40,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",  # TQQQ trending up, bonds strong
    },
    
    {
        "name": "bear_market_default_short",
        "description": "Default bear market conditions trigger short tech",
        "spy_price": 350,
        "spy_ma_200": 400,
        "spy_rsi_10": 40,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -5,
        "tqqq_price": 15,
        "tqqq_ma_20": 20,
        "tlt_rsi_20": 40,
        "psq_rsi_20": 50,
        "expected_action": "BUY",
        "expected_symbol": "SQQQ",
    },
]

def create_mock_market_data(scenario):
    """Create comprehensive mock market data for all symbols"""
    base_data = {
        'Open': [100] * 250,
        'High': [105] * 250,
        'Low': [95] * 250,
        'Close': [100] * 250,
        'Volume': [1000000] * 250,
    }
    
    # Create DataFrames for all symbols
    market_data = {}
    
    # SPY data
    spy_close = [scenario.get("spy_price", 400)] * 250
    market_data["SPY"] = pd.DataFrame({
        'Open': spy_close,
        'High': spy_close,
        'Low': spy_close,
        'Close': spy_close,
        'Volume': [1000000] * 250,
    })
    
    # Other market symbols
    for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF', 'VOX', 'UVXY', 'BTAL', 'QQQ', 'SQQQ', 'PSQ', 'UPRO', 'TLT', 'IEF']:
        price = scenario.get(f"{symbol.lower()}_price", 100)
        market_data[symbol] = pd.DataFrame({
            'Open': [price] * 250,
            'High': [price] * 250,
            'Low': [price] * 250,
            'Close': [price] * 250,
            'Volume': [1000000] * 250,
        })
    
    # Nuclear energy symbols
    nuclear_symbols = ['SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
    for symbol in nuclear_symbols:
        price = scenario.get(f"{symbol.lower()}_price", 20)
        market_data[symbol] = pd.DataFrame({
            'Open': [price] * 250,
            'High': [price] * 250,
            'Low': [price] * 250,
            'Close': [price] * 250,
            'Volume': [1000000] * 250,
        })
    
    return market_data

def create_mock_indicators(scenario):
    """Create comprehensive mock indicators for all symbols"""
    indicators = {}
    
    # SPY indicators
    indicators["SPY"] = {
        'rsi_10': scenario.get("spy_rsi_10", 50),
        'rsi_20': scenario.get("spy_rsi_20", 50),
        'ma_200': scenario.get("spy_ma_200", 400),
        'ma_20': scenario.get("spy_ma_20", 400),
        'ma_return_90': scenario.get("spy_ma_return_90", 0.5),
        'cum_return_60': scenario.get("spy_cum_return_60", 5),
        'current_price': scenario.get("spy_price", 400),
    }
    
    # Other market symbols
    for symbol in ['IOO', 'TQQQ', 'VTV', 'XLF', 'VOX', 'UVXY', 'BTAL', 'QQQ', 'SQQQ', 'PSQ', 'UPRO', 'TLT', 'IEF']:
        indicators[symbol] = {
            'rsi_10': scenario.get(f"{symbol.lower()}_rsi_10", 50),
            'rsi_20': scenario.get(f"{symbol.lower()}_rsi_20", 50),
            'ma_200': scenario.get(f"{symbol.lower()}_ma_200", 100),
            'ma_20': scenario.get(f"{symbol.lower()}_ma_20", 100),
            'ma_return_90': scenario.get(f"{symbol.lower()}_ma_return_90", 0.5),
            'cum_return_60': scenario.get(f"{symbol.lower()}_cum_return_60", 5),
            'current_price': scenario.get(f"{symbol.lower()}_price", 100),
        }
    
    # Nuclear energy symbols with performance data
    nuclear_performances = {
        'SMR': 1.4206,  # Based on actual bot output
        'BWXT': 0.4017,
        'LEU': 1.3150,
        'EXC': 0.0084,
        'NLR': 0.4899,
        'OKLO': 1.2732,
    }
    
    for symbol, performance in nuclear_performances.items():
        indicators[symbol] = {
            'rsi_10': scenario.get(f"{symbol.lower()}_rsi_10", 50),
            'rsi_20': scenario.get(f"{symbol.lower()}_rsi_20", 50),
            'ma_200': scenario.get(f"{symbol.lower()}_ma_200", 20),
            'ma_20': scenario.get(f"{symbol.lower()}_ma_20", 20),
            'ma_return_90': performance,  # Use actual performance for nuclear stocks
            'cum_return_60': scenario.get(f"{symbol.lower()}_cum_return_60", 5),
            'current_price': scenario.get(f"{symbol.lower()}_price", 20),
        }
    
    return indicators

@pytest.mark.parametrize("scenario", MARKET_SCENARIOS)
def test_nuclear_trading_bot_signals(scenario):
    """Test that the bot produces correct signals for all market scenarios"""
    bot = NuclearTradingBot()
    
    # Create mock data
    mock_market_data = create_mock_market_data(scenario)
    mock_indicators = create_mock_indicators(scenario)
    
    # Patch the bot's strategy methods
    with patch.object(bot.strategy, "get_market_data", return_value=mock_market_data), \
         patch.object(bot.strategy, "calculate_indicators", return_value=mock_indicators):
        
        # Run the analysis
        alerts = bot.run_analysis()
        
        # Verify we got alerts
        assert alerts is not None, f"No alerts produced for scenario: {scenario['name']}"
        assert len(alerts) > 0, f"Empty alerts list for scenario: {scenario['name']}"
        
        # Get the main signal
        main_alert = alerts[0]
        
        # Check the action
        assert main_alert.action == scenario["expected_action"], \
            f"Expected action {scenario['expected_action']} but got {main_alert.action} for {scenario['name']}"
        
        # Check the symbol (for non-portfolio signals)
        if scenario.get("expected_symbol") and scenario["expected_symbol"] != "NUCLEAR_PORTFOLIO":
            assert main_alert.symbol == scenario["expected_symbol"], \
                f"Expected symbol {scenario['expected_symbol']} but got {main_alert.symbol} for {scenario['name']}"
        
        # Check portfolio allocation for nuclear portfolio scenarios
        if scenario.get("expected_portfolio"):
            portfolio = bot.get_current_portfolio_allocation()
            assert portfolio is not None, f"No portfolio produced for scenario: {scenario['name']}"
            
            # Check that expected symbols are in the portfolio
            portfolio_symbols = set(portfolio.keys())
            expected_symbols = set(scenario["expected_portfolio"])
            assert expected_symbols.issubset(portfolio_symbols), \
                f"Expected symbols {expected_symbols} not found in portfolio {portfolio_symbols} for {scenario['name']}"
            
            # Check that portfolio weights sum to approximately 1.0
            total_weight = sum(data['weight'] for data in portfolio.values())
            assert abs(total_weight - 1.0) < 0.01, \
                f"Portfolio weights don't sum to 1.0 (got {total_weight}) for {scenario['name']}"

def test_nuclear_trading_bot_error_handling():
    """Test that the bot handles errors gracefully"""
    bot = NuclearTradingBot()
    
    # Test with empty market data
    with patch.object(bot.strategy, "get_market_data", return_value={}):
        alerts = bot.run_analysis()
        assert alerts is None or len(alerts) == 0
    
    # Test with missing SPY data
    incomplete_data = {"QQQ": pd.DataFrame({'Close': [100] * 250})}
    with patch.object(bot.strategy, "get_market_data", return_value=incomplete_data):
        alerts = bot.run_analysis()
        # Should still produce some result (likely a default signal)
        assert alerts is not None

def test_nuclear_portfolio_allocation():
    """Test nuclear portfolio allocation logic specifically"""
    bot = NuclearTradingBot()
    
    # Mock bull market scenario
    bull_scenario = MARKET_SCENARIOS[0]  # bull_market_nuclear_portfolio
    mock_market_data = create_mock_market_data(bull_scenario)
    mock_indicators = create_mock_indicators(bull_scenario)
    
    with patch.object(bot.strategy, "get_market_data", return_value=mock_market_data), \
         patch.object(bot.strategy, "calculate_indicators", return_value=mock_indicators):
        
        # Get portfolio allocation
        portfolio = bot.get_current_portfolio_allocation()
        
        assert portfolio is not None, "No portfolio allocation returned"
        
        # Check that we have the expected nuclear stocks
        expected_stocks = {'SMR', 'LEU', 'OKLO'}  # Top 3 performers
        portfolio_stocks = set(portfolio.keys())
        assert expected_stocks == portfolio_stocks, \
            f"Expected {expected_stocks} but got {portfolio_stocks}"
        
        # Check that each stock has required fields
        for symbol, data in portfolio.items():
            assert 'weight' in data, f"Missing weight for {symbol}"
            assert 'performance' in data, f"Missing performance for {symbol}"
            assert 'current_price' in data, f"Missing current_price for {symbol}"
            assert data['weight'] > 0, f"Invalid weight for {symbol}: {data['weight']}"
        
        # Check that weights sum to 1.0
        total_weight = sum(data['weight'] for data in portfolio.values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights don't sum to 1.0: {total_weight}"