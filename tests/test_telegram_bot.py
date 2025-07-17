import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from core.nuclear_trading_bot import NuclearTradingBot

# Comprehensive market scenarios based on the Clojure Nuclear.clj strategy
MARKET_SCENARIOS = [
    # SPY Overbought scenarios (RSI > 79)
    {
        "name": "spy_overbought_extreme",
        "spy_rsi_10": 82,
        "spy_price": 500,
        "spy_ma_200": 400,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
        "description": "SPY RSI > 81, should trigger UVXY"
    },
    {
        "name": "spy_overbought_moderate",
        "spy_rsi_10": 80,
        "spy_price": 500,
        "spy_ma_200": 400,
        "ioo_rsi_10": 82,
        "expected_action": "BUY", 
        "expected_symbol": "UVXY",
        "description": "SPY RSI 79-81, IOO RSI > 81, should trigger UVXY"
    },
    {
        "name": "multiple_overbought_uvxy_btal",
        "spy_rsi_10": 80,
        "spy_price": 500,
        "spy_ma_200": 400,
        "ioo_rsi_10": 80,
        "tqqq_rsi_10": 80,
        "vtv_rsi_10": 80,
        "xlf_rsi_10": 80,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",  # Should get 75% UVXY, 25% BTAL
        "description": "Multiple symbols overbought but none > 81, should trigger UVXY/BTAL portfolio"
    },
    
    # VOX Overbought scenario
    {
        "name": "vox_overbought",
        "spy_rsi_10": 75,
        "spy_price": 500,
        "spy_ma_200": 400,
        "vox_rsi_10": 82,
        "xlf_rsi_10": 82,
        "expected_action": "BUY",
        "expected_symbol": "UVXY",
        "description": "VOX RSI > 79, XLF RSI > 81, should trigger UVXY"
    },
    
    # Oversold scenarios
    {
        "name": "tqqq_oversold",
        "spy_rsi_10": 50,
        "spy_price": 500,
        "spy_ma_200": 400,
        "tqqq_rsi_10": 25,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",
        "description": "TQQQ RSI < 30, should buy TQQQ dip"
    },
    {
        "name": "spy_oversold",
        "spy_rsi_10": 25,
        "spy_price": 500,
        "spy_ma_200": 400,
        "tqqq_rsi_10": 50,
        "expected_action": "BUY",
        "expected_symbol": "UPRO",
        "description": "SPY RSI < 30, should buy UPRO (leveraged SPY)"
    },
    
    # Bull Market scenarios (SPY > MA200)
    {
        "name": "bull_market_nuclear",
        "spy_rsi_10": 60,
        "spy_price": 500,
        "spy_ma_200": 400,
        "tqqq_rsi_10": 50,
        "vox_rsi_10": 50,
        "expected_action": "BUY",
        "expected_portfolio": ["SMR", "LEU", "OKLO"],  # Top 3 nuclear stocks
        "description": "Bull market (SPY > MA200), should trigger nuclear portfolio"
    },
    
    # Bear Market scenarios (SPY < MA200)
    {
        "name": "bear_market_psq_oversold",
        "spy_rsi_10": 50,
        "spy_price": 350,
        "spy_ma_200": 400,
        "psq_rsi_10": 30,
        "expected_action": "BUY",
        "expected_symbol": "SQQQ",
        "description": "Bear market, PSQ RSI < 35, should buy SQQQ"
    },
    {
        "name": "bear_market_qqq_weak",
        "spy_rsi_10": 50,
        "spy_price": 350,
        "spy_ma_200": 400,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -15,
        "tlt_rsi_20": 60,
        "psq_rsi_20": 50,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",  # Bonds stronger than PSQ
        "description": "Bear market, QQQ weak, bonds strong vs PSQ, contrarian TQQQ buy"
    },
    {
        "name": "bear_market_tqqq_up_bonds_strong",
        "spy_rsi_10": 50,
        "spy_price": 350,
        "spy_ma_200": 400,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -5,
        "tqqq_price": 25,
        "tqqq_ma_20": 20,
        "tlt_rsi_20": 60,
        "psq_rsi_20": 50,
        "expected_action": "BUY",
        "expected_symbol": "TQQQ",
        "description": "Bear market, TQQQ trending up, bonds strong"
    },
    {
        "name": "bear_market_default_sqqq",
        "spy_rsi_10": 50,
        "spy_price": 350,
        "spy_ma_200": 400,
        "psq_rsi_10": 50,
        "qqq_cum_return_60": -5,
        "tqqq_price": 15,
        "tqqq_ma_20": 20,
        "tlt_rsi_20": 40,
        "psq_rsi_20": 50,
        "expected_action": "BUY",
        "expected_symbol": "SQQQ",
        "description": "Bear market, default to SQQQ"
    },
    
    # No clear signal scenario - actually triggers bear market logic
    {
        "name": "no_clear_signal",
        "spy_rsi_10": 50,
        "spy_price": 400,  # Exactly at MA200, not > MA200 so goes to bear market
        "spy_ma_200": 400,
        "tqqq_rsi_10": 50,
        "psq_rsi_10": 50,  # Not oversold
        "expected_action": "BUY",
        "expected_symbol": "SQQQ",  # Bear market default when no other conditions met
        "description": "SPY at MA200 triggers bear market logic with default SQQQ"
    }
]

