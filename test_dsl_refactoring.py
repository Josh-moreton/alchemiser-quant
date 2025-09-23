#!/usr/bin/env python3
"""Regression tests for DSL refactoring.

These tests ensure that the DSL engine behavior remains unchanged
during complexity refactoring.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock

import pytest

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import (
    IndicatorRequestDTO,
    PortfolioFragmentDTO,
)
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.strategy_v2.engines.dsl.dsl_evaluator import (
    DslEvaluationError,
    DslEvaluator,
    IndicatorService,
)
from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser


class TestIndicatorServiceRegression:
    """Test IndicatorService behavior before refactoring."""

    def test_get_indicator_rsi_basic(self):
        """Test basic RSI indicator computation."""
        # Mock market data service
        mock_market_data = Mock()
        mock_bar = Mock()
        mock_bar.close = Decimal("100.0")
        mock_market_data.get_bars.return_value = [mock_bar] * 50

        service = IndicatorService(mock_market_data)
        
        request = IndicatorRequestDTO(
            symbol="TEST",
            indicator_type="rsi",
            parameters={"window": 14}
        )
        
        result = service.get_indicator(request)
        
        assert isinstance(result, TechnicalIndicatorDTO)
        assert result.symbol == "TEST"
        assert result.rsi_14 is not None

    def test_get_indicator_current_price(self):
        """Test current price indicator."""
        mock_market_data = Mock()
        mock_bar = Mock()
        mock_bar.close = Decimal("150.0")
        mock_market_data.get_bars.return_value = [mock_bar]

        service = IndicatorService(mock_market_data)
        
        request = IndicatorRequestDTO(
            symbol="TEST",
            indicator_type="current_price",
            parameters={}
        )
        
        result = service.get_indicator(request)
        
        assert isinstance(result, TechnicalIndicatorDTO)
        assert result.current_price == Decimal("150.0")

    def test_get_indicator_no_market_data_raises(self):
        """Test that missing market data raises error."""
        service = IndicatorService(None)
        
        request = IndicatorRequestDTO(
            symbol="TEST",
            indicator_type="rsi",
            parameters={"window": 14}
        )
        
        with pytest.raises(DslEvaluationError, match="IndicatorService requires a MarketDataPort"):
            service.get_indicator(request)


class TestDslEvaluatorRegression:
    """Test DslEvaluator behavior before refactoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_market_data = Mock()
        self.mock_indicator_service = Mock(spec=IndicatorService)
        self.evaluator = DslEvaluator(self.mock_indicator_service)
        self.correlation_id = str(uuid.uuid4())
        self.trace = TraceDTO(
            trace_id=str(uuid.uuid4()),
            module=__name__,
            function="test",
            timestamp=datetime.now(UTC),
            step_name="test",
            step_status="running",
            metadata={}
        )

    def test_evaluate_node_atom(self):
        """Test evaluation of atomic values."""
        # String atom
        node = ASTNodeDTO.atom("test")
        result = self.evaluator._evaluate_node(node, self.correlation_id, self.trace)
        assert result == "test"

        # Decimal atom
        node = ASTNodeDTO.atom(Decimal("42.5"))
        result = self.evaluator._evaluate_node(node, self.correlation_id, self.trace)
        assert result == Decimal("42.5")

    def test_evaluate_node_symbol(self):
        """Test evaluation of symbols."""
        node = ASTNodeDTO.symbol("test-symbol")
        result = self.evaluator._evaluate_node(node, self.correlation_id, self.trace)
        assert result == "test-symbol"

    def test_evaluate_node_empty_list(self):
        """Test evaluation of empty list."""
        node = ASTNodeDTO.list_node([])
        result = self.evaluator._evaluate_node(node, self.correlation_id, self.trace)
        assert result == []

    def test_evaluate_node_map_literal(self):
        """Test evaluation of map literal."""
        key_node = ASTNodeDTO.symbol(":weight")
        val_node = ASTNodeDTO.atom(Decimal("0.5"))
        
        node = ASTNodeDTO.list_node(
            [key_node, val_node],
            metadata={"node_subtype": "map"}
        )
        
        result = self.evaluator._evaluate_node(node, self.correlation_id, self.trace)
        assert isinstance(result, dict)
        assert result["weight"] == Decimal("0.5")

    def test_eval_filter_basic(self):
        """Test basic filter operation."""
        # Create a simple filter expression: (filter (rsi {:window 14}) (select-top 1) ["A" "B"])
        rsi_node = ASTNodeDTO.list_node([
            ASTNodeDTO.symbol("rsi"),
            ASTNodeDTO.list_node([
                ASTNodeDTO.symbol(":window"),
                ASTNodeDTO.atom(Decimal("14"))
            ], metadata={"node_subtype": "map"})
        ])
        
        selector_node = ASTNodeDTO.list_node([
            ASTNodeDTO.symbol("select-top"),
            ASTNodeDTO.atom(Decimal("1"))
        ])
        
        assets_node = ASTNodeDTO.list_node([
            ASTNodeDTO.atom("A"),
            ASTNodeDTO.atom("B")
        ])
        
        # Mock RSI values for assets
        self.mock_indicator_service.get_indicator.side_effect = [
            TechnicalIndicatorDTO(
                symbol="A",
                timestamp=datetime.now(UTC),
                rsi_14=70.0,
                current_price=Decimal("100"),
                data_source="test",
                metadata={"value": 70.0}
            ),
            TechnicalIndicatorDTO(
                symbol="B", 
                timestamp=datetime.now(UTC),
                rsi_14=30.0,
                current_price=Decimal("100"),
                data_source="test",
                metadata={"value": 30.0}
            )
        ]
        
        result = self.evaluator._eval_filter(
            [rsi_node, selector_node, assets_node],
            self.correlation_id,
            self.trace
        )
        
        assert isinstance(result, PortfolioFragmentDTO)
        assert "A" in result.weights  # A has higher RSI, should be selected
        assert len(result.weights) == 1

    def test_eval_asset_basic(self):
        """Test basic asset evaluation."""
        symbol_node = ASTNodeDTO.atom("TEST")
        result = self.evaluator._eval_asset([symbol_node], self.correlation_id, self.trace)
        assert result == "TEST"

    def test_eval_weight_equal_basic(self):
        """Test equal weight allocation."""
        assets_node = ASTNodeDTO.list_node([
            ASTNodeDTO.atom("A"),
            ASTNodeDTO.atom("B")
        ])
        
        result = self.evaluator._eval_weight_equal([assets_node], self.correlation_id, self.trace)
        
        assert isinstance(result, PortfolioFragmentDTO)
        assert result.weights["A"] == 0.5
        assert result.weights["B"] == 0.5

    def test_coerce_param_value(self):
        """Test parameter value coercion."""
        assert self.evaluator._coerce_param_value(42) == 42
        assert self.evaluator._coerce_param_value(Decimal("3.14")) == Decimal("3.14")
        assert self.evaluator._coerce_param_value("test") == "test"
        assert self.evaluator._coerce_param_value([1, 2, 3]) == "list"

    def test_as_decimal(self):
        """Test decimal conversion."""
        assert self.evaluator._as_decimal(42) == Decimal("42")
        assert self.evaluator._as_decimal(3.14) == Decimal("3.14")
        assert self.evaluator._as_decimal("42.5") == Decimal("42.5")
        assert self.evaluator._as_decimal("invalid") == Decimal("0")
        assert self.evaluator._as_decimal(None) == Decimal("0")


