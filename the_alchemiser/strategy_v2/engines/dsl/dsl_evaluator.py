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

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import PortfolioFragmentDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService

from .context import DslContext
from .dispatcher import DslDispatcher
from .events import DslEventPublisher
from .operators.comparison import register_comparison_operators
from .operators.control_flow import register_control_flow_operators
from .operators.indicators import register_indicator_operators
from .operators.portfolio import register_portfolio_operators
from .operators.selection import register_selection_operators
from .types import DSLValue, DslEvaluationError


class DslEvaluator:
    """Evaluator for DSL strategy expressions.

    Walks AST nodes and evaluates them using a dispatcher-based operator
    registry with indicator service integration and event publishing.
    """

    def __init__(
        self, indicator_service: IndicatorService, event_bus: EventBus | None = None
    ) -> None:
        """Initialize DSL evaluator.

        Args:
            indicator_service: Service for computing indicators
            event_bus: Optional event bus for publishing events

        """
        self.indicator_service = indicator_service
        self.event_bus = event_bus
        self.event_publisher = DslEventPublisher(event_bus)
        
        # Initialize dispatcher and register all operators
        self.dispatcher = DslDispatcher()
        self._register_all_operators()

    def _register_all_operators(self) -> None:
        """Register all DSL operators with the dispatcher."""
        register_portfolio_operators(self.dispatcher)
        register_selection_operators(self.dispatcher)
        register_comparison_operators(self.dispatcher)
        register_control_flow_operators(self.dispatcher)
        register_indicator_operators(self.dispatcher)

    def evaluate(
        self, ast: ASTNodeDTO, correlation_id: str, trace: TraceDTO | None = None
    ) -> tuple[StrategyAllocationDTO, TraceDTO]:
        """Evaluate AST and return allocation with trace.

        Args:
            ast: AST to evaluate
            correlation_id: Correlation ID for tracking
            trace: Optional existing trace to append to

        Returns:
            Tuple of (StrategyAllocationDTO, TraceDTO)

        Raises:
            DslEvaluationError: If evaluation fails

        """
        if trace is None:
            trace = TraceDTO(
                trace_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                strategy_id="dsl_strategy",
                started_at=datetime.now(UTC),
            )

        try:
            # Add trace entry for evaluation start
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_start",
                description="Starting DSL evaluation",
                inputs={"ast_node_type": ast.node_type},
            )

            # Evaluate the AST
            result = self._evaluate_node(ast, correlation_id, trace)

            # Convert result to StrategyAllocationDTO
            if isinstance(result, PortfolioFragmentDTO):
                # Convert fragment to allocation
                allocation = self._fragment_to_allocation(result, correlation_id)
            elif isinstance(result, dict):
                # Direct weights dictionary
                allocation = StrategyAllocationDTO(
                    target_weights={k: decimal.Decimal(str(v)) for k, v in result.items()},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            elif isinstance(result, str):
                # Single asset result
                allocation = StrategyAllocationDTO(
                    target_weights={result: decimal.Decimal("1.0")},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            else:
                # Fallback for other types
                allocation = StrategyAllocationDTO(
                    target_weights={},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
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

    def _evaluate_node(self, node: ASTNodeDTO, correlation_id: str, trace: TraceDTO) -> DSLValue:
        """Evaluate a single AST node.

        Args:
            node: AST node to evaluate
            correlation_id: Correlation ID for tracking
            trace: Trace for logging

        Returns:
            Evaluation result

        """
        # Create context for operators
        context = DslContext(
            indicator_service=self.indicator_service,
            event_publisher=self.event_publisher,
            correlation_id=correlation_id,
            trace=trace,
            evaluate_node=self._evaluate_node,
        )

        if node.is_atom():
            return node.get_atom_value()
        if node.is_symbol():
            # Always return the symbol name; functions are invoked by list application
            return node.get_symbol_name()
        if node.is_list():
            if not node.children:
                return []

            # Map literal: convert to dict
            if node.metadata and node.metadata.get("node_subtype") == "map":
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
                    if isinstance(val, (str, int, float)):
                        m[key] = val
                    elif isinstance(val, decimal.Decimal):
                        m[key] = val
                    else:
                        m[key] = str(val)
                return m

            # Function application: (func arg1 arg2 ...)
            first_child = node.children[0]
            if first_child.is_symbol():
                func_name = first_child.get_symbol_name()
                if func_name is None:
                    raise DslEvaluationError("Function name cannot be None")
                
                args = node.children[1:]

                # Dispatch to operator function
                try:
                    return self.dispatcher.dispatch(func_name, args, context)
                except KeyError:
                    raise DslEvaluationError(f"Unknown function: {func_name}")
            else:
                # Evaluate each element and return as list
                return [self._evaluate_node(child, correlation_id, trace) for child in node.children]

        raise DslEvaluationError(f"Unknown node type: {node}")

    def _fragment_to_allocation(
        self, fragment: PortfolioFragmentDTO, correlation_id: str
    ) -> StrategyAllocationDTO:
        """Convert PortfolioFragmentDTO to StrategyAllocationDTO.

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

        return StrategyAllocationDTO(
            target_weights=target_weights,
            correlation_id=correlation_id,
            as_of=datetime.now(UTC),
        )
