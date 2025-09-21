#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL evaluator for strategy expressions.

Evaluates parsed AST nodes from S-expressions with whitelisted symbol table
and indicator service integration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import IndicatorRequestDTO, PortfolioFragmentDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    DecisionEvaluated,
    IndicatorComputed,
)


class DslEvaluationError(Exception):
    """Error during DSL evaluation."""



class IndicatorService:
    """Service for computing technical indicators.
    
    Placeholder implementation - in real system this would integrate with
    existing indicator calculation infrastructure.
    """
    
    def __init__(self) -> None:
        """Initialize indicator service."""
        # Mock indicator data for development
        self._mock_indicators: dict[str, dict[str, float]] = {
            "QQQE": {"rsi_10": 75.0, "rsi_14": 72.0},
            "VTV": {"rsi_10": 65.0, "rsi_14": 68.0},
            "VOX": {"rsi_10": 85.0, "rsi_14": 82.0},
            "TECL": {"rsi_10": 80.0, "rsi_14": 78.0},
            "VOOG": {"rsi_10": 70.0, "rsi_14": 72.0},
            "VOOV": {"rsi_10": 60.0, "rsi_14": 62.0},
            "XLP": {"rsi_10": 76.0, "rsi_14": 74.0},
            "TQQQ": {"rsi_10": 25.0, "rsi_14": 28.0},  # Low RSI for pop condition
            "XLY": {"rsi_10": 75.0, "rsi_14": 73.0},
            "FAS": {"rsi_10": 70.0, "rsi_14": 72.0},
            "SPY": {"rsi_10": 75.0, "rsi_14": 73.0},
            "SOXL": {"rsi_10": 35.0, "rsi_14": 38.0},  # Low RSI for pop condition
            "SPXL": {"rsi_10": 35.0, "rsi_14": 38.0},  # Low RSI for pop condition
            "LABU": {"rsi_10": 20.0, "rsi_14": 22.0},  # Very low RSI for pop condition
            "XLK": {"rsi_10": 65.0, "rsi_14": 67.0},
            "KMLM": {"rsi_10": 70.0, "rsi_14": 72.0},
        }
    
    def get_indicator(self, request: IndicatorRequestDTO) -> TechnicalIndicatorDTO:
        """Get technical indicator for symbol.
        
        Args:
            request: Indicator request
            
        Returns:
            TechnicalIndicatorDTO with indicator data

        """
        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters
        
        # Mock implementation
        if symbol in self._mock_indicators:
            indicator_data = self._mock_indicators[symbol]
            
            if indicator_type == "rsi":
                window = parameters.get("window", 14)
                rsi_key = f"rsi_{window}"
                rsi_value = indicator_data.get(rsi_key, indicator_data.get("rsi_14", 50.0))
                
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    rsi_14=rsi_value if window == 14 else None,
                    rsi_10=rsi_value if window == 10 else None,
                    rsi_21=rsi_value if window == 21 else None,
                    current_price=Decimal("100.0"),  # Mock price
                    data_source="mock_indicator_service"
                )
        
        # Default values for unknown symbols
        return TechnicalIndicatorDTO(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            rsi_14=50.0,  # Neutral RSI
            rsi_10=50.0,
            rsi_21=50.0,
            current_price=Decimal("100.0"),
            data_source="mock_indicator_service"
        )


