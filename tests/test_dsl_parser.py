"""Test the DSL parser functionality."""

import pytest

from the_alchemiser.domain.dsl.parser import DSLParser
from the_alchemiser.domain.dsl.ast import (
    NumberLiteral, Symbol, GreaterThan, If, RSI, Asset, WeightEqual
)
from the_alchemiser.domain.dsl.errors import ParseError, SchemaError


class TestDSLParser:
    """Test DSL parser functionality."""
    
    def test_parse_number_literal(self) -> None:
        """Test parsing numeric literals."""
        parser = DSLParser()
        
        # Integer
        result = parser.parse("42")
        assert isinstance(result, NumberLiteral)
        assert result.value == 42.0
        
        # Float  
        result = parser.parse("3.14")
        assert isinstance(result, NumberLiteral)
        assert result.value == 3.14
    
    def test_parse_symbol(self) -> None:
        """Test parsing symbols."""
        parser = DSLParser()
        
        result = parser.parse("SPY")
        assert isinstance(result, Symbol)
        assert result.name == "SPY"
    
    def test_parse_simple_comparison(self) -> None:
        """Test parsing simple comparison."""
        parser = DSLParser()
        
        result = parser.parse("(> 10 5)")
        assert isinstance(result, GreaterThan)
        assert isinstance(result.left, NumberLiteral)
        assert isinstance(result.right, NumberLiteral)
        assert result.left.value == 10.0
        assert result.right.value == 5.0
    
    def test_parse_rsi_with_window(self) -> None:
        """Test parsing RSI with window parameter."""
        parser = DSLParser()
        
        # Test with Clojure map parameter
        result = parser.parse('(rsi "SPY" {:window 10})')
        assert isinstance(result, RSI)
        assert result.symbol == "SPY"
        assert result.window == 10
    
    def test_parse_asset(self) -> None:
        """Test parsing asset definition."""
        parser = DSLParser()
        
        result = parser.parse('(asset "SPY")')
        assert isinstance(result, Asset) 
        assert result.symbol == "SPY"
        assert result.name is None
        
        result = parser.parse('(asset "SPY" "SPDR S&P 500")')
        assert isinstance(result, Asset)
        assert result.symbol == "SPY"
        assert result.name == "SPDR S&P 500"
    
    def test_parse_weight_equal(self) -> None:
        """Test parsing equal weight portfolio."""
        parser = DSLParser()
        
        result = parser.parse('(weight-equal (asset "SPY") (asset "QQQ"))')
        assert isinstance(result, WeightEqual)
        assert len(result.expressions) == 2
        assert all(isinstance(expr, Asset) for expr in result.expressions)
    
    def test_parse_if_conditional(self) -> None:
        """Test parsing if conditional."""
        parser = DSLParser()
        
        result = parser.parse('(if (> 10 5) (asset "SPY") (asset "QQQ"))')
        assert isinstance(result, If)
        assert isinstance(result.condition, GreaterThan)
        assert isinstance(result.then_expr, Asset)
        assert isinstance(result.else_expr, Asset)
    
    def test_empty_expression_error(self) -> None:
        """Test error on empty expression."""
        parser = DSLParser()
        
        with pytest.raises(ParseError, match="Empty expression"):
            parser.parse("")
        
        with pytest.raises(ParseError, match="Empty list expression"):
            parser.parse("()")
    
    def test_unmatched_parentheses_error(self) -> None:
        """Test error on unmatched parentheses."""
        parser = DSLParser()
        
        with pytest.raises(ParseError, match="Missing closing parenthesis"):
            parser.parse("(> 10 5")
        
        with pytest.raises(ParseError, match="Unexpected closing parenthesis"):
            parser.parse(")")
    
    def test_arity_validation(self) -> None:
        """Test arity validation for constructs."""
        parser = DSLParser()
        
        # > requires exactly 2 arguments
        with pytest.raises(SchemaError, match="> requires exactly 2 arguments"):
            parser.parse("(> 10)")
        
        with pytest.raises(SchemaError, match="> requires exactly 2 arguments"):
            parser.parse("(> 10 5 3)")
    
    def test_depth_limit(self) -> None:
        """Test AST depth limit protection.""" 
        parser = DSLParser()
        
        # Create deeply nested expression
        deep_expr = "x"
        for _ in range(parser.MAX_DEPTH + 1):
            deep_expr = f"(if true {deep_expr} false)"
        
        with pytest.raises(ParseError, match="Maximum AST depth exceeded"):
            parser.parse(deep_expr)