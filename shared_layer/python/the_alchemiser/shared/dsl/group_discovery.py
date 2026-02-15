"""Business Unit: shared | Status: current.

Group discovery utilities for DSL strategy files.

Provides AST-walking functions to discover groups that are direct children
of ``filter`` operators in strategy files. These groups need cached PnL data
because the filter computes a metric (moving-average-return, stdev-return, etc.)
over their historical return stream to rank/select them.

Also provides symbol extraction from AST nodes for market data pre-loading.
"""

from __future__ import annotations

from the_alchemiser.shared.schemas.ast_node import ASTNode


class GroupInfo:
    """Metadata about a discovered group that needs backfilling.

    Attributes:
        name: Human-readable group name from the strategy file.
        body: List of ASTNode expressions forming the group body.
        depth: Nesting depth (0 = top-level, 1 = nested inside another filter).
        parent_filter_metric: Metric name from the parent filter operator.

    """

    __slots__ = ("body", "depth", "name", "parent_filter_metric")

    def __init__(
        self,
        name: str,
        body: list[ASTNode],
        depth: int,
        parent_filter_metric: str,
    ) -> None:
        """Initialise group info with name, body, depth and parent metric."""
        self.name = name
        self.body = body
        self.depth = depth
        self.parent_filter_metric = parent_filter_metric

    def __repr__(self) -> str:  # noqa: D105
        return (
            f"GroupInfo(name={self.name!r}, depth={self.depth}, "
            f"metric={self.parent_filter_metric!r})"
        )

    # Explicit pickle support for __slots__-only class (required by spawn
    # multiprocessing which serialises objects across process boundaries).
    def __getstate__(self) -> dict[str, object]:  # noqa: D105
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def __setstate__(self, state: dict[str, object]) -> None:  # noqa: D105
        for slot, value in state.items():
            object.__setattr__(self, slot, value)


def find_filter_targeted_groups(
    node: ASTNode,
    depth: int = 0,
) -> list[GroupInfo]:
    """Walk AST and find groups that are direct children of ``filter`` operators.

    Only these groups need cached PnL data because the filter needs to
    compute a metric (moving-average-return, stdev-return, etc.) over
    their historical return stream to rank/select them.

    Groups that are just structural containers (e.g. ``(group "Bull" ...)``
    nested inside an ``if`` branch) do NOT need caching -- they resolve
    to a single allocation and their PnL is never queried by a filter.

    Within each filter-targeted group, we also recurse to find any
    inner filter-targeted groups (e.g. "MAX DD: TQQQ vs UVXY" inside
    "WYLD...") since those inner filters also need cached PnL for
    their own group children.

    Args:
        node: AST node to walk.
        depth: Current nesting depth (0 = top-level).

    Returns:
        List of GroupInfo with name, body, depth, and parent metric.

    """
    results: list[GroupInfo] = []
    if not isinstance(node, ASTNode):
        return results

    if not node.is_list() or not node.children:
        return results

    first = node.children[0]

    # Check if this is a (filter ...) node
    if first.is_symbol() and first.get_symbol_name() == "filter":
        # Extract the metric name from the condition expression
        metric_name = _extract_metric_name(
            node.children[1] if len(node.children) > 1 else None,
        )

        # The portfolio list is the last argument
        portfolio_node = node.children[-1] if len(node.children) >= 3 else None

        if portfolio_node is not None:
            # The portfolio list is a vector [...] which is parsed as a list node
            portfolio_items: list[ASTNode] = []
            if portfolio_node.is_list():
                portfolio_items = list(portfolio_node.children)
            else:
                portfolio_items = [portfolio_node]

            # Find group nodes among the portfolio items
            for item in portfolio_items:
                if not isinstance(item, ASTNode) or not item.is_list():
                    continue
                if not item.children:
                    continue
                item_first = item.children[0]
                if (
                    item_first.is_symbol()
                    and item_first.get_symbol_name() == "group"
                    and len(item.children) >= 3
                ):
                    name_node = item.children[1]
                    name_val = name_node.get_atom_value()
                    if isinstance(name_val, str):
                        body = list(item.children[2:])
                        results.append(
                            GroupInfo(
                                name=name_val,
                                body=body,
                                depth=depth,
                                parent_filter_metric=metric_name,
                            )
                        )
                        # Recurse into this group's body to find inner
                        # filter-targeted groups at depth+1
                        for body_expr in body:
                            results.extend(find_filter_targeted_groups(body_expr, depth + 1))

    # Always recurse into all children to find filters at any level
    for child in node.children:
        # Skip the portfolio_items we already processed above
        if first.is_symbol() and first.get_symbol_name() == "filter":
            # For filter nodes, we already recursed into group bodies above.
            # But we still need to recurse into the condition and selection
            # expressions (unlikely to contain filters, but be thorough).
            if child is not node.children[-1]:
                results.extend(find_filter_targeted_groups(child, depth))
        else:
            results.extend(find_filter_targeted_groups(child, depth))

    return results


def _extract_metric_name(condition_node: ASTNode | None) -> str:
    """Extract the metric name from a filter condition AST node.

    E.g. ``(moving-average-return {:window 10})`` -> ``"moving-average-return"``

    Args:
        condition_node: AST node representing the filter condition.

    Returns:
        Metric name string, or "unknown" if not extractable.

    """
    if not isinstance(condition_node, ASTNode):
        return "unknown"
    if condition_node.is_symbol():
        return condition_node.get_symbol_name() or "unknown"
    if condition_node.is_list() and condition_node.children:
        first = condition_node.children[0]
        if first.is_symbol():
            return first.get_symbol_name() or "unknown"
    return "unknown"


# Indicator DSL names whose first string argument is a ticker symbol.
_INDICATOR_FUNCTIONS: frozenset[str] = frozenset(
    {
        "rsi",
        "current-price",
        "moving-average-price",
        "moving-average-return",
        "cumulative-return",
        "exponential-moving-average-price",
        "stdev-return",
        "stdev-price",
        "max-drawdown",
        "percentage-price-oscillator",
        "percentage-price-oscillator-signal",
        "ma",
        "volatility",
    }
)


def extract_symbols_from_ast(nodes: list[ASTNode]) -> set[str]:
    """Extract ticker symbols from AST nodes.

    Walks AST for ``(asset ...)`` forms and indicator calls like
    ``(cumulative-return "FXI" ...)``.  This is a pure AST walk -- no
    engine evaluation or indicator computation needed.

    Args:
        nodes: List of ASTNode objects to walk.

    Returns:
        Set of ticker symbol strings.

    """
    symbols: set[str] = set()

    def _is_ticker(value: object) -> bool:
        """Check if a value looks like a ticker symbol (1-5 uppercase letters)."""
        return (
            isinstance(value, str) and 1 <= len(value) <= 5 and value.isalpha() and value.isupper()
        )

    def _walk(node: object) -> None:
        if not isinstance(node, ASTNode):
            return

        if node.is_list() and node.children:
            first = node.children[0]
            if first.is_symbol():
                func_name = first.get_symbol_name()

                # Match (asset "TICKER" "description")
                if (func_name == "asset" and len(node.children) >= 2) or (
                    func_name in _INDICATOR_FUNCTIONS and len(node.children) >= 2
                ):
                    ticker_node = node.children[1]
                    ticker = ticker_node.get_atom_value()
                    if isinstance(ticker, str) and _is_ticker(ticker):
                        symbols.add(ticker)

            # Recurse into all children
            for child in node.children:
                _walk(child)

        elif node.is_list():
            for child in node.children:
                _walk(child)

    for node in nodes:
        _walk(node)

    return symbols
