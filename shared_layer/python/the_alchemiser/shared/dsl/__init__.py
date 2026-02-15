"""Business Unit: shared | Status: current.

Shared DSL utilities for S-expression parsing and group discovery.

Provides:
- SexprParser: Parser for Clojure-style S-expressions
- GroupInfo: Metadata about discovered groups needing backfill
- derive_group_id: Deterministic group ID derivation
- find_filter_targeted_groups: AST walking to discover filter-targeted groups
- extract_symbols_from_ast: Symbol extraction from AST nodes
- get_strategies_dir: Strategy file path resolution
"""

from __future__ import annotations

from the_alchemiser.shared.dsl.group_discovery import (
    GroupInfo,
    derive_group_id,
    extract_symbols_from_ast,
    find_filter_targeted_groups,
)
from the_alchemiser.shared.dsl.sexpr_parser import SexprParser
from the_alchemiser.shared.dsl.strategy_paths import get_strategies_dir

__all__ = [
    "GroupInfo",
    "SexprParser",
    "derive_group_id",
    "extract_symbols_from_ast",
    "find_filter_targeted_groups",
    "get_strategies_dir",
]
