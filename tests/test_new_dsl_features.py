#!/usr/bin/env python3
"""
Additional tests for new DSL functionality.
"""

import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import Mock

from the_alchemiser.domain.dsl.parser import DSLParser
from the_alchemiser.domain.dsl.evaluator import DSLEvaluator
from the_alchemiser.domain.dsl.ast import StdevReturn, SelectTop, SelectBottom
from the_alchemiser.domain.dsl.errors import SchemaError, IndicatorError


class TestNewDSLFeatures:
    """Test new DSL features: stdev-return, select-top, select-bottom, and complete filter functionality."""

    @pytest.fixture
    def mock_market_data(self):
        """Create mock market data for testing."""
        mock_port = Mock()
        
        # Create sufficient data for indicators
        prices = [100 + i * 0.5 + (i % 5 - 2) * 2 for i in range(100)]
        test_data = pd.DataFrame({'close': prices})
        
        mock_port.get_data.return_value = test_data
        mock_port.get_current_price.return_value = prices[-1]
        
        return mock_port

    @pytest.fixture
    def parser(self):
        """Create DSL parser."""
        return DSLParser()

    @pytest.fixture
    def evaluator(self, mock_market_data):
        """Create DSL evaluator with mock data."""
        return DSLEvaluator(mock_market_data)

    def test_parse_stdev_return_with_symbol(self, parser):
        """Test parsing stdev-return with symbol and window."""
        code = '(stdev-return "SPY" {:window 10})'
        ast = parser.parse(code)
        
        assert isinstance(ast, StdevReturn)
        assert ast.symbol == "SPY"
        assert ast.window == 10

    def test_parse_stdev_return_filter_context(self, parser):
        """Test parsing stdev-return in filter context (no symbol)."""
        code = '(stdev-return {:window 5})'
        ast = parser.parse(code)
        
        assert isinstance(ast, StdevReturn)
        assert ast.symbol == ""  # Empty symbol for filter context
        assert ast.window == 5

    def test_parse_select_top(self, parser):
        """Test parsing select-top selector."""
        code = '(select-top 3)'
        ast = parser.parse(code)
        
        assert isinstance(ast, SelectTop)
        assert ast.count == 3

    def test_parse_select_bottom(self, parser):
        """Test parsing select-bottom selector."""
        code = '(select-bottom 2)'
        ast = parser.parse(code)
        
        assert isinstance(ast, SelectBottom)
        assert ast.count == 2

    def test_parse_filter_with_select_top(self, parser):
        """Test parsing complete filter with select-top."""
        code = '''
        (filter
            (rsi {:window 10})
            (select-top 2)
            (asset "SPY" "SPDR S&P 500 ETF")
            (asset "QQQ" "Invesco QQQ Trust"))
        '''
        
        ast = parser.parse(code)
        assert ast.__class__.__name__ == "Filter"
        assert isinstance(ast.selector, SelectTop)
        assert ast.selector.count == 2

    def test_parse_filter_with_select_bottom(self, parser):
        """Test parsing complete filter with select-bottom."""
        code = '''
        (filter
            (stdev-return {:window 5})
            (select-bottom 1)
            (asset "SPY" nil)
            (asset "QQQ" nil))
        '''
        
        ast = parser.parse(code)
        assert ast.__class__.__name__ == "Filter"
        assert isinstance(ast.selector, SelectBottom)
        assert ast.selector.count == 1

    def test_evaluate_stdev_return(self, evaluator):
        """Test evaluation of stdev-return indicator."""
        from the_alchemiser.domain.dsl.ast import StdevReturn
        
        node = StdevReturn("SPY", 10)
        result = evaluator.evaluate(node)
        
        assert isinstance(result, float)
        assert result > 0  # Standard deviation should be positive

    def test_evaluate_filter_select_top(self, evaluator, parser):
        """Test evaluation of filter with select-top."""
        code = '''
        (filter
            (rsi {:window 10})
            (select-top 2)
            (asset "SPY" "SPDR S&P 500 ETF")
            (asset "QQQ" "Invesco QQQ Trust")
            (asset "IWM" "iShares Russell 2000 ETF"))
        '''
        
        ast = parser.parse(code)
        result = evaluator.evaluate(ast)
        
        assert isinstance(result, dict)
        assert len(result) == 2  # Should select top 2
        assert all(isinstance(v, Decimal) for v in result.values())
        
        # Check that weights sum to 1.0
        total_weight = sum(result.values())
        assert abs(total_weight - Decimal('1.0')) < Decimal('0.0001')

    def test_evaluate_filter_select_bottom(self, evaluator, parser):
        """Test evaluation of filter with select-bottom."""
        code = '''
        (filter
            (stdev-return {:window 5})
            (select-bottom 1)
            (asset "SPY" nil)
            (asset "QQQ" nil)
            (asset "TLT" nil))
        '''
        
        ast = parser.parse(code)
        result = evaluator.evaluate(ast)
        
        assert isinstance(result, dict)
        assert len(result) == 1  # Should select bottom 1
        assert all(isinstance(v, Decimal) for v in result.values())
        
        # Check that weights sum to 1.0
        total_weight = sum(result.values())
        assert abs(total_weight - Decimal('1.0')) < Decimal('0.0001')

    def test_stdev_return_error_handling(self, parser):
        """Test error handling for stdev-return parsing."""
        # Test invalid arity
        with pytest.raises(SchemaError, match="requires 1 argument.*or 2 arguments"):
            parser.parse('(stdev-return)')
            
        with pytest.raises(SchemaError, match="requires 1 argument.*or 2 arguments"):
            parser.parse('(stdev-return "SPY" {:window 10} "extra")')

    def test_selector_error_handling(self, parser):
        """Test error handling for selector parsing."""
        # Test invalid arity for select-top
        with pytest.raises(SchemaError, match="select-top requires 1 argument"):
            parser.parse('(select-top)')
            
        # Test invalid arity for select-bottom
        with pytest.raises(SchemaError, match="select-bottom requires 1 argument"):
            parser.parse('(select-bottom)')
            
        # Test non-positive count
        with pytest.raises(SchemaError, match="must be a positive integer"):
            parser.parse('(select-top 0)')
            
        with pytest.raises(SchemaError, match="must be a positive integer"):
            parser.parse('(select-bottom -1)')

    def test_filter_error_handling(self, parser):
        """Test error handling for filter parsing."""
        # Test insufficient arguments
        with pytest.raises(SchemaError, match="filter requires at least 3 arguments"):
            parser.parse('(filter (rsi {:window 10}))')

    def test_indicator_caching_stdev_return(self, evaluator):
        """Test that stdev-return indicators are cached properly."""
        from the_alchemiser.domain.dsl.ast import StdevReturn
        
        node = StdevReturn("SPY", 10)
        
        # First evaluation
        result1 = evaluator._evaluate_stdev_return(node)
        
        # Second evaluation should use cached value (call _evaluate_stdev_return directly
        # to avoid clearing the cache that happens in the main evaluate method)
        result2 = evaluator._evaluate_stdev_return(node)
        
        assert result1 == result2
        # Market data should only be called once due to caching
        assert evaluator.market_data_port.get_data.call_count == 1

    def test_trace_collection_new_features(self, evaluator, parser):
        """Test that trace collection works for new features."""
        code = '''
        (filter
            (stdev-return {:window 5})
            (select-bottom 2)
            (asset "SPY" nil)
            (asset "QQQ" nil)
            (asset "TLT" nil))
        '''
        
        ast = parser.parse(code)
        result = evaluator.evaluate(ast)
        trace = evaluator.get_trace()
        
        assert len(trace) > 0
        
        # Check for stdev-return indicator traces
        indicator_traces = [t for t in trace if t.get('type') == 'indicator' and t.get('indicator') == 'stdev_return']
        assert len(indicator_traces) == 3  # One for each asset
        
        # Check for filter operation trace
        filter_traces = [t for t in trace if t.get('type') == 'portfolio' and t.get('operation') == 'filter']
        assert len(filter_traces) == 1
        
        filter_trace = filter_traces[0]
        assert filter_trace['selector_type'] == 'bottom'
        assert filter_trace['selector_count'] == 2
        assert filter_trace['total_assets'] == 3
        assert len(filter_trace['selected_assets']) == 2

    def test_nuclear_clj_compatibility(self, evaluator, parser):
        """Test compatibility with Nuclear.clj constructs."""
        # Test RSI in filter context (no symbol specified)
        code = '''
        (filter
            (moving-average-return {:window 90})
            (select-top 3)
            (asset "SMR" nil)
            (asset "BWXT" nil)
            (asset "LEU" nil)
            (asset "EXC" nil))
        '''
        
        ast = parser.parse(code)
        result = evaluator.evaluate(ast)
        
        assert isinstance(result, dict)
        assert len(result) == 3

    def test_klm_clj_compatibility(self, evaluator, parser):
        """Test compatibility with KLM.clj constructs."""
        # Test stdev-return with select-bottom
        code = '''
        (filter
            (stdev-return {:window 6})
            (select-bottom 3)
            (asset "UUP" "Invesco DB US Dollar Index Bullish Fund")
            (asset "FTLS" "First Trust Long/Short Equity ETF")
            (asset "KMLM" "KFA Mount Lucas Managed Futures Index Strategy ETF")
            (asset "SVXY" nil)
            (asset "VIXM" nil))
        '''
        
        ast = parser.parse(code)
        result = evaluator.evaluate(ast)
        
        assert isinstance(result, dict)
        assert len(result) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])