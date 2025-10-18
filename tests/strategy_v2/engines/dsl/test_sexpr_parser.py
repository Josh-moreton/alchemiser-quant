"""Business Unit: strategy | Status: current.

Test S-expression parser for DSL engine.

Tests parsing of Clojure-style S-expressions into ASTNode structures,
including valid expressions, error handling, and edge cases.
"""

from decimal import Decimal

import pytest

from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import (
    SexprParseError,
    SexprParser,
)


@pytest.mark.unit
@pytest.mark.dsl
class TestSexprParser:
    """Test S-expression parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return SexprParser()

    def test_parse_atom_integer(self, parser):
        """Test parsing integer atom."""
        ast = parser.parse("42")
        assert ast.is_atom()
        assert ast.get_atom_value() == Decimal("42")

    def test_parse_atom_float(self, parser):
        """Test parsing float atom."""
        ast = parser.parse("3.14")
        assert ast.is_atom()
        assert ast.get_atom_value() == Decimal("3.14")

    def test_parse_atom_negative(self, parser):
        """Test parsing negative number."""
        ast = parser.parse("-10")
        assert ast.is_atom()
        assert ast.get_atom_value() == Decimal("-10")

    def test_parse_atom_string(self, parser):
        """Test parsing string atom."""
        ast = parser.parse('"hello"')
        assert ast.is_atom()
        assert ast.get_atom_value() == "hello"

    def test_parse_symbol(self, parser):
        """Test parsing symbol."""
        ast = parser.parse("weight-equal")
        assert ast.is_symbol()
        assert ast.get_symbol_name() == "weight-equal"

    def test_parse_simple_list(self, parser):
        """Test parsing simple list."""
        ast = parser.parse("(+ 1 2)")
        assert ast.is_list()
        assert len(ast.children) == 3
        assert ast.children[0].get_symbol_name() == "+"
        assert ast.children[1].get_atom_value() == Decimal("1")
        assert ast.children[2].get_atom_value() == Decimal("2")

    def test_parse_nested_list(self, parser):
        """Test parsing nested list."""
        ast = parser.parse("(+ (- 5 3) 2)")
        assert ast.is_list()
        assert len(ast.children) == 3
        assert ast.children[0].get_symbol_name() == "+"

        # Check nested expression
        nested = ast.children[1]
        assert nested.is_list()
        assert nested.children[0].get_symbol_name() == "-"

    def test_parse_vector(self, parser):
        """Test parsing vector (square brackets)."""
        ast = parser.parse('["AAPL" "GOOGL" "MSFT"]')
        assert ast.is_list()
        assert len(ast.children) == 3
        assert ast.children[0].get_atom_value() == "AAPL"

    def test_parse_map(self, parser):
        """Test parsing map literal."""
        ast = parser.parse("{:window 14}")
        assert ast.is_list()
        assert ast.metadata and ast.metadata.get("node_subtype") == "map"

    def test_parse_keyword(self, parser):
        """Test parsing keyword."""
        ast = parser.parse(":window")
        assert ast.is_symbol()
        assert ast.get_symbol_name() == ":window"

    def test_parse_with_comments(self, parser):
        """Test parsing with comments."""
        ast = parser.parse("(+ 1 2) ; add numbers")
        assert ast.is_list()
        assert len(ast.children) == 3

    def test_parse_with_whitespace(self, parser):
        """Test parsing with various whitespace."""
        ast = parser.parse("  (  +   1    2  )  ")
        assert ast.is_list()
        assert len(ast.children) == 3

    def test_parse_defsymphony(self, parser):
        """Test parsing defsymphony expression."""
        code = '(defsymphony "test" {} (weight-equal "AAPL"))'
        ast = parser.parse(code)
        assert ast.is_list()
        assert ast.children[0].get_symbol_name() == "defsymphony"
        assert ast.children[1].get_atom_value() == "test"

    def test_parse_if_expression(self, parser):
        """Test parsing if expression."""
        code = "(if (> x 50) a b)"
        ast = parser.parse(code)
        assert ast.is_list()
        assert ast.children[0].get_symbol_name() == "if"

        condition = ast.children[1]
        assert condition.is_list()
        assert condition.children[0].get_symbol_name() == ">"

    def test_parse_empty_list(self, parser):
        """Test parsing empty list."""
        ast = parser.parse("()")
        assert ast.is_list()
        assert len(ast.children) == 0

    def test_parse_error_empty_input(self, parser):
        """Test error on empty input."""
        with pytest.raises(SexprParseError, match="Empty input"):
            parser.parse("")

    def test_parse_error_unexpected_rparen(self, parser):
        """Test error on unexpected right paren."""
        with pytest.raises(SexprParseError):
            parser.parse(")")

    def test_parse_error_unclosed_paren(self, parser):
        """Test error on unclosed parenthesis."""
        with pytest.raises(SexprParseError):
            parser.parse("(+ 1 2")

    def test_parse_error_unclosed_string(self, parser):
        """Test error on unclosed string."""
        with pytest.raises(SexprParseError):
            parser.parse('"hello')

    def test_parse_error_unexpected_tokens(self, parser):
        """Test error on unexpected tokens after expression."""
        with pytest.raises(SexprParseError, match="Unexpected tokens"):
            parser.parse("(+ 1 2) extra")

    def test_tokenize_basic(self, parser):
        """Test tokenization of basic expression."""
        tokens = parser.tokenize("(+ 1 2)")
        assert len(tokens) == 5
        assert tokens[0] == ("(", "LPAREN")
        assert tokens[1] == ("+", "SYMBOL")
        assert tokens[2] == ("1", "INTEGER")

    def test_tokenize_string_with_escaped_quotes(self, parser):
        """Test tokenization of string with escaped quotes."""
        tokens = parser.tokenize(r'"hello \"world\""')
        assert len(tokens) == 1
        assert tokens[0][1] == "STRING"

    def test_parse_comparison_operators(self, parser):
        """Test parsing comparison operators."""
        for op in [">", "<", ">=", "<=", "="]:
            ast = parser.parse(f"({op} x y)")
            assert ast.is_list()
            assert ast.children[0].get_symbol_name() == op

    def test_parse_file_not_found(self, parser):
        """Test parse_file with non-existent file."""
        with pytest.raises(Exception):  # FileNotFoundError or similar
            parser.parse_file("/nonexistent/file.clj")


@pytest.mark.unit
@pytest.mark.dsl
@pytest.mark.property
class TestSexprParserPropertyBased:
    """Property-based tests for parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return SexprParser()

    def test_parse_roundtrip_atoms(self, parser):
        """Test that parsing atoms produces valid AST nodes."""
        test_cases = [
            ("42", Decimal("42")),
            ("-100", Decimal("-100")),
            ("3.14", Decimal("3.14")),
            ('"test"', "test"),
        ]

        for input_str, expected_value in test_cases:
            ast = parser.parse(input_str)
            assert ast.is_atom()
            assert ast.get_atom_value() == expected_value

    def test_parse_nested_depth(self, parser):
        """Test parsing expressions with varying nesting depth."""
        # Depth 1
        ast1 = parser.parse("(+ 1 2)")
        assert ast1.is_list()

        # Depth 2
        ast2 = parser.parse("(+ (+ 1 2) 3)")
        assert ast2.is_list()
        assert ast2.children[1].is_list()

        # Depth 3
        ast3 = parser.parse("(+ (+ (+ 1 2) 3) 4)")
        assert ast3.is_list()
        assert ast3.children[1].is_list()
        assert ast3.children[1].children[1].is_list()