class TestSexprParserRegression:
    """Test SexprParser behavior before refactoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SexprParser()

    def test_tokenize_basic(self):
        """Test basic tokenization."""
        tokens = self.parser.tokenize("(asset \"TEST\")")
        expected = [
            ("LPAREN", "("),
            ("SYMBOL", "asset"),
            ("STRING", "TEST"),
            ("RPAREN", ")")
        ]
        assert tokens == expected

    def test_tokenize_numbers(self):
        """Test number tokenization."""
        tokens = self.parser.tokenize("42 3.14 -5")
        expected = [
            ("NUMBER", "42"),
            ("NUMBER", "3.14"),
            ("NUMBER", "-5")
        ]
        assert tokens == expected

    def test_tokenize_keywords(self):
        """Test keyword tokenization."""
        tokens = self.parser.tokenize(":window :weight")
        expected = [
            ("KEYWORD", ":window"),
            ("KEYWORD", ":weight")
        ]
        assert tokens == expected

    def test_parse_basic_list(self):
        """Test parsing basic list."""
        ast = self.parser.parse("(asset \"TEST\")")
        assert ast.is_list()
        assert len(ast.children) == 2
        assert ast.children[0].is_symbol()
        assert ast.children[0].get_symbol_name() == "asset"
        assert ast.children[1].is_atom()
        assert ast.children[1].get_atom_value() == "TEST"

    def test_parse_nested_list(self):
        """Test parsing nested list."""
        ast = self.parser.parse("(weight-equal [(asset \"A\") (asset \"B\")])")
        assert ast.is_list()
        assert len(ast.children) == 2
        
        # Second child should be a list of assets
        assets_list = ast.children[1]
        assert assets_list.is_list()
        assert len(assets_list.children) == 2

    def test_parse_map(self):
        """Test parsing map literal."""
        ast = self.parser.parse("{:window 14 :symbol \"TEST\"}")
        assert ast.is_list()
        assert ast.metadata["node_subtype"] == "map"
        assert len(ast.children) == 4  # key1, val1, key2, val2


if __name__ == "__main__":
    pytest.main([__file__])