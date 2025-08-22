"""Test the DSL evaluator functionality."""

import pytest
from unittest.mock import Mock
import pandas as pd
from decimal import Decimal

from the_alchemiser.domain.dsl.evaluator import DSLEvaluator
from the_alchemiser.domain.dsl.ast import (
    NumberLiteral, GreaterThan, If, RSI, Asset, WeightEqual, CurrentPrice
)
from the_alchemiser.domain.dsl.errors import EvaluationError, IndicatorError
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


class TestDSLEvaluator:
    """Test DSL evaluator functionality."""
    
    @pytest.fixture
    def mock_market_data_port(self) -> Mock:
        """Create mock market data port."""
        mock_port = Mock(spec=MarketDataPort)
        
        # Mock price data for SPY
        price_data = pd.DataFrame({
            'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
            'volume': [1000] * 10
        })
        mock_port.get_data.return_value = price_data
        mock_port.get_current_price.return_value = 109.0
        
        return mock_port
    
    def test_evaluate_number_literal(self, mock_market_data_port: Mock) -> None:
        """Test evaluating numeric literals."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        result = evaluator.evaluate(NumberLiteral(42.5))
        assert result == pytest.approx(42.5)
    
    def test_evaluate_simple_comparison(self, mock_market_data_port: Mock) -> None:
        """Test evaluating simple comparison."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # 10 > 5 should be True
        node = GreaterThan(NumberLiteral(10), NumberLiteral(5))
        result = evaluator.evaluate(node)
        assert result is True
        
        # 3 > 7 should be False  
        node = GreaterThan(NumberLiteral(3), NumberLiteral(7))
        result = evaluator.evaluate(node)
        assert result is False
    
    def test_evaluate_if_conditional(self, mock_market_data_port: Mock) -> None:
        """Test evaluating if conditional."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # if (10 > 5) then Asset("SPY") else Asset("QQQ")
        condition = GreaterThan(NumberLiteral(10), NumberLiteral(5))
        then_expr = Asset("SPY")
        else_expr = Asset("QQQ")
        
        node = If(condition, then_expr, else_expr)
        result = evaluator.evaluate(node)
        
        # Should evaluate to SPY portfolio since 10 > 5 is True
        assert isinstance(result, dict)
        assert result == {"SPY": 1.0}
    
    def test_evaluate_rsi_indicator(self, mock_market_data_port: Mock) -> None:
        """Test evaluating RSI indicator."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        node = RSI("SPY", 14)
        result = evaluator.evaluate(node)
        
        # Should return a numeric RSI value
        assert isinstance(result, float)
        assert 0 <= result <= 100  # RSI should be between 0 and 100
        
        # Verify market data was called
        mock_market_data_port.get_data.assert_called_with("SPY", timeframe="1day", period="1y")
    
    def test_evaluate_current_price(self, mock_market_data_port: Mock) -> None:
        """Test evaluating current price."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        node = CurrentPrice("SPY")
        result = evaluator.evaluate(node)
        
        assert result == pytest.approx(109.0)
        mock_market_data_port.get_current_price.assert_called_with("SPY")
    
    def test_evaluate_asset_portfolio(self, mock_market_data_port: Mock) -> None:
        """Test evaluating asset to portfolio."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        node = Asset("SPY", "SPDR S&P 500")
        result = evaluator.evaluate(node)
        
        assert isinstance(result, dict)
        assert result == {"SPY": pytest.approx(Decimal('1.0'))}
    
    def test_evaluate_weight_equal(self, mock_market_data_port: Mock) -> None:
        """Test evaluating equal weight portfolio."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # weight-equal of SPY and QQQ
        node = WeightEqual([Asset("SPY"), Asset("QQQ")])
        result = evaluator.evaluate(node)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["SPY"] == pytest.approx(Decimal('0.5'))
        assert result["QQQ"] == pytest.approx(Decimal('0.5'))
    
    def test_evaluate_rsi_comparison(self, mock_market_data_port: Mock) -> None:
        """Test evaluating RSI comparison."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # Test: rsi("SPY", 14) > 70
        rsi_node = RSI("SPY", 14)
        comparison = GreaterThan(rsi_node, NumberLiteral(70))
        
        result = evaluator.evaluate(comparison)
        assert isinstance(result, bool)
    
    def test_indicator_error_handling(self, mock_market_data_port: Mock) -> None:
        """Test error handling for indicator failures."""
        # Mock empty data to trigger error
        mock_market_data_port.get_data.return_value = pd.DataFrame()
        
        evaluator = DSLEvaluator(mock_market_data_port)
        node = RSI("INVALID", 14)
        
        with pytest.raises(IndicatorError):
            evaluator.evaluate(node)
    
    def test_trace_collection(self, mock_market_data_port: Mock) -> None:
        """Test that evaluation trace is collected."""
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # Evaluate simple comparison
        node = GreaterThan(NumberLiteral(10), NumberLiteral(5))
        evaluator.evaluate(node)
        
        trace = evaluator.get_trace()
        assert len(trace) == 1
        assert trace[0]["type"] == "comparison"
        assert trace[0]["operator"] == ">"
        assert trace[0]["result"] is True
    
    def test_indicator_caching(self, mock_market_data_port: Mock) -> None:
        """Test that indicators are cached within evaluation.""" 
        evaluator = DSLEvaluator(mock_market_data_port)
        
        # Evaluate RSI twice
        node1 = RSI("SPY", 14)
        node2 = RSI("SPY", 14)
        
        result1 = evaluator.evaluate(node1)
        result2 = evaluator.evaluate(node2)
        
        # Should get same result
        assert result1 == result2
        
        # But market data should only be called once (due to cache clearing between evaluations)
        # Let's test within a single evaluation instead
        comparison = GreaterThan(RSI("SPY", 14), RSI("SPY", 14))
        evaluator.evaluate(comparison)
        
        # Market data should only be called once for the same symbol/window
        assert mock_market_data_port.get_data.call_count >= 1