def create_comprehensive_mock_data(scenario):
    """Create comprehensive mock market data with all required symbols and proper DataFrame structure"""
    
    # Base prices for all symbols (realistic values)
    base_prices = {
        'SPY': scenario.get('spy_price', 450),
        'IOO': 85,
        'TQQQ': scenario.get('tqqq_price', 45),
        'VTV': 160,
        'XLF': 40,
        'VOX': 95,
        'UVXY': 12,
        'BTAL': 25,
        'QQQ': 380,
        'SQQQ': 8,
        'PSQ': 14,
        'UPRO': 65,
        'TLT': 90,
        'IEF': 100,
        'SMR': 45,
        'BWXT': 85,
        'LEU': 55,
        'EXC': 38,
        'NLR': 120,
        'OKLO': 8
    }
    
    market_data = {}
    
    for symbol, base_price in base_prices.items():
        # Create realistic price series with some variation
        np.random.seed(42)  # For reproducible tests
        price_series = base_price + np.cumsum(np.random.normal(0, 0.01, 250)) * base_price * 0.1
        price_series = np.maximum(price_series, base_price * 0.5)  # Prevent negative prices
        
        # Create proper DataFrame structure
        dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
        
        market_data[symbol] = pd.DataFrame({
            'Open': price_series * 0.99,
            'High': price_series * 1.02,
            'Low': price_series * 0.98,
            'Close': price_series,
            'Volume': np.random.randint(1000000, 5000000, 250)
        }, index=dates)
    
    return market_data

