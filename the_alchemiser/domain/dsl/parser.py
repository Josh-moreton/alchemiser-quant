"""
S-expression parser for the Strategy DSL.

Provides a minimal, secure S-expression reader with schema validation.
Converts S-expressions into typed AST nodes without using eval().
"""

from __future__ import annotations

import re
from typing import Any, Union

from the_alchemiser.domain.dsl.ast import (
    ASTNode, ASTNodeType, Asset, CumulativeReturn, CurrentPrice, Filter,
    FunctionCall, GreaterThan, Group, If, LessThan, MovingAveragePrice,
    MovingAverageReturn, NumberLiteral, RSI, Strategy, Symbol,
    WeightEqual, WeightInverseVolatility, WeightSpecified
)
from the_alchemiser.domain.dsl.errors import ParseError, SchemaError


# Type for raw S-expression elements
SExpr = Union[str, int, float, list['SExpr']]


class DSLParser:
    """S-expression parser with schema validation for trading strategy DSL."""
    
    # Maximum AST depth to prevent stack overflow attacks
    MAX_DEPTH = 50
    # Maximum number of nodes to prevent memory exhaustion
    MAX_NODES = 10000
    
    def __init__(self) -> None:
        self._node_count = 0
        
    def parse(self, source: str) -> ASTNode:
        """Parse S-expression source into an AST.
        
        Args:
            source: S-expression source code
            
        Returns:
            Parsed AST node
            
        Raises:
            ParseError: If parsing fails
            SchemaError: If schema validation fails
        """
        self._node_count = 0
        
        try:
            sexpr = self._parse_sexpr(source.strip())
            return self._sexpr_to_ast(sexpr, depth=0)
        except (ParseError, SchemaError):
            raise
        except Exception as e:
            raise ParseError(f"Unexpected parsing error: {e}", expression=source) from e
    
    def _parse_sexpr(self, source: str) -> SExpr:
        """Parse source string into nested lists and atoms."""
        source = source.strip()
        if not source:
            raise ParseError("Empty expression")
            
        tokens = self._tokenize(source)
        if not tokens:
            raise ParseError("No tokens found")
            
        result, remaining = self._parse_tokens(tokens)
        if remaining:
            raise ParseError(f"Unexpected tokens remaining: {remaining}")
            
        return result
    
    def _tokenize(self, source: str) -> list[str]:
        """Tokenize S-expression source."""
        # Remove Clojure-style comments (;; comment text)
        lines = source.split('\n')
        clean_lines = []
        for line in lines:
            comment_pos = line.find(';;')
            if comment_pos >= 0:
                line = line[:comment_pos]
            clean_lines.append(line)
        
        clean_source = '\n'.join(clean_lines)
        
        # Enhanced tokenizer - handles parentheses, braces, and quoted strings
        token_pattern = r'\{|\}|\(|\)|"[^"]*"|[^\s(){}"]+' 
        tokens = re.findall(token_pattern, clean_source)
        return [t for t in tokens if t.strip()]
    
    def _parse_tokens(self, tokens: list[str]) -> tuple[SExpr, list[str]]:
        """Parse tokens into S-expression."""
        if not tokens:
            raise ParseError("Unexpected end of input")
            
        token = tokens[0]
        remaining = tokens[1:]
        
        if token == '(':
            # Parse list
            elements = []
            while remaining and remaining[0] != ')':
                element, remaining = self._parse_tokens(remaining)
                elements.append(element)
            
            if not remaining or remaining[0] != ')':
                raise ParseError("Missing closing parenthesis")
                
            return elements, remaining[1:]  # Skip closing ')'
            
        elif token == '{':
            # Parse Clojure map {:key value ...}
            map_dict = {}
            while remaining and remaining[0] != '}':
                # Parse key
                key, remaining = self._parse_tokens(remaining)
                if not remaining:
                    raise ParseError("Missing value in map")
                # Parse value
                value, remaining = self._parse_tokens(remaining)
                map_dict[str(key)] = value
            
            if not remaining or remaining[0] != '}':
                raise ParseError("Missing closing brace")
                
            return map_dict, remaining[1:]  # Skip closing '}'
            
        elif token in (')', '}'):
            raise ParseError(f"Unexpected closing {token}")
            
        else:
            # Parse atom
            return self._parse_atom(token), remaining
    
    def _parse_atom(self, token: str) -> Union[str, int, float]:
        """Parse atomic token (number, string, symbol)."""
        # Handle quoted strings
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]  # Remove quotes
        
        # Handle keywords (Clojure style)
        if token.startswith(':'):
            return token  # Keep the colon for keywords
        
        # Try to parse as number
        try:
            if '.' in token:
                return float(token)
            else:
                return int(token)
        except ValueError:
            pass
            
        # Return as string/symbol
        return token
    
    def _sexpr_to_ast(self, sexpr: SExpr, depth: int) -> ASTNode:
        """Convert S-expression to AST node."""
        if depth > self.MAX_DEPTH:
            raise ParseError(f"Maximum AST depth exceeded: {self.MAX_DEPTH}")
            
        self._node_count += 1
        if self._node_count > self.MAX_NODES:
            raise ParseError(f"Maximum node count exceeded: {self.MAX_NODES}")
        
        # Atomic values
        if isinstance(sexpr, (int, float)):
            return NumberLiteral(float(sexpr))
        elif isinstance(sexpr, str):
            return Symbol(sexpr)
        elif not isinstance(sexpr, list):
            raise ParseError(f"Unexpected S-expression type: {type(sexpr)}")
        
        # Empty list
        if not sexpr:
            raise ParseError("Empty list expression")
        
        # List expressions - first element is the operator/function
        operator = sexpr[0]
        args = sexpr[1:]
        
        if isinstance(operator, str):
            return self._parse_construct(operator, args, depth)
        else:
            raise ParseError(f"Operator must be a symbol, got: {type(operator)}")
    
    def _parse_construct(self, operator: str, args: list[SExpr], depth: int) -> ASTNode:
        """Parse a specific DSL construct."""
        
        # Control flow
        if operator == "if":
            return self._parse_if(args, depth)
        elif operator == ">":
            return self._parse_comparison(GreaterThan, args, depth)
        elif operator == "<":
            return self._parse_comparison(LessThan, args, depth)
            
        # Indicators  
        elif operator == "rsi":
            return self._parse_rsi(args, depth)
        elif operator == "moving-average-price":
            return self._parse_moving_average_price(args, depth)
        elif operator == "moving-average-return":
            return self._parse_moving_average_return(args, depth)
        elif operator == "cumulative-return":
            return self._parse_cumulative_return(args, depth)
        elif operator == "current-price":
            return self._parse_current_price(args, depth)
            
        # Portfolio construction
        elif operator == "asset":
            return self._parse_asset(args, depth)
        elif operator == "group":
            return self._parse_group(args, depth)
        elif operator == "weight-equal":
            return self._parse_weight_equal(args, depth)
        elif operator == "weight-specified":
            return self._parse_weight_specified(args, depth)
        elif operator == "weight-inverse-volatility":
            return self._parse_weight_inverse_volatility(args, depth)
            
        # Selectors
        elif operator == "filter":
            return self._parse_filter(args, depth)
            
        # Strategy root
        elif operator == "defsymphony":
            return self._parse_strategy(args, depth)
            
        else:
            # Generic function call for extensibility
            parsed_args = [self._sexpr_to_ast(arg, depth + 1) for arg in args]
            return FunctionCall(operator, parsed_args)
    
    def _parse_if(self, args: list[SExpr], depth: int) -> If:
        """Parse if conditional."""
        if len(args) < 2 or len(args) > 3:
            raise SchemaError(
                "if requires 2-3 arguments: condition, then_expr, [else_expr]",
                construct="if",
                expected_arity="2-3",
                actual_arity=len(args)
            )
        
        condition = self._sexpr_to_ast(args[0], depth + 1)
        then_expr = self._sexpr_to_ast(args[1], depth + 1)
        else_expr = self._sexpr_to_ast(args[2], depth + 1) if len(args) > 2 else None
        
        return If(condition, then_expr, else_expr)
    
    def _parse_comparison(self, node_type: type[GreaterThan] | type[LessThan], args: list[SExpr], depth: int) -> Union[GreaterThan, LessThan]:
        """Parse comparison operator."""
        if len(args) != 2:
            op_name = ">" if node_type == GreaterThan else "<"
            raise SchemaError(
                f"{op_name} requires exactly 2 arguments",
                construct=op_name,
                expected_arity=2,
                actual_arity=len(args)
            )
        
        left = self._sexpr_to_ast(args[0], depth + 1)
        right = self._sexpr_to_ast(args[1], depth + 1)
        
        return node_type(left, right)
    
    def _parse_rsi(self, args: list[SExpr], depth: int) -> RSI:
        """Parse RSI indicator."""
        if len(args) != 2:
            raise SchemaError(
                "rsi requires 2 arguments: symbol, window_spec",
                construct="rsi",
                expected_arity=2,
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("rsi symbol must be a string")
        
        window = self._extract_window(args[1])
        return RSI(symbol, window)
    
    def _parse_moving_average_price(self, args: list[SExpr], depth: int) -> MovingAveragePrice:
        """Parse moving average price indicator."""
        if len(args) != 2:
            raise SchemaError(
                "moving-average-price requires 2 arguments: symbol, window",
                construct="moving-average-price",
                expected_arity=2,
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("moving-average-price symbol must be a string")
        
        window = self._extract_window(args[1])
        return MovingAveragePrice(symbol, window)
    
    def _parse_moving_average_return(self, args: list[SExpr], depth: int) -> MovingAverageReturn:
        """Parse moving average return indicator."""
        if len(args) != 2:
            raise SchemaError(
                "moving-average-return requires 2 arguments: symbol, window",
                construct="moving-average-return", 
                expected_arity=2,
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("moving-average-return symbol must be a string")
        
        window = self._extract_window(args[1])
        return MovingAverageReturn(symbol, window)
    
    def _parse_cumulative_return(self, args: list[SExpr], depth: int) -> CumulativeReturn:
        """Parse cumulative return indicator."""
        if len(args) != 2:
            raise SchemaError(
                "cumulative-return requires 2 arguments: symbol, window",
                construct="cumulative-return",
                expected_arity=2,
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("cumulative-return symbol must be a string")
        
        window = self._extract_window(args[1])
        return CumulativeReturn(symbol, window)
    
    def _parse_current_price(self, args: list[SExpr], depth: int) -> CurrentPrice:
        """Parse current price indicator."""
        if len(args) != 1:
            raise SchemaError(
                "current-price requires 1 argument: symbol",
                construct="current-price",
                expected_arity=1,
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("current-price symbol must be a string")
        
        return CurrentPrice(symbol)
    
    def _parse_asset(self, args: list[SExpr], depth: int) -> Asset:
        """Parse asset definition.""" 
        if len(args) < 1 or len(args) > 2:
            raise SchemaError(
                "asset requires 1-2 arguments: symbol, [name]",
                construct="asset",
                expected_arity="1-2",
                actual_arity=len(args)
            )
        
        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("asset symbol must be a string")
        
        name = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        return Asset(symbol, name)
    
    def _parse_group(self, args: list[SExpr], depth: int) -> Group:
        """Parse group wrapper."""
        if len(args) < 2:
            raise SchemaError(
                "group requires at least 2 arguments: name, expressions...",
                construct="group",
                expected_arity="2+",
                actual_arity=len(args)
            )
        
        name = args[0]
        if not isinstance(name, str):
            raise SchemaError("group name must be a string")
        
        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args[1:]]
        return Group(name, expressions)
    
    def _parse_weight_equal(self, args: list[SExpr], depth: int) -> WeightEqual:
        """Parse equal weight portfolio."""
        if not args:
            raise SchemaError(
                "weight-equal requires at least 1 argument",
                construct="weight-equal",
                expected_arity="1+",
                actual_arity=0
            )
        
        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args]
        return WeightEqual(expressions)
    
    def _parse_weight_specified(self, args: list[SExpr], depth: int) -> WeightSpecified:
        """Parse explicitly weighted portfolio."""
        if len(args) % 2 != 0:
            raise SchemaError(
                "weight-specified requires pairs of weight, expression arguments",
                construct="weight-specified"
            )
        
        if len(args) < 2:
            raise SchemaError(
                "weight-specified requires at least one weight, expression pair",
                construct="weight-specified"
            )
        
        weights_and_expressions = []
        for i in range(0, len(args), 2):
            weight = args[i]
            expression = args[i + 1]
            
            if not isinstance(weight, (int, float)):
                raise SchemaError("weight-specified weights must be numeric")
            
            expr_ast = self._sexpr_to_ast(expression, depth + 1)
            weights_and_expressions.append((float(weight), expr_ast))
        
        return WeightSpecified(weights_and_expressions)
    
    def _parse_weight_inverse_volatility(self, args: list[SExpr], depth: int) -> WeightInverseVolatility:
        """Parse inverse volatility weighted portfolio."""
        if len(args) < 2:
            raise SchemaError(
                "weight-inverse-volatility requires at least 2 arguments: lookback, expressions...",
                construct="weight-inverse-volatility",
                expected_arity="2+",
                actual_arity=len(args)
            )
        
        lookback = args[0]
        if not isinstance(lookback, int) or lookback <= 0:
            raise SchemaError("weight-inverse-volatility lookback must be a positive integer")
        
        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args[1:]]
        return WeightInverseVolatility(lookback, expressions)
    
    def _parse_filter(self, args: list[SExpr], depth: int) -> Filter:
        """Parse filter selector."""
        if len(args) < 3:
            raise SchemaError(
                "filter requires at least 3 arguments: metric_fn, select-top n, assets...",
                construct="filter",
                expected_arity="3+",
                actual_arity=len(args)
            )
        
        metric_fn = self._sexpr_to_ast(args[0], depth + 1)
        
        # Parse "select-top n" - expect list ["select-top", n]
        select_clause = args[1]
        if not isinstance(select_clause, list) or len(select_clause) != 2:
            raise SchemaError("filter requires [select-top n] as second argument")
        
        if select_clause[0] != "select-top":
            raise SchemaError("filter requires select-top clause")
        
        select_n = select_clause[1]
        if not isinstance(select_n, int) or select_n <= 0:
            raise SchemaError("select-top n must be a positive integer")
        
        assets = [self._sexpr_to_ast(asset, depth + 1) for asset in args[2:]]
        return Filter(metric_fn, select_n, assets)
    
    def _parse_strategy(self, args: list[SExpr], depth: int) -> Strategy:
        """Parse strategy root node."""
        if len(args) < 3:
            raise SchemaError(
                "defsymphony requires 3 arguments: name, metadata, expression",
                construct="defsymphony",
                expected_arity=3,
                actual_arity=len(args)
            )
        
        name = args[0]
        if not isinstance(name, str):
            raise SchemaError("strategy name must be a string")
        
        # Parse metadata (should be a map/dict in Clojure syntax)
        metadata_raw = args[1]
        metadata = self._parse_metadata_map(metadata_raw)
        
        expression = self._sexpr_to_ast(args[2], depth + 1)
        
        return Strategy(name, metadata, expression)
    
    def _parse_metadata_map(self, metadata_raw: SExpr) -> dict[str, Any]:
        """Parse Clojure-style metadata map {:key value ...}."""
        if not isinstance(metadata_raw, dict):
            # For now, return empty metadata if not properly structured
            # TODO: Implement proper Clojure map parsing if needed
            return {}
        return dict(metadata_raw)
    
    def _extract_window(self, window_spec: SExpr) -> int:
        """Extract window parameter from various formats."""
        # Handle direct integer
        if isinstance(window_spec, int):
            return window_spec
        
        # Handle Clojure map {:window N}
        if isinstance(window_spec, dict) and ":window" in window_spec:
            window = window_spec[":window"] 
            if isinstance(window, int):
                return window
        
        raise SchemaError(f"Could not extract window from: {window_spec}")