#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL operator dispatcher and registry for function evaluation.

Provides a registry system for mapping DSL symbols to their implementing
functions, enabling clean separation of concerns and testability.
"""

from __future__ import annotations

from collections.abc import Callable

from the_alchemiser.shared.schemas.ast_node import ASTNode

from .context import DslContext
from .types import DSLValue


class DslDispatcher:
    """Dispatcher for DSL operator functions.

    Maintains a registry of DSL symbols mapped to their implementing functions
    and provides dispatch functionality for AST evaluation.
    """

    def __init__(self) -> None:
        """Initialize empty dispatcher."""
        self.symbol_table: dict[str, Callable[[list[ASTNode], DslContext], DSLValue]] = {}

    def register(self, symbol: str, func: Callable[[list[ASTNode], DslContext], DSLValue]) -> None:
        """Register a function for a DSL symbol.

        Args:
            symbol: DSL symbol name (e.g., "weight-equal", "rsi", ">")
            func: Function that implements the operator

        """
        self.symbol_table[symbol] = func

    def dispatch(self, symbol: str, args: list[ASTNode], context: DslContext) -> DSLValue:
        """Dispatch a DSL function call.

        Args:
            symbol: DSL symbol to call
            args: Arguments for the function
            context: DSL evaluation context

        Returns:
            Result of the function call

        Raises:
            KeyError: If symbol is not registered

        """
        if symbol not in self.symbol_table:
            raise KeyError(f"Unknown DSL function: {symbol}")

        return self.symbol_table[symbol](args, context)

    def is_registered(self, symbol: str) -> bool:
        """Check if a symbol is registered.

        Args:
            symbol: DSL symbol to check

        Returns:
            True if symbol is registered, False otherwise

        """
        return symbol in self.symbol_table

    def list_symbols(self) -> list[str]:
        """Get list of all registered symbols.

        Returns:
            List of registered symbol names

        """
        return list(self.symbol_table.keys())