def create_comprehensive_mock_indicators(scenario):
    """Create comprehensive mock indicators with all required values"""
    
    # Default indicator values
    default_indicators = {
        'SPY': {
            'rsi_10': scenario.get('spy_rsi_10', 50),
            'rsi_20': scenario.get('spy_rsi_20', 50),
            'ma_200': scenario.get('spy_ma_200', 400),
            'ma_20': scenario.get('spy_ma_20', scenario.get('spy_price', 450) * 0.98),
            'ma_return_90': 0.5,
            'cum_return_60': 5.0,
            'current_price': scenario.get('spy_price', 450)
        },
        'IOO': {
            'rsi_10': scenario.get('ioo_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 80,
            'ma_20': 84,
            'ma_return_90': 0.3,
            'cum_return_60': 3.0,
            'current_price': 85
        },
        'TQQQ': {
            'rsi_10': scenario.get('tqqq_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 40,
            'ma_20': scenario.get('tqqq_ma_20', 44),
            'ma_return_90': 1.2,
            'cum_return_60': 10.0,
            'current_price': scenario.get('tqqq_price', 45)
        },
        'VTV': {
            'rsi_10': scenario.get('vtv_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 155,
            'ma_20': 158,
            'ma_return_90': 0.4,
            'cum_return_60': 4.0,
            'current_price': 160
        },
        'XLF': {
            'rsi_10': scenario.get('xlf_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 38,
            'ma_20': 39,
            'ma_return_90': 0.6,
            'cum_return_60': 6.0,
            'current_price': 40
        },
        'VOX': {
            'rsi_10': scenario.get('vox_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 90,
            'ma_20': 93,
            'ma_return_90': 0.8,
            'cum_return_60': 8.0,
            'current_price': 95
        },
        'UVXY': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 15,
            'ma_20': 13,
            'ma_return_90': -2.0,
            'cum_return_60': -15.0,
            'current_price': 12
        },
        'BTAL': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 24,
            'ma_20': 25,
            'ma_return_90': 0.2,
            'cum_return_60': 2.0,
            'current_price': 25
        },
        'QQQ': {
            'rsi_10': scenario.get('qqq_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 370,
            'ma_20': 375,
            'ma_return_90': 1.0,
            'cum_return_60': scenario.get('qqq_cum_return_60', 8.0),
            'current_price': 380
        },
        'SQQQ': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 10,
            'ma_20': 9,
            'ma_return_90': -1.5,
            'cum_return_60': -12.0,
            'current_price': 8
        },
        'PSQ': {
            'rsi_10': scenario.get('psq_rsi_10', 50),
            'rsi_20': scenario.get('psq_rsi_20', 50),
            'ma_200': 15,
            'ma_20': 14,
            'ma_return_90': -0.8,
            'cum_return_60': -6.0,
            'current_price': 14
        },
        'UPRO': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 60,
            'ma_20': 63,
            'ma_return_90': 1.5,
            'cum_return_60': 12.0,
            'current_price': 65
        },
        'TLT': {
            'rsi_10': 50,
            'rsi_20': scenario.get('tlt_rsi_20', 50),
            'ma_200': 85,
            'ma_20': 88,
            'ma_return_90': -0.5,
            'cum_return_60': -3.0,
            'current_price': 90
        },
        'IEF': {
            'rsi_10': scenario.get('ief_rsi_10', 50),
            'rsi_20': 50,
            'ma_200': 95,
            'ma_20': 98,
            'ma_return_90': -0.2,
            'cum_return_60': -1.0,
            'current_price': 100
        },
        # Nuclear stocks with different performance rankings
        'SMR': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 40,
            'ma_20': 43,
            'ma_return_90': 1.4,  # Best performer
            'cum_return_60': 12.0,
            'current_price': 45
        },
        'LEU': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 50,
            'ma_20': 53,
            'ma_return_90': 1.3,  # Second best
            'cum_return_60': 11.0,
            'current_price': 55
        },
        'OKLO': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 7,
            'ma_20': 7.5,
            'ma_return_90': 1.2,  # Third best
            'cum_return_60': 10.0,
            'current_price': 8
        },
        'BWXT': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 80,
            'ma_20': 83,
            'ma_return_90': 0.4,  # Fourth
            'cum_return_60': 4.0,
            'current_price': 85
        },
        'EXC': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 36,
            'ma_20': 37,
            'ma_return_90': 0.1,  # Fifth
            'cum_return_60': 1.0,
            'current_price': 38
        },
        'NLR': {
            'rsi_10': 50,
            'rsi_20': 50,
            'ma_200': 115,
            'ma_20': 118,
            'ma_return_90': 0.5,  # Sixth
            'cum_return_60': 5.0,
            'current_price': 120
        }
    }
    
    return default_indicators

