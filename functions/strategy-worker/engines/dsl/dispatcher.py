#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL operator dispatcher and registry for function evaluation.

Provides a registry system for mapping DSL symbols to their implementing
functions, enabling clean separation of concerns and testability.
"""

from __future__ import annotations

from collections.abc import Callable

import structlog

from the_alchemiser.shared.schemas.ast_node import ASTNode

from engines.dsl.context import DslContext
from engines.dsl.types import DslEvaluationError, DSLValue

logger = structlog.get_logger(__name__)


class DslDispatcher:
    """Dispatcher for DSL operator functions.

    Maintains a registry of DSL symbols mapped to their implementing functions
    and provides dispatch functionality for AST evaluation.

    Thread Safety: This class is not thread-safe. It is designed to be
    initialized once (registration phase) and then used for read-only
    dispatch operations. If concurrent access is required, external
    synchronization must be provided.
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
        if symbol in self.symbol_table:
            logger.info("overwriting_dsl_operator", symbol=symbol)

        self.symbol_table[symbol] = func
        logger.debug("registered_dsl_operator", symbol=symbol)

    def dispatch(self, symbol: str, args: list[ASTNode], context: DslContext) -> DSLValue:
        """Dispatch a DSL function call.

        Args:
            symbol: DSL symbol to call
            args: Arguments for the function
            context: DSL evaluation context

        Returns:
            Result of the function call

        Raises:
            DslEvaluationError: If symbol is not registered

        """
        if symbol not in self.symbol_table:
            logger.warning(
                "unknown_dsl_function",
                symbol=symbol,
                correlation_id=context.correlation_id,
            )
            raise DslEvaluationError(f"Unknown DSL function: {symbol}")

        logger.debug(
            "dispatching_dsl_function",
            symbol=symbol,
            correlation_id=context.correlation_id,
            arg_count=len(args),
        )
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
