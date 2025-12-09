#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL evaluator for strategy expressions.

Evaluates parsed AST nodes from S-expressions with whitelisted symbol table
and indicator service integration.
"""

from __future__ import annotations

import decimal
import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation
from the_alchemiser.shared.schemas.trace import Trace
from the_alchemiser.shared.types.indicator_port import IndicatorPort

from .context import DslContext
from .dispatcher import DslDispatcher
from .events import DslEventPublisher
from .operators.comparison import register_comparison_operators
from .operators.control_flow import register_control_flow_operators
from .operators.indicators import register_indicator_operators
from .operators.portfolio import register_portfolio_operators
from .operators.selection import register_selection_operators
from .types import DslEvaluationError, DSLValue

__all__ = [
    "DslEvaluationError",
    "DslEvaluator",
    "IndicatorPort",
]


class DslEvaluator:
    """Evaluator for DSL strategy expressions.

    Walks AST nodes and evaluates them using a dispatcher-based operator
    registry with indicator service integration and event publishing.
    """

    def __init__(self, indicator_service: IndicatorPort, event_bus: EventBus | None = None) -> None:
        """Initialize DSL evaluator.

        Args:
            indicator_service: Service for computing indicators (IndicatorPort)
            event_bus: Optional event bus for publishing events

        """
        self.indicator_service = indicator_service
        self.event_bus = event_bus
        self.event_publisher = DslEventPublisher(event_bus)

        # Initialize dispatcher and register all operators
        self.dispatcher = DslDispatcher()
        self._register_all_operators()

        # Shared decision path for all contexts during evaluation (stored as dicts for serialization)
        self.decision_path: list[dict[str, Any]] = []

    def _register_all_operators(self) -> None:
        """Register all DSL operators with the dispatcher."""
        register_portfolio_operators(self.dispatcher)
        register_selection_operators(self.dispatcher)
        register_comparison_operators(self.dispatcher)
        register_control_flow_operators(self.dispatcher)
        register_indicator_operators(self.dispatcher)

    def evaluate(
        self, ast: ASTNode, correlation_id: str, trace: Trace | None = None
    ) -> tuple[StrategyAllocation, Trace]:
        """Evaluate AST and return allocation with trace.

        Args:
            ast: AST to evaluate
            correlation_id: Correlation ID for tracking
            trace: Optional existing trace to append to

        Returns:
            Tuple of (StrategyAllocation, Trace)

        Raises:
            DslEvaluationError: If evaluation fails

        """
        if trace is None:
            trace = Trace(
                trace_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                strategy_id="dsl_strategy",
                started_at=datetime.now(UTC),
            )

        try:
            # Clear decision path for new evaluation
            self.decision_path = []

            # Add trace entry for evaluation start
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_start",
                description="Starting DSL evaluation",
                inputs={"ast_node_type": ast.node_type},
            )

            # Evaluate the AST
            result = self._evaluate_node(ast, correlation_id, trace)

            # Convert result to StrategyAllocation
            if isinstance(result, PortfolioFragment):
                # Convert fragment to allocation
                allocation = self._fragment_to_allocation(result, correlation_id)
            elif isinstance(result, dict):
                # Direct weights dictionary
                allocation = StrategyAllocation(
                    target_weights={k: decimal.Decimal(str(v)) for k, v in result.items()},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            elif isinstance(result, str):
                # Single asset result
                allocation = StrategyAllocation(
                    target_weights={result: decimal.Decimal("1.0")},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            else:
                # Invalid result type - must be PortfolioFragment, dict, or str
                raise DslEvaluationError(
                    f"Evaluation produced invalid type for allocation: {type(result).__name__}. "
                    f"Expected PortfolioFragment, dict, or str."
                )

            # Add final trace entry
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_complete",
                description="DSL evaluation completed successfully",
                outputs={"allocation_assets": len(allocation.target_weights)},
            )

            return allocation, trace

        except Exception as e:
            # Add error trace entry
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_error",
                description=f"DSL evaluation failed: {e}",
                outputs={"error": str(e)},
            )
            raise DslEvaluationError(f"DSL evaluation failed: {e}") from e

    def _evaluate_atom_node(self, node: ASTNode) -> DSLValue:
        """Evaluate an atom node.

        Args:
            node: Atom AST node to evaluate

        Returns:
            The atom value

        """
        return node.get_atom_value()

    def _evaluate_symbol_node(self, node: ASTNode) -> DSLValue:
        """Evaluate a symbol node.

        Args:
            node: Symbol AST node to evaluate

        Returns:
            The symbol name

        """
        # Always return the symbol name; functions are invoked by list application
        return node.get_symbol_name()

    def _evaluate_map_literal(
        self, node: ASTNode, correlation_id: str, trace: Trace
    ) -> dict[str, float | int | decimal.Decimal | str]:
        """Evaluate a map literal node.

        Args:
            node: List node with map metadata
            correlation_id: Correlation ID for tracking
            trace: Trace for logging

        Returns:
            Dictionary representation of the map

        """
        m: dict[str, float | int | decimal.Decimal | str] = {}
        # Expect pairs: keyword/value
        it = iter(node.children)
        for key_node, val_node in zip(it, it, strict=True):
            key = (
                key_node.get_symbol_name()
                if key_node.is_symbol()
                else str(key_node.get_atom_value())
            )
            if key is None:
                key = "unknown"

            val = self._evaluate_node(val_node, correlation_id, trace)
            # Convert the value to an appropriate type
            if isinstance(val, str | int | float | decimal.Decimal):
                m[key] = val
            else:
                m[key] = str(val)
        return m

    def _evaluate_function_application(self, node: ASTNode, context: DslContext) -> DSLValue:
        """Evaluate a function application.

        Args:
            node: List node with function as first child
            context: DSL evaluation context

        Returns:
            Result of function evaluation

        Raises:
            DslEvaluationError: If function name is None or unknown

        """
        first_child = node.children[0]
        func_name = first_child.get_symbol_name()
        if func_name is None:
            raise DslEvaluationError("Function name cannot be None")

        args = node.children[1:]

        # Dispatch to operator function (raises DslEvaluationError if unknown)
        return self.dispatcher.dispatch(func_name, args, context)

    def _evaluate_list_elements(
        self, node: ASTNode, correlation_id: str, trace: Trace
    ) -> list[DSLValue]:
        """Evaluate list elements as a regular list.

        Args:
            node: List node to evaluate
            correlation_id: Correlation ID for tracking
            trace: Trace for logging

        Returns:
            List of evaluated elements

        """
        return [self._evaluate_node(child, correlation_id, trace) for child in node.children]

    def _evaluate_list_node(self, node: ASTNode, correlation_id: str, trace: Trace) -> DSLValue:
        """Evaluate a list node.

        Args:
            node: List AST node to evaluate
            correlation_id: Correlation ID for tracking
            trace: Trace for logging

        Returns:
            Evaluation result based on list type

        """
        if not node.children:
            return []

        # Map literal: convert to dict
        if node.metadata and node.metadata.get("node_subtype") == "map":
            return self._evaluate_map_literal(node, correlation_id, trace)

        # Create context for function applications
        context = DslContext(
            indicator_service=self.indicator_service,
            event_publisher=self.event_publisher,
            correlation_id=correlation_id,
            trace=trace,
            evaluate_node=self._evaluate_node,
        )
        # Share decision_path with context so all contexts accumulate to the same list
        context.decision_path = self.decision_path

        # Function application: (func arg1 arg2 ...)
        first_child = node.children[0]
        if first_child.is_symbol():
            return self._evaluate_function_application(node, context)
        # Evaluate each element and return as list
        return self._evaluate_list_elements(node, correlation_id, trace)

    def _evaluate_node(self, node: ASTNode, correlation_id: str, trace: Trace) -> DSLValue:
        """Evaluate a single AST node.

        Args:
            node: AST node to evaluate
            correlation_id: Correlation ID for tracking
            trace: Trace for logging

        Returns:
            Evaluation result

        """
        if node.is_atom():
            return self._evaluate_atom_node(node)

        if node.is_symbol():
            return self._evaluate_symbol_node(node)

        if node.is_list():
            return self._evaluate_list_node(node, correlation_id, trace)

        raise DslEvaluationError(f"Unknown node type: {node}")

    def _fragment_to_allocation(
        self, fragment: PortfolioFragment, correlation_id: str
    ) -> StrategyAllocation:
        """Convert PortfolioFragment to StrategyAllocation.

        Args:
            fragment: Portfolio fragment to convert
            correlation_id: Correlation ID for tracking

        Returns:
            Strategy allocation with normalized weights

        """
        # Normalize fragment weights first
        normalized_fragment = fragment.normalize_weights()

        # Convert to Decimal for strategy allocation
        target_weights = {
            symbol: decimal.Decimal(str(weight))
            for symbol, weight in normalized_fragment.weights.items()
        }

        return StrategyAllocation(
            target_weights=target_weights,
            correlation_id=correlation_id,
            as_of=datetime.now(UTC),
        )