@pytest.mark.parametrize("scenario", MARKET_SCENARIOS)
def test_telegram_bot_signals_comprehensive(scenario):
    """Test that the telegram bot produces correct signals for all market conditions"""
    bot = NuclearTradingBot()

    # Create comprehensive mock data
    mock_market_data = create_comprehensive_mock_data(scenario)
    mock_indicators = create_comprehensive_mock_indicators(scenario)
    
    # Patch the strategy methods
    with patch.object(bot.strategy, "get_market_data", return_value=mock_market_data), \
         patch.object(bot.strategy, "calculate_indicators", return_value=mock_indicators):
        
        # Run the analysis
        alerts = bot.run_analysis()
        
        # Check that we got alerts
        assert alerts is not None, f"No alerts produced for scenario: {scenario['name']}"
        assert len(alerts) > 0, f"Empty alerts list for scenario: {scenario['name']}"
        
        # Extract the main signal (first alert)
        main_alert = alerts[0]
            
        # Verify the expected action
        assert main_alert.action == scenario["expected_action"], \
            f"Expected action {scenario['expected_action']} but got {main_alert.action} for {scenario['name']}: {scenario['description']}"
        
        # Verify the expected symbol (for single symbol scenarios)
        if "expected_symbol" in scenario and scenario["expected_symbol"] not in ["NUCLEAR_PORTFOLIO", "UVXY_BTAL_PORTFOLIO"]:
            assert main_alert.symbol == scenario["expected_symbol"], \
                f"Expected symbol {scenario['expected_symbol']} but got {main_alert.symbol} for {scenario['name']}: {scenario['description']}"
        
        # For nuclear portfolio scenarios, check that we get multiple alerts
        if "expected_portfolio" in scenario and scenario["expected_portfolio"]:
            # Should have multiple alerts for nuclear portfolio
            alert_symbols = [alert.symbol for alert in alerts]
            for expected_symbol in scenario["expected_portfolio"]:
                assert expected_symbol in alert_symbols, \
                    f"Expected {expected_symbol} in nuclear portfolio alerts for {scenario['name']}: {scenario['description']}"
        
        # Validate that all alerts have required fields
        for alert in alerts:
            assert hasattr(alert, 'symbol'), f"Alert missing symbol for {scenario['name']}"
            assert hasattr(alert, 'action'), f"Alert missing action for {scenario['name']}"
            assert hasattr(alert, 'reason'), f"Alert missing reason for {scenario['name']}"
            assert hasattr(alert, 'price'), f"Alert missing price for {scenario['name']}"
            assert hasattr(alert, 'timestamp'), f"Alert missing timestamp for {scenario['name']}"

def test_telegram_bot_initialization():
    """Test that the telegram bot initializes correctly"""
    bot = NuclearTradingBot()
    assert bot.strategy is not None
    assert hasattr(bot.strategy, 'nuclear_symbols')
    assert 'SMR' in bot.strategy.nuclear_symbols
    assert 'OKLO' in bot.strategy.nuclear_symbols

def test_nuclear_portfolio_ranking():
    """Test that nuclear portfolio correctly ranks stocks by performance"""
    bot = NuclearTradingBot()
    
    # Mock indicators with specific performance ranking
    mock_indicators = {
        'SMR': {'ma_return_90': 2.0, 'current_price': 45},
        'LEU': {'ma_return_90': 1.5, 'current_price': 55}, 
        'OKLO': {'ma_return_90': 1.0, 'current_price': 8},
        'BWXT': {'ma_return_90': 0.5, 'current_price': 85},
        'EXC': {'ma_return_90': 0.1, 'current_price': 38},
        'NLR': {'ma_return_90': 0.8, 'current_price': 120}
    }
    
    # Mock market data for volatility calculation
    mock_market_data = create_comprehensive_mock_data({})
    
    portfolio = bot.strategy.get_nuclear_portfolio(mock_indicators, mock_market_data, top_n=3)
    
    # Should get top 3: SMR, LEU, OKLO
    assert 'SMR' in portfolio
    assert 'LEU' in portfolio  
    assert 'OKLO' in portfolio
    assert len(portfolio) == 3
    
    # Verify performance values are correct
    assert portfolio['SMR']['performance'] == 2.0
    assert portfolio['LEU']['performance'] == 1.5
    assert portfolio['OKLO']['performance'] == 1.0

def test_bear_market_logic():
    """Test specific bear market decision logic"""
    bot = NuclearTradingBot()
    
    # Test PSQ oversold scenario
    indicators_psq_oversold = {
        'SPY': {'current_price': 350, 'ma_200': 400, 'rsi_10': 50},
        'PSQ': {'rsi_10': 30}  # Oversold
    }
    
    result = bot.strategy._bear_subgroup_1(indicators_psq_oversold)
    assert result[0] == 'SQQQ'
    assert result[1] == 'BUY'
    
    # Test bonds stronger than PSQ scenario
    indicators_bonds_strong = {
        'QQQ': {'cum_return_60': -15},  # Weak
        'TLT': {'rsi_20': 60},
        'PSQ': {'rsi_20': 45}  # TLT stronger than PSQ
    }
    
    result = bot.strategy._bear_subgroup_1(indicators_bonds_strong)
    assert result[0] == 'TQQQ'  # Contrarian buy
    assert result[1] == 'BUY'

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
    bull_scenario = MARKET_SCENARIOS[6]  # bull_market_nuclear
    mock_market_data = create_comprehensive_mock_data(bull_scenario)
    mock_indicators = create_comprehensive_mock_indicators(bull_scenario)
    
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