class DslEvaluator:
    """Evaluator for DSL strategy expressions.
    
    Walks AST nodes and evaluates them using whitelisted symbol table
    with indicator service integration and event publishing.
    """

    def __init__(
        self, 
        indicator_service: IndicatorService,
        event_bus: EventBus | None = None
    ) -> None:
        """Initialize DSL evaluator.
        
        Args:
            indicator_service: Service for computing indicators
            event_bus: Optional event bus for publishing events

        """
        self.indicator_service = indicator_service
        self.event_bus = event_bus
        
        # Whitelisted symbols for DSL evaluation
        self.symbol_table = {
            # Core functions
            "defsymphony": self._eval_defsymphony,
            "weight-equal": self._eval_weight_equal,
            "weight-specified": self._eval_weight_specified,
            "weight-inverse-volatility": self._eval_weight_inverse_volatility,
            "group": self._eval_group,
            "asset": self._eval_asset,
            "if": self._eval_if,
            "filter": self._eval_filter,
            "select-top": self._eval_select_top,
            "select-bottom": self._eval_select_bottom,
            
            # Comparison operators
            ">": self._eval_greater_than,
            "<": self._eval_less_than,
            ">=": self._eval_greater_equal,
            "<=": self._eval_less_equal,
            "=": self._eval_equal,
            
            # Indicator functions
            "rsi": self._eval_rsi,
            "ma": self._eval_moving_average,
            "volatility": self._eval_volatility,
        }

    def evaluate(
        self, 
        ast: ASTNodeDTO, 
        correlation_id: str,
        trace: TraceDTO | None = None
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
                started_at=datetime.now(UTC)
            )
        
        try:
            # Add trace entry for evaluation start
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_start",
                description="Starting DSL evaluation",
                inputs={"ast_node_type": ast.node_type}
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
                    target_weights={k: Decimal(str(v)) for k, v in result.items()},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC)
                )
            else:
                raise DslEvaluationError(f"Unexpected evaluation result type: {type(result)}")
            
            # Mark trace as completed
            trace = trace.mark_completed(success=True)
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_complete",
                description="DSL evaluation completed successfully",
                outputs={"allocation": allocation.model_dump()}
            )
            
            return allocation, trace
            
        except Exception as e:
            # Mark trace as failed
            trace = trace.mark_completed(success=False, error_message=str(e))
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_error",
                description=f"DSL evaluation failed: {e}",
                metadata={"error_type": type(e).__name__}
            )
            raise DslEvaluationError(f"DSL evaluation failed: {e}") from e

    def _evaluate_node(
        self, 
        node: ASTNodeDTO, 
        correlation_id: str, 
        trace: TraceDTO
    ) -> Any:  # type: ignore[misc]  # DSL evaluation can return various types
        """Evaluate a single AST node.
        
        Args:
            node: AST node to evaluate
            correlation_id: Correlation ID for tracking
            trace: Trace for logging
            
        Returns:
            Evaluation result

        """
        if node.is_atom():
            return node.get_atom_value()
        if node.is_symbol():
            symbol_name = node.get_symbol_name()
            if symbol_name in self.symbol_table:
                return self.symbol_table[symbol_name]
            # For unknown symbols, return the symbol name as string
            return symbol_name
        if node.is_list():
            if not node.children:
                return []
            
            # First child should be the function
            func_node = node.children[0]
            if not func_node.is_symbol():
                # If first child is not a symbol, treat as data list
                return [self._evaluate_node(child, correlation_id, trace) for child in node.children]
            
            func_name = func_node.get_symbol_name()
            if func_name not in self.symbol_table:
                # Unknown function - treat as data list
                return [self._evaluate_node(child, correlation_id, trace) for child in node.children]
            
            func = self.symbol_table[func_name]
            args = node.children[1:]
            
            return func(args, correlation_id, trace)
        raise DslEvaluationError(f"Unknown node type: {node.node_type}")

    def _fragment_to_allocation(
        self, 
        fragment: PortfolioFragmentDTO, 
        correlation_id: str
    ) -> StrategyAllocationDTO:
        """Convert portfolio fragment to strategy allocation.
        
        Args:
            fragment: Portfolio fragment
            correlation_id: Correlation ID
            
        Returns:
            StrategyAllocationDTO

        """
        weights = {k: Decimal(str(v)) for k, v in fragment.weights.items()}
        return StrategyAllocationDTO(
            target_weights=weights,
            correlation_id=correlation_id,
            as_of=datetime.now(UTC)
        )

    # DSL function implementations
    
    def _eval_defsymphony(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> Any:  # type: ignore[misc]  # DSL function can return various types
        """Evaluate defsymphony - main strategy definition."""
        if len(args) < 3:
            raise DslEvaluationError("defsymphony requires at least 3 arguments")
        
        _name = args[0]  # Strategy name (unused in evaluation)
        _config = args[1]  # Strategy config (unused in evaluation)
        body = args[2]
        
        # Evaluate the strategy body
        return self._evaluate_node(body, correlation_id, trace)

    def _eval_weight_equal(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> PortfolioFragmentDTO:
        """Evaluate weight-equal - equal weight allocation."""
        if not args:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()),
                source_step="weight_equal",
                weights={}
            )
        
        # Evaluate all arguments and collect allocations
        allocations = []
        for arg in args:
            result = self._evaluate_node(arg, correlation_id, trace)
            if isinstance(result, PortfolioFragmentDTO):
                allocations.append(result)
            elif isinstance(result, list) and result:
                # Handle list of assets
                for item in result:
                    if isinstance(item, PortfolioFragmentDTO):
                        allocations.append(item)
        
        # Combine allocations with equal weights
        if not allocations:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()),
                source_step="weight_equal",
                weights={}
            )
        
        combined_weights = {}
        weight_per_allocation = 1.0 / len(allocations)
        
        for allocation in allocations:
            for symbol, weight in allocation.weights.items():
                if symbol in combined_weights:
                    combined_weights[symbol] += weight * weight_per_allocation
                else:
                    combined_weights[symbol] = weight * weight_per_allocation
        
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_equal",
            weights=combined_weights
        )

    def _eval_weight_specified(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> PortfolioFragmentDTO:
        """Evaluate weight-specified - specified weight allocation."""
        # TODO: Implement weight-specified logic
        return self._eval_weight_equal(args, correlation_id, trace)

    def _eval_weight_inverse_volatility(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> PortfolioFragmentDTO:
        """Evaluate weight-inverse-volatility - inverse volatility weighting."""
        # TODO: Implement inverse volatility weighting
        return self._eval_weight_equal(args, correlation_id, trace)

    def _eval_group(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> Any:  # type: ignore[misc]  # DSL function can return various types
        """Evaluate group - grouping construct."""
        if len(args) < 2:
            raise DslEvaluationError("group requires at least 2 arguments")
        
        _name = args[0]  # Group name (unused in evaluation)
        body = args[1:]
        
        # Evaluate the group body
        if len(body) == 1:
            return self._evaluate_node(body[0], correlation_id, trace)
        # Multiple expressions - evaluate last one
        result = None
        for expr in body:
            result = self._evaluate_node(expr, correlation_id, trace)
        return result

    def _eval_asset(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> PortfolioFragmentDTO:
        """Evaluate asset - single asset allocation."""
        if not args:
            raise DslEvaluationError("asset requires at least 1 argument")
        
        symbol_node = args[0]
        symbol = self._evaluate_node(symbol_node, correlation_id, trace)
        
        if not isinstance(symbol, str):
            raise DslEvaluationError(f"Asset symbol must be string, got {type(symbol)}")
        
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="asset",
            weights={symbol: 1.0}
        )

    def _eval_if(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> Any:  # type: ignore[misc]  # DSL function can return various types
        """Evaluate if - conditional expression."""
        if len(args) < 2:
            raise DslEvaluationError("if requires at least 2 arguments")
        
        condition = args[0]
        then_expr = args[1]
        else_expr = args[2] if len(args) > 2 else None
        
        # Evaluate condition
        condition_result = self._evaluate_node(condition, correlation_id, trace)
        
        # Determine branch
        if condition_result:
            branch_taken = "then"
            result = self._evaluate_node(then_expr, correlation_id, trace)
        elif else_expr:
            branch_taken = "else"
            result = self._evaluate_node(else_expr, correlation_id, trace)
        else:
            branch_taken = "else"
            result = None
        
        # Publish decision event
        if self.event_bus:
            decision_event = DecisionEvaluated(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                source_module="strategy_v2.engines.dsl",
                decision_expression=condition,
                condition_result=bool(condition_result),
                branch_taken=branch_taken,
                branch_result=result if isinstance(result, PortfolioFragmentDTO) else None
            )
            self.event_bus.publish(decision_event)
        
        return result

    def _eval_filter(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> list[PortfolioFragmentDTO]:
        """Evaluate filter - filter assets by criteria."""
        # TODO: Implement filter logic
        return []

    def _eval_select_top(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> Any:  # type: ignore[misc]  # DSL function can return various types
        """Evaluate select-top - select top N assets."""
        if not args:
            raise DslEvaluationError("select-top requires at least 1 argument")
        
        n_node = args[0]
        n = self._evaluate_node(n_node, correlation_id, trace)
        
        if not isinstance(n, (int, Decimal)):
            raise DslEvaluationError(f"select-top N must be number, got {type(n)}")
        
        # TODO: Implement actual selection logic
        return n

    def _eval_select_bottom(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> Any:  # type: ignore[misc]  # DSL function can return various types
        """Evaluate select-bottom - select bottom N assets."""
        if not args:
            raise DslEvaluationError("select-bottom requires at least 1 argument")
        
        n_node = args[0]
        n = self._evaluate_node(n_node, correlation_id, trace)
        
        if not isinstance(n, (int, Decimal)):
            raise DslEvaluationError(f"select-bottom N must be number, got {type(n)}")
        
        # TODO: Implement actual selection logic
        return n

    def _eval_greater_than(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> bool:
        """Evaluate > - greater than comparison."""
        if len(args) != 2:
            raise DslEvaluationError("> requires exactly 2 arguments")
        
        left = self._evaluate_node(args[0], correlation_id, trace)
        right = self._evaluate_node(args[1], correlation_id, trace)
        
        return float(left) > float(right)

    def _eval_less_than(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> bool:
        """Evaluate < - less than comparison."""
        if len(args) != 2:
            raise DslEvaluationError("< requires exactly 2 arguments")
        
        left = self._evaluate_node(args[0], correlation_id, trace)
        right = self._evaluate_node(args[1], correlation_id, trace)
        
        return float(left) < float(right)

    def _eval_greater_equal(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> bool:
        """Evaluate >= - greater than or equal comparison."""
        if len(args) != 2:
            raise DslEvaluationError(">= requires exactly 2 arguments")
        
        left = self._evaluate_node(args[0], correlation_id, trace)
        right = self._evaluate_node(args[1], correlation_id, trace)
        
        return float(left) >= float(right)

    def _eval_less_equal(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> bool:
        """Evaluate <= - less than or equal comparison."""
        if len(args) != 2:
            raise DslEvaluationError("<= requires exactly 2 arguments")
        
        left = self._evaluate_node(args[0], correlation_id, trace)
        right = self._evaluate_node(args[1], correlation_id, trace)
        
        return float(left) <= float(right)

    def _eval_equal(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> bool:
        """Evaluate = - equality comparison."""
        if len(args) != 2:
            raise DslEvaluationError("= requires exactly 2 arguments")
        
        left = self._evaluate_node(args[0], correlation_id, trace)
        right = self._evaluate_node(args[1], correlation_id, trace)
        
        return left == right

    def _eval_rsi(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> float:
        """Evaluate rsi - RSI indicator."""
        if not args:
            raise DslEvaluationError("rsi requires at least 1 argument")
        
        symbol_node = args[0]
        symbol = self._evaluate_node(symbol_node, correlation_id, trace)
        
        if not isinstance(symbol, str):
            raise DslEvaluationError(f"RSI symbol must be string, got {type(symbol)}")
        
        # Parse parameters
        window = 14  # Default window
        if len(args) > 1:
            params_node = args[1]
            params = self._evaluate_node(params_node, correlation_id, trace)
            if isinstance(params, dict) and "window" in params:
                window = int(params["window"])
        
        # Request indicator from service
        request = IndicatorRequestDTO.rsi_request(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol,
            window=window
        )
        
        indicator = self.indicator_service.get_indicator(request)
        
        # Publish indicator computed event
        if self.event_bus:
            indicator_event = IndicatorComputed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                source_module="strategy_v2.engines.dsl",
                request_id=request.request_id,
                indicator=indicator,
                computation_time_ms=0.0  # Mock timing
            )
            self.event_bus.publish(indicator_event)
        
        # Extract RSI value based on window
        if window == 10:
            return indicator.rsi_10 or 50.0
        if window == 14:
            return indicator.rsi_14 or 50.0
        if window == 21:
            return indicator.rsi_21 or 50.0
        return indicator.rsi_14 or 50.0

    def _eval_moving_average(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> float:
        """Evaluate ma - moving average indicator."""
        # TODO: Implement moving average logic
        return 100.0

    def _eval_volatility(self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO) -> float:
        """Evaluate volatility - volatility indicator."""
        # TODO: Implement volatility logic
        return 0.2