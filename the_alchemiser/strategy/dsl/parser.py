"""Business Unit: utilities; Status: current.

S-expression parser with Clojure vector [] support for trading strategy DSL.

Vectors act as grouping constructs. For portfolio / selector constructs they
are flattened into the surrounding argument list. For conditional branches a
vector containing multiple expressions becomes an implicit block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from the_alchemiser.strategy.dsl.ast import (
    RSI,
    Asset,
    ASTNode,
    CumulativeReturn,
    CurrentPrice,
    Filter,
    FunctionCall,
    GreaterThan,
    Group,
    If,
    LessThan,
    MovingAveragePrice,
    MovingAverageReturn,
    NumberLiteral,
    SelectBottom,
    SelectTop,
    StdevReturn,
    Strategy,
    Symbol,
    WeightEqual,
    WeightInverseVolatility,
    WeightSpecified,
)
from the_alchemiser.strategy.dsl.errors import ParseError, SchemaError


@dataclass(frozen=True)
class Vector:
    """Immutable vector container for DSL elements.

    Attributes:
        elements: List of elements contained in this vector

    """

    elements: list[Any]


# Simplified for linter compatibility (recursive union replaced by Any)
SExprType = Any


class DSLParser:
    MAX_DEPTH = 5000000  # Default very high for extremely nested strategies
    MAX_NODES = 2000000000  # Default very high for massive complex strategies

    def __init__(
        self,
        max_nodes: int | None = MAX_NODES,
        max_depth: int | None = MAX_DEPTH,
        enable_interning: bool = False,
    ) -> None:
        """Create a DSL parser.

        Args:
            max_nodes: Maximum AST nodes allowed (None disables cap).
            max_depth: Maximum recursion depth (None disables cap).
            enable_interning: Enable AST interning during parsing for structural sharing.

        """
        self._configured_max_nodes = max_nodes
        self._configured_max_depth = max_depth
        self._enable_interning = enable_interning
        self._node_count: int = 0
        self._max_depth_seen: int = 0

    @property
    def node_count(self) -> int:
        """Return node count from the last parse operation."""
        return self._node_count

    @property
    def max_depth_seen(self) -> int:
        """Return maximum depth observed during last parse."""
        return self._max_depth_seen

    def parse(self, source: str, enable_interning: bool | None = None) -> ASTNode:
        """Parse source code into an AST.

        Args:
            source: S-expression source code
            enable_interning: Whether to apply AST interning for structural sharing
                (overrides constructor setting if provided)

        Returns:
            Parsed AST root node (potentially with structural sharing applied)

        """
        # Allow override of instance setting
        if enable_interning is not None:
            self._enable_interning = enable_interning

        self._node_count = 0
        try:
            sexpr = self._parse_sexpr(source.strip())
            return self._sexpr_to_ast(sexpr, 0)
        except (ParseError, SchemaError):  # re-raise cleanly
            raise
        except Exception as e:  # pragma: no cover
            raise ParseError(f"Unexpected parsing error: {e}", expression=source) from e

    # ---------------- Tokenization -----------------
    def _tokenize(self, source: str) -> list[str]:
        cleaned: list[str] = []
        for line in source.split("\n"):
            comment = line.find(";;")
            if comment >= 0:
                line = line[:comment]
            cleaned.append(line)
        joined = "\n".join(cleaned)
        pattern = r'\{|\}|\(|\)|\[|\]|"[^"]*"|[^\s(){}\[\]"]+'
        raw_tokens = [t for t in re.findall(pattern, joined) if t.strip()]
        processed: list[str] = []
        for tok in raw_tokens:
            # Clojure treats commas as whitespace; strip trailing commas from tokens.
            if tok.endswith(","):
                tok = tok[:-1]
            # Drop standalone commas or empty tokens if they ever appear (defensive)
            if tok == "," or not tok.strip():
                continue
            processed.append(tok)
        return processed

    def _parse_sexpr(self, source: str) -> SExprType:
        if not source:
            raise ParseError("Empty expression")
        tokens = self._tokenize(source)
        if not tokens:
            raise ParseError("No tokens found")
        expr, remaining = self._parse_tokens(tokens)
        if remaining:
            raise ParseError(f"Unexpected tokens remaining: {remaining}")
        return expr

    def _parse_tokens(self, tokens: list[str]) -> tuple[SExprType, list[str]]:
        """Parse tokens into S-expressions with proper nesting handling."""
        if not tokens:
            raise ParseError("Unexpected end of input")

        head, rest = tokens[0], tokens[1:]

        # Dispatch parsing based on opening delimiter
        return self._dispatch_token_parsing(head, rest)

    def _dispatch_token_parsing(self, head: str, rest: list[str]) -> tuple[SExprType, list[str]]:
        """Dispatch token parsing based on the head token type."""
        token_parsers = {
            "(": lambda: self._parse_list_tokens(rest, ")", "Missing closing parenthesis"),
            "[": lambda: self._parse_vector_tokens(rest),
            "{": lambda: self._parse_map_tokens(rest),
        }

        if head in token_parsers:
            return token_parsers[head]()
        if head in (")", "]", "}"):
            raise ParseError(f"Unexpected closing {head}")
        return self._parse_atom(head), rest

    def _parse_list_tokens(
        self, rest: list[str], closing_token: str, error_message: str
    ) -> tuple[list[SExprType], list[str]]:
        """Parse list tokens until closing delimiter."""
        items: list[SExprType] = []
        while rest and rest[0] != closing_token:
            sub, rest = self._parse_tokens(rest)
            items.append(sub)
        if not rest or rest[0] != closing_token:
            raise ParseError(error_message)
        return items, rest[1:]

    def _parse_vector_tokens(self, rest: list[str]) -> tuple[Vector, list[str]]:
        """Parse vector tokens (square brackets)."""
        items_v: list[SExprType] = []
        while rest and rest[0] != "]":
            sub, rest = self._parse_tokens(rest)
            items_v.append(sub)
        if not rest or rest[0] != "]":
            raise ParseError("Missing closing bracket")
        return Vector(items_v), rest[1:]

    def _parse_map_tokens(self, rest: list[str]) -> tuple[dict[str, SExprType], list[str]]:
        """Parse map tokens (curly braces)."""
        mp: dict[str, SExprType] = {}
        while rest and rest[0] != "}":
            k, rest = self._parse_tokens(rest)
            if not rest:
                raise ParseError("Missing value in map")
            v, rest = self._parse_tokens(rest)
            mp[str(k)] = v
        if not rest or rest[0] != "}":
            raise ParseError("Missing closing brace")
        return mp, rest[1:]

    def _parse_atom(self, token: str) -> str | int | float:
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        if token.startswith(":"):
            return token
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            return token

    # ---------------- AST Conversion -----------------
    def _sexpr_to_ast(self, sexpr: SExprType, depth: int) -> ASTNode:
        """Convert S-expression to AST node with depth tracking and validation."""
        # Track and validate depth
        self._track_and_validate_depth(depth)

        # Create the appropriate AST node
        node = self._create_ast_node_from_sexpr(sexpr, depth)

        # Handle interning and node counting
        return self._finalize_ast_node(node)

    def _track_and_validate_depth(self, depth: int) -> None:
        """Track maximum depth and enforce limits."""
        if depth > self._max_depth_seen:
            self._max_depth_seen = depth
        # Enforce depth limit if configured
        if self._configured_max_depth is not None and depth > self._configured_max_depth:
            raise ParseError(f"Maximum AST depth exceeded: {self._configured_max_depth}")

    def _create_ast_node_from_sexpr(self, sexpr: SExprType, depth: int) -> ASTNode:
        """Create the appropriate AST node based on S-expression type."""
        if isinstance(sexpr, int | float):
            return NumberLiteral(float(sexpr))
        if isinstance(sexpr, str):
            return Symbol(sexpr)
        if isinstance(sexpr, Vector):
            inner = [self._sexpr_to_ast(e, depth + 1) for e in sexpr.elements]
            return Group("__vector__", inner)
        if isinstance(sexpr, list):
            return self._create_ast_node_from_list(sexpr, depth)
        if isinstance(sexpr, dict):  # metadata map placeholder
            return Symbol("__map__")
        raise ParseError(f"Unexpected S-expression type: {type(sexpr)}")

    def _create_ast_node_from_list(self, sexpr: list, depth: int) -> ASTNode:
        """Create AST node from list S-expression (function call)."""
        if not sexpr:
            raise ParseError("Empty list expression")
        op = sexpr[0]
        if not isinstance(op, str):
            raise ParseError(f"Operator must be symbol, got {type(op)}")
        raw_args = sexpr[1:]
        return self._parse_construct(op, raw_args, depth)

    def _finalize_ast_node(self, node: ASTNode) -> ASTNode:
        """Apply interning and node counting to finalize the AST node."""
        # Apply interning if enabled, which may return an existing instance
        if self._enable_interning:
            from the_alchemiser.strategy.dsl.interning import intern_node

            interned_node = intern_node(node)
            # Only count as a new node if this is actually a new unique structure
            if interned_node is node:  # New node created
                self._increment_node_count()
            # else: reused existing node, don't count it
            return interned_node
        # No interning - count every node
        self._increment_node_count()
        return node

    def _increment_node_count(self) -> None:
        """Increment node count and enforce limits."""
        self._node_count += 1
        if self._configured_max_nodes is not None and self._node_count > self._configured_max_nodes:
            raise ParseError(f"Maximum node count exceeded: {self._configured_max_nodes}")

    def _unwrap_vector_group(self, node: ASTNode) -> list[ASTNode]:
        if isinstance(node, Group) and node.name == "__vector__":
            return node.expressions
        return [node]

    def _flatten_vector_nodes(self, nodes: list[ASTNode]) -> list[ASTNode]:
        flat: list[ASTNode] = []
        for n in nodes:
            if isinstance(n, Group) and n.name == "__vector__":
                flat.extend(n.expressions)
            else:
                flat.append(n)
        return flat

    def _parse_construct(self, operator: str, args: list[SExprType], depth: int) -> ASTNode:
        """Parse a construct based on the operator, using dispatch table for efficiency."""
        ast_args = [self._sexpr_to_ast(a, depth + 1) for a in args]

        # Handle special preprocessing for certain operators
        ast_args = self._preprocess_construct_args(operator, ast_args, args)

        # Handle special cases that don't use standard dispatch
        if special_result := self._handle_special_constructs(operator, ast_args, args, depth):
            return special_result

        # Use dispatch table for standard constructs
        return self._dispatch_construct_parsing(operator, args, depth)

    def _preprocess_construct_args(
        self, operator: str, ast_args: list[ASTNode], args: list[SExprType]
    ) -> list[ASTNode]:
        """Preprocess AST arguments for operators that need special handling."""
        if operator in {"weight-equal", "group", "weight-inverse-volatility", "weight-specified"}:
            return self._flatten_vector_nodes(ast_args)
        if operator == "filter" and len(ast_args) >= 3:
            return self._preprocess_filter_args(ast_args, args)
        if operator == "if":
            return self._preprocess_if_args(ast_args)
        return ast_args

    def _preprocess_filter_args(
        self, ast_args: list[ASTNode], args: list[SExprType]
    ) -> list[ASTNode]:
        """Preprocess filter arguments to handle vector unwrapping."""
        _metric_ast, _selector_ast, *assets = ast_args
        if len(assets) == 1 and isinstance(assets[0], Group) and assets[0].name == "__vector__":
            assets = assets[0].expressions
        # Rebuild raw args for downstream parse method using original SExpr for indicator semantics
        # Create new args list to avoid modifying the original list passed as parameter
        new_args = [
            args[0],
            args[1],
            *[self._ast_to_sexpr_placeholder(a) for a in assets],
        ]
        args[:] = new_args
        return ast_args

    def _preprocess_if_args(self, ast_args: list[ASTNode]) -> list[ASTNode]:
        """Preprocess if construct arguments."""
        if len(ast_args) >= 2:
            then_nodes = self._unwrap_vector_group(ast_args[1])
            ast_args[1] = (
                then_nodes[0] if len(then_nodes) == 1 else Group("__implicit_block__", then_nodes)
            )
        if len(ast_args) >= 3:
            else_nodes = self._unwrap_vector_group(ast_args[2])
            ast_args[2] = (
                else_nodes[0] if len(else_nodes) == 1 else Group("__implicit_block__", else_nodes)
            )
        return ast_args

    def _handle_special_constructs(
        self, operator: str, ast_args: list[ASTNode], args: list[SExprType], depth: int
    ) -> ASTNode | None:
        """Handle special constructs that need custom logic."""
        if operator == "if":
            if len(ast_args) < 2 or len(ast_args) > 3:
                raise SchemaError(
                    "if requires 2-3 arguments: condition, then_expr, [else_expr]",
                    construct="if",
                    actual_arity=len(ast_args),
                )
            return If(ast_args[0], ast_args[1], ast_args[2] if len(ast_args) == 3 else None)
        return None

    def _dispatch_construct_parsing(
        self, operator: str, args: list[SExprType], depth: int
    ) -> ASTNode:
        """Dispatch construct parsing using a lookup table."""
        # Create dispatch table for construct parsers
        construct_parsers = {
            ">": lambda: self._parse_comparison(GreaterThan, args, depth),
            "<": lambda: self._parse_comparison(LessThan, args, depth),
            "rsi": lambda: self._parse_rsi(args, depth),
            "moving-average-price": lambda: self._parse_moving_average_price(args, depth),
            "moving-average-return": lambda: self._parse_moving_average_return(args, depth),
            "cumulative-return": lambda: self._parse_cumulative_return(args, depth),
            "current-price": lambda: self._parse_current_price(args, depth),
            "stdev-return": lambda: self._parse_stdev_return(args, depth),
            "asset": lambda: self._parse_asset(args, depth),
            "group": lambda: self._parse_group(args, depth),
            "weight-equal": lambda: self._parse_weight_equal(args, depth),
            "weight-specified": lambda: self._parse_weight_specified(args, depth),
            "weight-inverse-volatility": lambda: self._parse_weight_inverse_volatility(args, depth),
            "filter": lambda: self._parse_filter(args, depth),
            "select-top": lambda: self._parse_select_top(args, depth),
            "select-bottom": lambda: self._parse_select_bottom(args, depth),
            "defsymphony": lambda: self._parse_strategy(args, depth),
        }

        # Use dispatch table or fall back to generic function call
        if operator in construct_parsers:
            return construct_parsers[operator]()

        return FunctionCall(operator, [self._sexpr_to_ast(a, depth + 1) for a in args])

    def _ast_to_sexpr_placeholder(self, node: ASTNode) -> SExprType:
        # This helper is minimal; currently only needed for filter asset reconstruction.
        if isinstance(node, Group) and node.name == "__vector__":
            # Represent nested vector as list of placeholder symbols
            return [self._ast_to_sexpr_placeholder(e) for e in node.expressions]
        if isinstance(node, Symbol):
            return node.name
        if isinstance(node, Asset):
            # Reconstruct asset S-expression to preserve Asset node semantics
            return ["asset", node.symbol, node.name]
        return getattr(node, "symbol", "__expr__")

    def _parse_comparison(
        self,
        node_type: type[GreaterThan] | type[LessThan],
        args: list[SExprType],
        depth: int,
    ) -> GreaterThan | LessThan:
        """Parse comparison operator."""
        if len(args) != 2:
            op_name = ">" if node_type == GreaterThan else "<"
            raise SchemaError(
                f"{op_name} requires exactly 2 arguments",
                construct=op_name,
                expected_arity=2,
                actual_arity=len(args),
            )

        left = self._sexpr_to_ast(args[0], depth + 1)
        right = self._sexpr_to_ast(args[1], depth + 1)

        return node_type(left, right)

    def _parse_rsi(self, args: list[SExprType], depth: int) -> RSI:  # depth kept for symmetry
        """Parse RSI indicator."""
        # For filter context, RSI might have only window parameter
        if len(args) == 1:
            # Only window parameter - symbol will be substituted later
            window = self._extract_window(args[0])
            return RSI("", window)  # Empty symbol to be filled later
        if len(args) == 2:
            # Standard format: symbol and window
            symbol = args[0]
            if not isinstance(symbol, str):
                raise SchemaError("rsi symbol must be a string")

            window = self._extract_window(args[1])
            return RSI(symbol, window)
        raise SchemaError(
            "rsi requires 1 argument (window) for filters or 2 arguments (symbol, window) for direct use",
            construct="rsi",
            actual_arity=len(args),
        )

    def _parse_moving_average_price(
        self, args: list[SExprType], depth: int
    ) -> MovingAveragePrice:  # depth kept
        """Parse moving average price indicator."""
        # For filter context, might have only window parameter
        if len(args) == 1:
            # Only window parameter - symbol will be substituted later
            window = self._extract_window(args[0])
            return MovingAveragePrice("", window)  # Empty symbol to be filled later
        if len(args) == 2:
            # Standard format: symbol and window
            symbol = args[0]
            if not isinstance(symbol, str):
                raise SchemaError("moving-average-price symbol must be a string")

            window = self._extract_window(args[1])
            return MovingAveragePrice(symbol, window)
        raise SchemaError(
            "moving-average-price requires 1 argument (window) for filters or 2 arguments (symbol, window) for direct use",
            construct="moving-average-price",
            actual_arity=len(args),
        )

    def _parse_moving_average_return(
        self,
        args: list[SExprType],
        depth: int,  # depth kept
    ) -> MovingAverageReturn:
        """Parse moving average return indicator."""
        # For filter context, might have only window parameter
        if len(args) == 1:
            # Only window parameter - symbol will be substituted later
            window = self._extract_window(args[0])
            return MovingAverageReturn("", window)  # Empty symbol to be filled later
        if len(args) == 2:
            # Standard format: symbol and window
            symbol = args[0]
            if not isinstance(symbol, str):
                raise SchemaError("moving-average-return symbol must be a string")

            window = self._extract_window(args[1])
            return MovingAverageReturn(symbol, window)
        raise SchemaError(
            "moving-average-return requires 1 argument (window) for filters or 2 arguments (symbol, window) for direct use",
            construct="moving-average-return",
            actual_arity=len(args),
        )

    def _parse_cumulative_return(
        self, args: list[SExprType], depth: int
    ) -> CumulativeReturn:  # depth kept
        """Parse cumulative return indicator."""
        # For filter context, might have only window parameter
        if len(args) == 1:
            # Only window parameter - symbol will be substituted later
            window = self._extract_window(args[0])
            return CumulativeReturn("", window)  # Empty symbol to be filled later
        if len(args) == 2:
            # Standard format: symbol and window
            symbol = args[0]
            if not isinstance(symbol, str):
                raise SchemaError("cumulative-return symbol must be a string")

            window = self._extract_window(args[1])
            return CumulativeReturn(symbol, window)
        raise SchemaError(
            "cumulative-return requires 1 argument (window) for filters or 2 arguments (symbol, window) for direct use",
            construct="cumulative-return",
            actual_arity=len(args),
        )

    def _parse_current_price(self, args: list[SExprType], depth: int) -> CurrentPrice:  # depth kept
        """Parse current price indicator."""
        if len(args) != 1:
            raise SchemaError(
                "current-price requires 1 argument: symbol",
                construct="current-price",
                expected_arity=1,
                actual_arity=len(args),
            )

        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("current-price symbol must be a string")

        return CurrentPrice(symbol)

    def _parse_stdev_return(self, args: list[SExprType], depth: int) -> StdevReturn:  # depth kept
        """Parse standard deviation of returns indicator."""
        # For filter context, stdev-return might have only window parameter
        if len(args) == 1:
            # Only window parameter - symbol will be substituted later
            window = self._extract_window(args[0])
            return StdevReturn("", window)  # Empty symbol to be filled later
        if len(args) == 2:
            # Standard format: symbol and window
            symbol = args[0]
            if not isinstance(symbol, str):
                raise SchemaError("stdev-return symbol must be a string")

            window = self._extract_window(args[1])
            return StdevReturn(symbol, window)
        raise SchemaError(
            "stdev-return requires 1 argument (window) for filters or 2 arguments (symbol, window) for direct use",
            construct="stdev-return",
            actual_arity=len(args),
        )

    def _parse_asset(self, args: list[SExprType], depth: int) -> Asset:  # depth kept
        """Parse asset definition."""
        if len(args) < 1 or len(args) > 2:
            raise SchemaError(
                "asset requires 1-2 arguments: symbol, [name]",
                construct="asset",
                actual_arity=len(args),
            )

        symbol = args[0]
        if not isinstance(symbol, str):
            raise SchemaError("asset symbol must be a string")

        name = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        return Asset(symbol, name)

    def _parse_group(self, args: list[SExprType], depth: int) -> Group:
        """Parse group wrapper."""
        if len(args) < 2:
            raise SchemaError(
                "group requires at least 2 arguments: name, expressions...",
                construct="group",
                actual_arity=len(args),
            )

        name = args[0]
        if not isinstance(name, str):
            raise SchemaError("group name must be a string")

        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args[1:]]
        return Group(name, expressions)

    def _parse_weight_equal(self, args: list[SExprType], depth: int) -> WeightEqual:
        """Parse equal weight portfolio."""
        if not args:
            raise SchemaError(
                "weight-equal requires at least 1 argument",
                construct="weight-equal",
                actual_arity=0,
            )

        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args]
        return WeightEqual(expressions)

    def _parse_weight_specified(self, args: list[SExprType], depth: int) -> WeightSpecified:
        """Parse explicitly weighted portfolio."""
        if len(args) % 2 != 0:
            raise SchemaError(
                "weight-specified requires pairs of weight, expression arguments",
                construct="weight-specified",
            )

        if len(args) < 2:
            raise SchemaError(
                "weight-specified requires at least one weight, expression pair",
                construct="weight-specified",
            )

        weights_and_expressions = []
        for i in range(0, len(args), 2):
            weight = args[i]
            expression = args[i + 1]

            if not isinstance(weight, int | float):
                raise SchemaError("weight-specified weights must be numeric")

            expr_ast = self._sexpr_to_ast(expression, depth + 1)
            weights_and_expressions.append((float(weight), expr_ast))

        return WeightSpecified(weights_and_expressions)

    def _parse_weight_inverse_volatility(
        self, args: list[SExprType], depth: int
    ) -> WeightInverseVolatility:
        """Parse inverse volatility weighted portfolio."""
        if len(args) < 2:
            raise SchemaError(
                "weight-inverse-volatility requires at least 2 arguments: lookback, expressions...",
                construct="weight-inverse-volatility",
                actual_arity=len(args),
            )

        lookback = args[0]
        if not isinstance(lookback, int) or lookback <= 0:
            raise SchemaError("weight-inverse-volatility lookback must be a positive integer")

        expressions = [self._sexpr_to_ast(expr, depth + 1) for expr in args[1:]]
        return WeightInverseVolatility(lookback, expressions)

    def _parse_filter(self, args: list[SExprType], depth: int) -> Filter:
        """Parse filter selector."""
        if len(args) < 3:
            raise SchemaError(
                "filter requires at least 3 arguments: metric_fn, selector, assets...",
                construct="filter",
                actual_arity=len(args),
            )

        metric_fn = self._sexpr_to_ast(args[0], depth + 1)

        # Parse selector (select-top n or select-bottom n)
        selector = self._sexpr_to_ast(args[1], depth + 1)
        if not isinstance(selector, SelectTop | SelectBottom):
            raise SchemaError("filter requires select-top or select-bottom as second argument")
        assets = [self._sexpr_to_ast(asset, depth + 1) for asset in args[2:]]
        return Filter(metric_fn, selector, assets)

    def _parse_select_top(self, args: list[SExprType], depth: int) -> SelectTop:  # depth kept
        """Parse select-top selector."""
        if len(args) != 1:
            raise SchemaError(
                "select-top requires 1 argument: count",
                construct="select-top",
                expected_arity=1,
                actual_arity=len(args),
            )

        count = args[0]
        if not isinstance(count, int) or count <= 0:
            raise SchemaError("select-top count must be a positive integer")

        return SelectTop(count)

    def _parse_select_bottom(self, args: list[SExprType], depth: int) -> SelectBottom:  # depth kept
        """Parse select-bottom selector."""
        if len(args) != 1:
            raise SchemaError(
                "select-bottom requires 1 argument: count",
                construct="select-bottom",
                expected_arity=1,
                actual_arity=len(args),
            )

        count = args[0]
        if not isinstance(count, int) or count <= 0:
            raise SchemaError("select-bottom count must be a positive integer")

        return SelectBottom(count)

    def _parse_strategy(self, args: list[SExprType], depth: int) -> Strategy:
        """Parse strategy root node."""
        if len(args) < 3:
            raise SchemaError(
                "defsymphony requires 3 arguments: name, metadata, expression",
                construct="defsymphony",
                expected_arity=3,
                actual_arity=len(args),
            )

        name = args[0]
        if not isinstance(name, str):
            raise SchemaError("strategy name must be a string")

        # Parse metadata (should be a map/dict in Clojure syntax)
        metadata_raw = args[1]
        metadata = self._parse_metadata_map(metadata_raw)

        expression = self._sexpr_to_ast(args[2], depth + 1)

        return Strategy(name, metadata, expression)

    def _parse_metadata_map(self, metadata_raw: SExprType) -> dict[str, Any]:
        """Parse Clojure-style metadata map {:key value ...}."""
        if not isinstance(metadata_raw, dict):
            # For now, return empty metadata if not properly structured
            # TODO: Implement proper Clojure map parsing if needed
            return {}
        return dict(metadata_raw)

    def _extract_window(self, window_spec: SExprType) -> int:
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
