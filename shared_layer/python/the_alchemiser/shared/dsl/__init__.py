"""Business Unit: shared | Status: current.

Shared DSL utilities for S-expression parsing and group discovery.

Provides:
- SexprParser: Parser for Clojure-style S-expressions
- GroupInfo: Metadata about discovered groups needing backfill
- find_filter_targeted_groups: AST walking to discover filter-targeted groups
- extract_symbols_from_ast: Symbol extraction from AST nodes
"""

from __future__ import annotations

from the_alchemiser.shared.dsl.group_discovery import (
    GroupInfo,
    extract_symbols_from_ast,
    find_filter_targeted_groups,
)
from the_alchemiser.shared.dsl.sexpr_parser import SexprParser

__all__ = [
    "GroupInfo",
    "SexprParser",
    "extract_symbols_from_ast",
    "find_filter_targeted_groups",
]
