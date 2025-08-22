"""Integration test showing parser and evaluator working together."""

import pytest
from unittest.mock import Mock
import pandas as pd
from decimal import Decimal

from the_alchemiser.domain.dsl.parser import DSLParser
from the_alchemiser.domain.dsl.evaluator import DSLEvaluator
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


class TestDSLIntegration:
    """Test parser and evaluator integration."""
    
    @pytest.fixture
    def mock_market_data_port(self) -> Mock:
        """Create mock market data port with realistic data."""
        mock_port = Mock(spec=MarketDataPort)
        
        # Mock price data that will result in RSI > 79
        high_rsi_data = pd.DataFrame({
            'close': [100, 102, 105, 108, 112, 115, 118, 120, 122, 125], # Strong uptrend
            'volume': [1000] * 10
        })
        
        # Mock price data that will result in RSI < 79  
        normal_data = pd.DataFrame({
            'close': [100, 101, 100, 102, 101, 103, 102, 104, 103, 105], # Gentle trend
            'volume': [1000] * 10
        })
        
        def mock_get_data(symbol: str, **kwargs):
            if symbol == "HIGH_RSI":
                return high_rsi_data
            else:
                return normal_data
        
        mock_port.get_data.side_effect = mock_get_data
        mock_port.get_current_price.return_value = 105.0
        
        return mock_port
    
    def test_simple_rsi_strategy(self, mock_market_data_port: Mock) -> None:
        """Test a simple RSI-based strategy."""
        # Strategy: if RSI("SPY", 10) > 79 then Asset("UVXY") else Asset("SPY")
        strategy_code = '''
        (if (> (rsi "HIGH_RSI" {:window 10}) 79)
            (asset "UVXY" "High volatility ETF")
            (asset "SPY" "S&P 500 ETF"))
        '''
        
        # Parse the strategy
        parser = DSLParser()
        ast_node = parser.parse(strategy_code)
        
        # Evaluate the strategy
        evaluator = DSLEvaluator(mock_market_data_port)
        result = evaluator.evaluate(ast_node)
        
        # Should choose UVXY since HIGH_RSI has high RSI
        assert isinstance(result, dict)
        assert "UVXY" in result
        assert result["UVXY"] == pytest.approx(Decimal('1.0'))
        
        # Check the trace
        trace = evaluator.get_trace()
        assert len(trace) >= 2  # At least RSI calculation and comparison
        
        # Find the RSI trace entry
        rsi_trace = next((entry for entry in trace if entry["type"] == "indicator" and entry["indicator"] == "rsi"), None)
        assert rsi_trace is not None
        assert rsi_trace["symbol"] == "HIGH_RSI"
        assert rsi_trace["window"] == 10
        assert rsi_trace["value"] > 79  # Should be high RSI
        
        # Find the comparison trace entry
        comparison_trace = next((entry for entry in trace if entry["type"] == "comparison"), None)
        assert comparison_trace is not None
        assert comparison_trace["operator"] == ">"
        assert comparison_trace["result"] is True
    
    def test_equal_weight_portfolio(self, mock_market_data_port: Mock) -> None:
        """Test equal weight portfolio construction."""
        strategy_code = '''
        (weight-equal 
            (asset "SPY" "S&P 500 ETF")
            (asset "QQQ" "Nasdaq ETF")
            (asset "IWM" "Russell 2000 ETF"))
        '''
        
        parser = DSLParser()
        ast_node = parser.parse(strategy_code)
        
        evaluator = DSLEvaluator(mock_market_data_port)
        result = evaluator.evaluate(ast_node)
        
        # Should be equal weight across 3 assets
        assert isinstance(result, dict)
        assert len(result) == 3
        assert abs(result["SPY"] - Decimal('1')/Decimal('3')) < Decimal('1e-9')
        assert abs(result["QQQ"] - Decimal('1')/Decimal('3')) < Decimal('1e-9')
        assert abs(result["IWM"] - Decimal('1')/Decimal('3')) < Decimal('1e-9')
        
        # Check the trace
        trace = evaluator.get_trace()
        portfolio_trace = next((entry for entry in trace if entry["type"] == "portfolio" and entry["operation"] == "weight_equal"), None)
        assert portfolio_trace is not None
        assert portfolio_trace["input_portfolios"] == 3
    
    def test_nested_conditional_strategy(self, mock_market_data_port: Mock) -> None:
        """Test nested conditional strategy similar to Nuclear.clj structure."""
        strategy_code = '''
        (if (> (rsi "SPY" {:window 10}) 79)
            (if (> (rsi "SPY" {:window 10}) 81)
                (asset "UVXY" "ProShares Ultra VIX")
                (weight-equal 
                    (asset "UVXY" "ProShares Ultra VIX")
                    (asset "BTAL" "AGF U.S. Market Neutral")))
            (weight-equal
                (asset "TQQQ" "ProShares UltraPro QQQ")
                (asset "UPRO" "ProShares UltraPro S&P 500")))
        '''
        
        parser = DSLParser()
        ast_node = parser.parse(strategy_code)
        
        evaluator = DSLEvaluator(mock_market_data_port)
        result = evaluator.evaluate(ast_node)
        
        # Should be a valid portfolio
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # All weights should sum to 1.0
        total_weight = sum(result.values())
        assert abs(total_weight - Decimal('1.0')) < Decimal('1e-9')
    
    def test_weight_specified_portfolio(self, mock_market_data_port: Mock) -> None:
        """Test explicitly weighted portfolio."""
        strategy_code = '''
        (weight-specified 
            0.75 (asset "UVXY" "ProShares Ultra VIX")
            0.25 (asset "BTAL" "AGF U.S. Market Neutral"))
        '''
        
        parser = DSLParser()
        ast_node = parser.parse(strategy_code)
        
        evaluator = DSLEvaluator(mock_market_data_port)
        result = evaluator.evaluate(ast_node)
        
        # Should have correct weights
        assert isinstance(result, dict)
        assert len(result) == 2
        assert abs(result["UVXY"] - Decimal('0.75')) < Decimal('1e-9')
        assert abs(result["BTAL"] - Decimal('0.25')) < Decimal('1e-9')
        
        # Total should sum to 1.0
        total_weight = sum(result.values())
        assert abs(total_weight - Decimal('1.0')) < Decimal('1e-9')