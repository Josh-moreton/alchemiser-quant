#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL evaluator for strategy expressions.

Evaluates parsed AST nodes from S-expressions with whitelisted symbol table
and indicator service integration.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.constants import DSL_ENGINE_MODULE
from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import (
    IndicatorRequestDTO,
    PortfolioFragmentDTO,
)
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.dto.trace_dto import TraceDTO
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.events.dsl_events import (
    DecisionEvaluated,
    IndicatorComputed,
)
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators

# Values that may result from evaluating a DSL node
type DSLValue = (
    PortfolioFragmentDTO
    | dict[str, float | int | Decimal | str]
    | list["DSLValue"]
    | str
    | int
    | float
    | bool
    | Decimal
    | None
)


class DslEvaluationError(Exception):
    """Error during DSL evaluation."""


class IndicatorService:
    """Service for computing technical indicators using real market data.

    Integrates with the existing market data infrastructure to provide
    real-time technical indicator calculations for DSL strategy evaluation.
    """

    def __init__(self, market_data_service: MarketDataPort | None) -> None:
        """Initialize indicator service with market data provider.

        Args:
            market_data_service: MarketDataService instance for real market data (None for fallback)

        """
        self.market_data_service = market_data_service
        self.technical_indicators = (
            TechnicalIndicators() if market_data_service else None
        )

    def get_indicator(self, request: IndicatorRequestDTO) -> TechnicalIndicatorDTO:
        """Get technical indicator for symbol using real market data.

        Args:
            request: Indicator request

        Returns:
            TechnicalIndicatorDTO with real indicator data

        """
        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters

        # Require real market data; no mocks
        if not self.market_data_service or not self.technical_indicators:
            raise DslEvaluationError(
                "IndicatorService requires a MarketDataPort; no fallback indicators allowed"
            )

        try:
            # Compute dynamic lookback based on indicator/window to ensure enough bars
            def _required_bars(
                ind_type: str, params: dict[str, int | float | str]
            ) -> int:
                window = int(params.get("window", 0)) if params else 0
                if ind_type in {
                    "moving_average",
                    "exponential_moving_average_price",
                    "max_drawdown",
                }:
                    return max(window, 200)
                if ind_type in {
                    "moving_average_return",
                    "stdev_return",
                    "cumulative_return",
                }:
                    # Need at least window plus some extra for pct_change/shift stability
                    return max(window + 5, 60)
                if ind_type == "rsi":
                    # RSI stabilizes with more data; fetch ~3x window (min 200)
                    return max(window * 3 if window > 0 else 200, 200)
                if ind_type == "current_price":
                    return 1
                return 252  # sensible default (~1Y)

            def _period_for_bars(required_bars: int) -> str:
                # Convert required trading bars to calendar period string understood by MarketDataService
                # Use years granularity to avoid weekend/holiday gaps; add 10% safety margin
                bars_with_buffer = math.ceil(required_bars * 1.1)
                years = max(1, math.ceil(bars_with_buffer / 252))
                return f"{years}Y"

            required = _required_bars(indicator_type, parameters)
            period = _period_for_bars(required)

            # Fetch bars with computed lookback
            symbol_obj = Symbol(symbol)
            bars = self.market_data_service.get_bars(
                symbol=symbol_obj,
                period=period,
                timeframe="1Day",
            )

            if not bars:
                raise DslEvaluationError(
                    f"No market data available for symbol {symbol}"
                )

            # Convert bars to pandas Series for technical indicators
            import pandas as pd

            prices = pd.Series([float(bar.close) for bar in bars])

            if indicator_type == "rsi":
                window = parameters.get("window", 14)
                rsi_series = self.technical_indicators.rsi(prices, window=window)

                # Get the most recent RSI value
                if len(rsi_series) > 0 and not pd.isna(rsi_series.iloc[-1]):
                    rsi_value = float(rsi_series.iloc[-1])
                else:
                    rsi_value = 50.0  # Neutral fallback

                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    rsi_14=rsi_value if window == 14 else None,
                    rsi_10=rsi_value if window == 10 else None,
                    rsi_20=rsi_value if window == 20 else None,
                    rsi_21=rsi_value if window == 21 else None,
                    current_price=(
                        Decimal(str(prices.iloc[-1]))
                        if len(prices) > 0
                        else Decimal("100.0")
                    ),
                    data_source="real_market_data",
                    metadata={"value": rsi_value, "window": window},
                )
            if indicator_type == "current_price":
                last_price = float(prices.iloc[-1]) if len(prices) > 0 else None
                if last_price is None:
                    raise DslEvaluationError(f"No last price for symbol {symbol}")
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    rsi_14=None,
                    rsi_10=None,
                    rsi_21=None,
                    current_price=Decimal(str(last_price)),
                    data_source="real_market_data",
                    metadata={"value": last_price},
                )

            if indicator_type == "moving_average":
                window = int(parameters.get("window", 200))
                ma_series = self.technical_indicators.moving_average(
                    prices, window=window
                )
                import pandas as pd

                latest_ma = float(ma_series.iloc[-1]) if len(ma_series) > 0 else None
                if latest_ma is None or pd.isna(latest_ma):
                    raise DslEvaluationError(
                        f"No moving average available for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    ma_20=latest_ma if window == 20 else None,
                    ma_50=latest_ma if window == 50 else None,
                    ma_200=latest_ma if window == 200 else None,
                    data_source="real_market_data",
                    metadata={"value": latest_ma, "window": window},
                )

            if indicator_type == "moving_average_return":
                window = int(parameters.get("window", 21))
                mar_series = self.technical_indicators.moving_average_return(
                    prices, window=window
                )
                import pandas as pd

                latest = float(mar_series.iloc[-1]) if len(mar_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No moving average return for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    ma_return_90=latest if window == 90 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "cumulative_return":
                window = int(parameters.get("window", 60))
                cum_series = self.technical_indicators.cumulative_return(
                    prices, window=window
                )
                import pandas as pd

                latest = float(cum_series.iloc[-1]) if len(cum_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No cumulative return for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    cum_return_60=latest if window == 60 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "exponential_moving_average_price":
                window = int(parameters.get("window", 12))
                ema_series = self.technical_indicators.exponential_moving_average(
                    prices, window=window
                )
                import pandas as pd

                latest = float(ema_series.iloc[-1]) if len(ema_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No EMA available for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    ema_12=latest if window == 12 else None,
                    ema_26=latest if window == 26 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "stdev_return":
                window = int(parameters.get("window", 6))
                std_series = self.technical_indicators.stdev_return(
                    prices, window=window
                )
                import pandas as pd

                latest = float(std_series.iloc[-1]) if len(std_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No stdev-return for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    stdev_return_6=latest if window == 6 else None,
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            if indicator_type == "max_drawdown":
                window = int(parameters.get("window", 60))
                mdd_series = self.technical_indicators.max_drawdown(
                    prices, window=window
                )
                import pandas as pd

                latest = float(mdd_series.iloc[-1]) if len(mdd_series) > 0 else None
                if latest is None or pd.isna(latest):
                    raise DslEvaluationError(
                        f"No max-drawdown for {symbol} window={window}"
                    )
                return TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=(
                        Decimal(str(prices.iloc[-1])) if len(prices) > 0 else None
                    ),
                    data_source="real_market_data",
                    metadata={"value": latest, "window": window},
                )

            # Unsupported indicator types
            raise DslEvaluationError(f"Unsupported indicator type: {indicator_type}")

        except Exception as e:
            raise DslEvaluationError(
                f"Error getting indicator {indicator_type} for {symbol}: {e}"
            ) from e


class DslEvaluator:
    """Evaluator for DSL strategy expressions.

    Walks AST nodes and evaluates them using whitelisted symbol table
    with indicator service integration and event publishing.
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

        # Whitelisted functions for DSL evaluation
        self.symbol_table: dict[
            str, Callable[[list[ASTNodeDTO], str, TraceDTO], DSLValue]
        ] = {
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
            "current-price": self._eval_current_price,
            "moving-average-price": self._eval_moving_average_price,
            "moving-average-return": self._eval_moving_average_return,
            "cumulative-return": self._eval_cumulative_return,
            "exponential-moving-average-price": self._eval_exponential_moving_average_price,
            "stdev-return": self._eval_stdev_return,
            "max-drawdown": self._eval_max_drawdown,
            "ma": self._eval_moving_average,
            "volatility": self._eval_volatility,
        }

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

            # DEBUG: Log what we got from evaluation
            print(f"DEBUG: DSL evaluation result type: {type(result)}")
            print(f"DEBUG: DSL evaluation result: {result}")

            # Convert result to StrategyAllocationDTO
            if isinstance(result, PortfolioFragmentDTO):
                # Convert fragment to allocation
                allocation = self._fragment_to_allocation(result, correlation_id)
            elif isinstance(result, dict):
                # Direct weights dictionary
                allocation = StrategyAllocationDTO(
                    target_weights={k: Decimal(str(v)) for k, v in result.items()},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            elif isinstance(result, str):
                # Single asset result
                allocation = StrategyAllocationDTO(
                    target_weights={result: Decimal("1.0")},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )
            elif isinstance(result, list) and result:
                # List of assets - equal weight
                weights = {
                    str(asset): Decimal(str(1.0 / len(result)))
                    for asset in result
                    if asset
                }
                if weights:
                    allocation = StrategyAllocationDTO(
                        target_weights=weights,
                        correlation_id=correlation_id,
                        as_of=datetime.now(UTC),
                    )
                else:
                    # Empty result - create fallback allocation
                    allocation = StrategyAllocationDTO(
                        target_weights={"CASH": Decimal("1.0")},
                        correlation_id=correlation_id,
                        as_of=datetime.now(UTC),
                    )
            else:
                # Unknown result type - create fallback allocation
                allocation = StrategyAllocationDTO(
                    target_weights={"CASH": Decimal("1.0")},
                    correlation_id=correlation_id,
                    as_of=datetime.now(UTC),
                )

            # Mark trace as completed
            trace = trace.mark_completed(success=True)
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_complete",
                description="DSL evaluation completed successfully",
                outputs={"allocation": allocation.model_dump()},
            )

            return allocation, trace

        except Exception as e:
            # Mark trace as failed
            trace = trace.mark_completed(success=False, error_message=str(e))
            trace = trace.add_entry(
                step_id=str(uuid.uuid4()),
                step_type="evaluation_error",
                description=f"DSL evaluation failed: {e}",
                metadata={"error_type": type(e).__name__},
            )
            raise DslEvaluationError(f"DSL evaluation failed: {e}") from e

    def _evaluate_node(
        self, node: ASTNodeDTO, correlation_id: str, trace: TraceDTO
    ) -> DSLValue:
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
            # Always return the symbol name; functions are invoked by list application
            return node.get_symbol_name()
        if node.is_list():
            if not node.children:
                return []

            # Map literal: convert to dict
            if node.metadata and node.metadata.get("node_subtype") == "map":
                m: dict[str, float | int | Decimal | str] = {}
                # Expect pairs: keyword/value
                it = iter(node.children)
                for key_node, val_node in zip(it, it, strict=True):
                    key = (
                        key_node.get_symbol_name()
                        if key_node.is_symbol()
                        else str(key_node.value)
                    )
                    key = key.lstrip(":") if isinstance(key, str) else str(key)
                    evaluated = self._evaluate_node(val_node, correlation_id, trace)
                    m[key] = self._coerce_param_value(evaluated)
                return m

            # First child should be the function
            func_node = node.children[0]
            if not func_node.is_symbol():
                # If first child is not a symbol, treat as data list
                return [
                    self._evaluate_node(child, correlation_id, trace)
                    for child in node.children
                ]

            func_name = func_node.get_symbol_name()
            if func_name not in self.symbol_table:
                # Unknown function - treat as data list
                return [
                    self._evaluate_node(child, correlation_id, trace)
                    for child in node.children
                ]

            func = self.symbol_table[func_name]
            args = node.children[1:]

            return func(args, correlation_id, trace)
        raise DslEvaluationError(f"Unknown node type: {node.node_type}")

    def _fragment_to_allocation(
        self, fragment: PortfolioFragmentDTO, correlation_id: str
    ) -> StrategyAllocationDTO:
        """Convert portfolio fragment to strategy allocation.

        Args:
            fragment: Portfolio fragment
            correlation_id: Correlation ID

        Returns:
            StrategyAllocationDTO

        """
        print(f"DEBUG: Fragment weights: {fragment.weights}")
        weights = {k: Decimal(str(v)) for k, v in fragment.weights.items()}
        print(f"DEBUG: Converted weights: {weights}")

        # If no weights, create a fallback cash allocation
        if not weights:
            print("DEBUG: No weights, creating CASH fallback")
            weights = {"CASH": Decimal("1.0")}

        print(f"DEBUG: Final weights for allocation: {weights}")

        return StrategyAllocationDTO(
            target_weights=weights,
            correlation_id=correlation_id,
            as_of=datetime.now(UTC),
        )

    def _coerce_param_value(self, val: DSLValue) -> float | int | Decimal | str:
        """Coerce a DSLValue into a scalar suitable for parameter maps.

        Allowed types: int, float, Decimal, str. Booleans are coerced to int (1/0).
        Raises DslEvaluationError for non-scalar values.
        """
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, (int, float, Decimal, str)):
            return val
        raise DslEvaluationError(
            f"Map literal values must be scalar (int|float|Decimal|string); got {type(val)}"
        )

    # DSL function implementations

    def _as_decimal(self, val: DSLValue) -> Decimal:
        """Coerce a DSLValue to Decimal for numeric comparisons."""
        if isinstance(val, Decimal):
            return val
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        if isinstance(val, str):
            try:
                return Decimal(val)
            except Exception:
                return Decimal("0")
        return Decimal("0")

    def _eval_defsymphony(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> DSLValue:
        """Evaluate defsymphony - main strategy definition."""
        if len(args) < 3:
            raise DslEvaluationError("defsymphony requires at least 3 arguments")

        _name = args[0]  # Strategy name (unused in evaluation)
        _config = args[1]  # Strategy config (unused in evaluation)
        body = args[2]

        # Evaluate the strategy body
        return self._evaluate_node(body, correlation_id, trace)

    def _eval_weight_equal(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> PortfolioFragmentDTO:
        """Evaluate weight-equal - equal weight allocation."""
        if not args:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()), source_step="weight_equal", weights={}
            )

        # Collect all assets from arguments
        all_assets: list[str] = []

        for arg in args:
            result = self._evaluate_node(arg, correlation_id, trace)

            if isinstance(result, PortfolioFragmentDTO):
                # Add all assets from this fragment
                for symbol in result.weights:
                    all_assets.append(symbol)
            elif isinstance(result, list):
                # Handle list of results - recursively process nested lists
                def process_list_items(items: Iterable[DSLValue]) -> list[str]:
                    assets: list[str] = []
                    for item in items:
                        if isinstance(item, PortfolioFragmentDTO):
                            assets.extend(item.weights.keys())
                        elif isinstance(item, str):
                            assets.append(item)
                        elif isinstance(item, list):
                            # Recursively process nested lists
                            assets.extend(process_list_items(item))
                    return assets

                nested_assets = process_list_items(result)
                all_assets.extend(nested_assets)
            elif isinstance(result, str):
                # Direct symbol string
                all_assets.append(result)

        # Create equal weights for all collected assets
        if not all_assets:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()), source_step="weight_equal", weights={}
            )

        # Remove duplicates while preserving order
        unique_assets: list[str] = []
        seen: set[str] = set()
        for asset in all_assets:
            if asset not in seen:
                unique_assets.append(asset)
                seen.add(asset)

        weight_per_asset = 1.0 / len(unique_assets)
        weights = dict.fromkeys(unique_assets, weight_per_asset)

        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_equal",
            weights=weights,
        )

    def _eval_weight_specified(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> PortfolioFragmentDTO:
        """Evaluate weight-specified - specified weight allocation.

        Format: (weight-specified weight1 asset1 weight2 asset2 ...)
        """
        if len(args) < 2 or len(args) % 2 != 0:
            raise DslEvaluationError(
                "weight-specified requires pairs of weight and asset arguments"
            )

        weights: dict[str, float] = {}

        def collect_normalized_weights(value: DSLValue) -> dict[str, float]:
            collected: dict[str, float] = {}
            if isinstance(value, str):
                collected[value] = 1.0
                return collected
            if isinstance(value, PortfolioFragmentDTO):
                frag = value.normalize_weights()
                return dict(frag.weights)
            if isinstance(value, list):
                for item in value:
                    nested = collect_normalized_weights(item)
                    for sym, w in nested.items():
                        collected[sym] = collected.get(sym, 0.0) + w
                total = sum(collected.values())
                if total > 0:
                    collected = {sym: w / total for sym, w in collected.items()}
                return collected
            return collected

        # Process weight-asset pairs
        for i in range(0, len(args), 2):
            weight_node = args[i]
            asset_node = args[i + 1]

            # Evaluate weight (should be a number)
            weight_value = self._evaluate_node(weight_node, correlation_id, trace)
            if not isinstance(weight_value, (int, float, Decimal)):
                raise DslEvaluationError(
                    f"Weight must be a number, got {type(weight_value)}"
                )

            weight = float(weight_value)

            # Evaluate asset (should be a symbol or asset result)
            asset_result = self._evaluate_node(asset_node, correlation_id, trace)

            normalized = collect_normalized_weights(asset_result)
            if not normalized:
                raise DslEvaluationError(
                    f"Expected asset symbol or fragment, got {type(asset_result)}"
                )
            for symbol, base_w in normalized.items():
                scaled = base_w * weight
                weights[symbol] = weights.get(symbol, 0.0) + scaled

        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_specified",
            weights=weights,
        )

    def _eval_weight_inverse_volatility(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> PortfolioFragmentDTO:
        """Evaluate weight-inverse-volatility - inverse volatility weighting.

        Format: (weight-inverse-volatility window [assets...])
        """
        if not args:
            raise DslEvaluationError(
                "weight-inverse-volatility requires window and assets"
            )

        # First argument is the window
        window_node = args[0]
        window = self._evaluate_node(window_node, correlation_id, trace)

        if not isinstance(window, (int, float, Decimal)):
            raise DslEvaluationError(f"Window must be a number, got {type(window)}")

        # Collect assets from remaining arguments
        all_assets: list[str] = []
        for arg in args[1:]:
            result = self._evaluate_node(arg, correlation_id, trace)

            if isinstance(result, PortfolioFragmentDTO):
                all_assets.extend(result.weights.keys())
            elif isinstance(result, list):
                for item in result:
                    if isinstance(item, PortfolioFragmentDTO):
                        all_assets.extend(item.weights.keys())
                    elif isinstance(item, str):
                        all_assets.append(item)
            elif isinstance(result, str):
                all_assets.append(result)

        if not all_assets:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()),
                source_step="weight_inverse_volatility",
                weights={},
            )

        # Calculate inverse volatility weights
        # For now, use mock volatilities - in real implementation would calculate from price history
        mock_volatilities = {
            "UVXY": 0.8,  # High volatility
            "BTAL": 0.2,  # Low volatility
            "TLT": 0.15,
            "QQQ": 0.25,
            "SPY": 0.20,
            "TQQQ": 0.6,
            "SQQQ": 0.6,
        }

        # Calculate inverse weights
        inverse_weights = {}
        total_inverse = 0.0

        for asset in all_assets:
            volatility = mock_volatilities.get(asset, 0.25)  # Default volatility
            inverse_vol = 1.0 / volatility
            inverse_weights[asset] = inverse_vol
            total_inverse += inverse_vol

        # Normalize to sum to 1
        normalized_weights = {}
        for asset, inv_weight in inverse_weights.items():
            normalized_weights[asset] = inv_weight / total_inverse

        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_inverse_volatility",
            weights=normalized_weights,
        )

    def _eval_group(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> DSLValue:
        """Evaluate group - aggregate results from body expressions.

        Groups act as composition blocks in the DSL. We evaluate each body
        expression and combine any resulting portfolio fragments by summing
        weights. If no weights are produced by the body, we fall back to the
        result of the last expression to preserve compatibility.
        """
        if len(args) < 2:
            raise DslEvaluationError("group requires at least 2 arguments")

        _name = args[0]  # Group name (unused in evaluation)
        body = args[1:]

        combined: dict[str, float] = {}
        last_result: DSLValue = None

        def _merge_weights_from(value: DSLValue) -> None:
            if isinstance(value, PortfolioFragmentDTO):
                for sym, w in value.weights.items():
                    combined[sym] = combined.get(sym, 0.0) + float(w)
            elif isinstance(value, list):
                for item in value:
                    _merge_weights_from(item)
            elif isinstance(value, str):
                combined[value] = combined.get(value, 0.0) + 1.0

        # Evaluate each expression and merge any weights found
        for expr in body:
            res = self._evaluate_node(expr, correlation_id, trace)
            last_result = res
            _merge_weights_from(res)

        # If we gathered any weights, return as a fragment; else, return last result
        if combined:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()),
                source_step="group",
                weights=combined,
            )

        # No combined weights produced: if single body item, return its result; otherwise last
        return (
            last_result
            if last_result is not None
            else PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()), source_step="group", weights={}
            )
        )

    def _eval_asset(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> str:
        """Evaluate asset - single asset allocation."""
        if not args:
            raise DslEvaluationError("asset requires at least 1 argument")

        symbol_node = args[0]
        symbol = self._evaluate_node(symbol_node, correlation_id, trace)

        if not isinstance(symbol, str):
            raise DslEvaluationError(f"Asset symbol must be string, got {type(symbol)}")

        # Return just the symbol string - weight-equal will handle creating the fragment
        return symbol

    def _eval_if(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> DSLValue:
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
                source_module=DSL_ENGINE_MODULE,
                decision_expression=condition,
                condition_result=bool(condition_result),
                branch_taken=branch_taken,
                branch_result=(
                    result if isinstance(result, PortfolioFragmentDTO) else None
                ),
            )
            self.event_bus.publish(decision_event)

        return result

    def _eval_filter(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> PortfolioFragmentDTO:
        """Evaluate filter - filter assets by criteria and select top/bottom.

        Format: (filter indicator selector assets)
        Example: (filter (rsi {:window 10}) (select-top 1) [(asset "A") (asset "B")])
        """
        if len(args) < 3:
            raise DslEvaluationError(
                "filter requires indicator, selector, and assets arguments"
            )

        indicator_expr = args[0]
        selector_expr = args[1]
        assets_expr = args[2]

        # Evaluate the assets list
        assets_result = self._evaluate_node(assets_expr, correlation_id, trace)

        # Extract assets from the result
        assets = []
        if isinstance(assets_result, list):
            for item in assets_result:
                if isinstance(item, str):
                    assets.append(item)
                elif isinstance(item, PortfolioFragmentDTO):
                    assets.extend(item.weights.keys())

        if not assets:
            return PortfolioFragmentDTO(
                fragment_id=str(uuid.uuid4()), source_step="filter", weights={}
            )

        # Evaluate indicator for each asset and collect scores
        asset_scores: list[tuple[str, float]] = []
        for asset in assets:
            try:
                # Evaluate indicator with this asset
                if indicator_expr.is_list() and indicator_expr.children:
                    # Replace or add symbol parameter to indicator
                    modified_indicator = self._create_indicator_with_symbol(
                        indicator_expr, asset
                    )
                    score_val = self._evaluate_node(
                        modified_indicator, correlation_id, trace
                    )
                else:
                    score_val = self._evaluate_node(
                        indicator_expr, correlation_id, trace
                    )

                coerced: float
                if isinstance(score_val, (int, float, Decimal)):
                    coerced = float(score_val)
                elif isinstance(score_val, str):
                    try:
                        coerced = float(Decimal(score_val))
                    except Exception:
                        coerced = 50.0
                else:
                    coerced = 50.0

                asset_scores.append((asset, coerced))
            except Exception:
                # If evaluation fails, use neutral score
                asset_scores.append((asset, 50.0))

        # Apply selector
        # Determine how many to select (top/bottom)
        n_select = 1
        select_type = "top"
        if selector_expr.is_list() and selector_expr.children:
            func_name = selector_expr.children[0].get_symbol_name()
            if func_name == "select-top":
                select_type = "top"
                if len(selector_expr.children) > 1:
                    n_val = self._evaluate_node(
                        selector_expr.children[1], correlation_id, trace
                    )
                    if isinstance(n_val, (int, Decimal)):
                        n_select = int(n_val)
            elif func_name == "select-bottom":
                select_type = "bottom"
                if len(selector_expr.children) > 1:
                    n_val = self._evaluate_node(
                        selector_expr.children[1], correlation_id, trace
                    )
                    if isinstance(n_val, (int, Decimal)):
                        n_select = int(n_val)

        # Sort and select
        if select_type == "top":
            sorted_assets = sorted(asset_scores, key=lambda x: x[1], reverse=True)
        else:
            sorted_assets = sorted(asset_scores, key=lambda x: x[1])

        selected_assets = [asset for asset, _score in sorted_assets[:n_select]]

        # Create equal weight allocation for selected assets
        if selected_assets:
            weight_per_asset = 1.0 / len(selected_assets)
            weights = dict.fromkeys(selected_assets, weight_per_asset)
        else:
            weights = {}

        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()), source_step="filter", weights=weights
        )

    def _create_indicator_with_symbol(
        self, indicator_expr: ASTNodeDTO, symbol: str
    ) -> ASTNodeDTO:
        """Create indicator expression with specific symbol."""
        if not indicator_expr.is_list() or not indicator_expr.children:
            return indicator_expr

        # For RSI indicator, create: (rsi "SYMBOL" {:window N})
        func_name = indicator_expr.children[0].get_symbol_name()
        if func_name in {
            "rsi",
            "moving-average-price",
            "moving-average-return",
            "cumulative-return",
            "exponential-moving-average-price",
            "stdev-return",
            "max-drawdown",
        }:
            children = [ASTNodeDTO.symbol(func_name), ASTNodeDTO.atom(symbol)]
            # Add parameters if present
            if len(indicator_expr.children) > 1:
                children.append(indicator_expr.children[1])
            else:
                # Add default window parameter per indicator
                default_window = 10
                if func_name == "moving-average-price":
                    default_window = 200
                elif func_name == "moving-average-return":
                    default_window = 21
                elif func_name == "cumulative-return":
                    default_window = 60
                elif func_name == "exponential-moving-average-price":
                    default_window = 12
                elif func_name == "stdev-return":
                    default_window = 6
                elif func_name == "rsi":
                    default_window = 14
                elif func_name == "max-drawdown":
                    default_window = 60

                children.append(
                    ASTNodeDTO.list_node(
                        [
                            ASTNodeDTO.symbol(":window"),
                            ASTNodeDTO.atom(Decimal(str(default_window))),
                        ],
                        metadata={"node_subtype": "map"},
                    )
                )

            return ASTNodeDTO.list_node(children)

        return indicator_expr

    def _eval_select_top(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> int:
        """Evaluate select-top - select top N assets."""
        if not args:
            raise DslEvaluationError("select-top requires at least 1 argument")

        n_node = args[0]
        n = self._evaluate_node(n_node, correlation_id, trace)

        if not isinstance(n, (int, Decimal)):
            raise DslEvaluationError(f"select-top N must be number, got {type(n)}")

        return int(n)

    def _eval_select_bottom(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> int:
        """Evaluate select-bottom - select bottom N assets."""
        if not args:
            raise DslEvaluationError("select-bottom requires at least 1 argument")

        n_node = args[0]
        n = self._evaluate_node(n_node, correlation_id, trace)

        if not isinstance(n, (int, Decimal)):
            raise DslEvaluationError(f"select-bottom N must be number, got {type(n)}")

        return int(n)

    def _eval_greater_than(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> bool:
        """Evaluate > - greater than comparison."""
        if len(args) != 2:
            raise DslEvaluationError("> requires exactly 2 arguments")

        left_v = self._evaluate_node(args[0], correlation_id, trace)
        right_v = self._evaluate_node(args[1], correlation_id, trace)
        return self._as_decimal(left_v) > self._as_decimal(right_v)

    def _eval_less_than(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> bool:
        """Evaluate < - less than comparison."""
        if len(args) != 2:
            raise DslEvaluationError("< requires exactly 2 arguments")

        left_v = self._evaluate_node(args[0], correlation_id, trace)
        right_v = self._evaluate_node(args[1], correlation_id, trace)
        return self._as_decimal(left_v) < self._as_decimal(right_v)

    def _eval_greater_equal(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> bool:
        """Evaluate >= - greater than or equal comparison."""
        if len(args) != 2:
            raise DslEvaluationError(">= requires exactly 2 arguments")

        left_v = self._evaluate_node(args[0], correlation_id, trace)
        right_v = self._evaluate_node(args[1], correlation_id, trace)
        return self._as_decimal(left_v) >= self._as_decimal(right_v)

    def _eval_less_equal(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> bool:
        """Evaluate <= - less than or equal comparison."""
        if len(args) != 2:
            raise DslEvaluationError("<= requires exactly 2 arguments")

        left_v = self._evaluate_node(args[0], correlation_id, trace)
        right_v = self._evaluate_node(args[1], correlation_id, trace)
        return self._as_decimal(left_v) <= self._as_decimal(right_v)

    def _eval_equal(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> bool:
        """Evaluate = - equality comparison."""
        if len(args) != 2:
            raise DslEvaluationError("= requires exactly 2 arguments")

        left_v = self._evaluate_node(args[0], correlation_id, trace)
        right_v = self._evaluate_node(args[1], correlation_id, trace)

        def to_decimal_if_number(val: DSLValue) -> Decimal | None:
            if isinstance(val, Decimal):
                return val
            if isinstance(val, (int, float)):
                return Decimal(str(val))
            return None

        l_num = to_decimal_if_number(left_v)
        r_num = to_decimal_if_number(right_v)
        if l_num is not None and r_num is not None:
            return l_num == r_num
        if isinstance(left_v, str) and isinstance(right_v, str):
            return left_v == right_v
        return False

    def _eval_rsi(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
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
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 14

        # Request indicator from service
        request = IndicatorRequestDTO.rsi_request(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol,
            window=window,
        )

        indicator = self.indicator_service.get_indicator(request)

        # Publish indicator computed event
        if self.event_bus:
            indicator_event = IndicatorComputed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                source_module=DSL_ENGINE_MODULE,
                request_id=request.request_id,
                indicator=indicator,
                computation_time_ms=0.0,  # Mock timing
            )
            self.event_bus.publish(indicator_event)

        # Extract RSI value based on window
        if window == 10:
            return indicator.rsi_10 or 50.0
        if window == 14:
            return indicator.rsi_14 or 50.0
        if window == 20:
            return indicator.rsi_20 or 50.0
        if window == 21:
            return indicator.rsi_21 or 50.0

        # For arbitrary windows, use metadata value
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])  # type: ignore[misc]
            except Exception as exc:
                print(f"DEBUG: Failed to coerce RSI metadata value: {exc}")

        # Final fallback
        return indicator.rsi_14 or 50.0

    def _eval_moving_average(
        self, _args: list[ASTNodeDTO], _correlation_id: str, _trace: TraceDTO
    ) -> float:
        """Evaluate ma - disabled mock; not implemented."""
        raise DslEvaluationError(
            "ma is not implemented in DSL evaluator; use moving-average-* indicators via data layer"
        )

    def _eval_volatility(
        self, _args: list[ASTNodeDTO], _correlation_id: str, _trace: TraceDTO
    ) -> float:
        """Evaluate volatility - disabled mock; not implemented."""
        raise DslEvaluationError(
            "volatility is not implemented in DSL evaluator; compute via data layer"
        )

    def _eval_current_price(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate current-price - get current price of symbol (requires market data)."""
        if not args:
            raise DslEvaluationError("current-price requires symbol argument")

        symbol_node = args[0]
        symbol = self._evaluate_node(symbol_node, correlation_id, trace)

        if not isinstance(symbol, str):
            raise DslEvaluationError(f"Symbol must be string, got {type(symbol)}")

        # Get indicator to access current price
        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol,
            indicator_type="current_price",
            parameters={},
        )

        indicator = self.indicator_service.get_indicator(request)
        if indicator.current_price is None:
            raise DslEvaluationError(f"No current price available for {symbol}")
        return float(indicator.current_price)

    def _eval_moving_average_price(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate moving-average-price using TechnicalIndicators via IndicatorService."""
        if not args:
            raise DslEvaluationError("moving-average-price requires symbol and params")

        symbol_val = self._evaluate_node(args[0], correlation_id, trace)
        if not isinstance(symbol_val, str):
            raise DslEvaluationError(f"Symbol must be string, got {type(symbol_val)}")

        window = 200
        if len(args) > 1:
            params = self._evaluate_node(args[1], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 200

        request = IndicatorRequestDTO.moving_average_request(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            window=window,
        )
        indicator = self.indicator_service.get_indicator(request)
        # Choose appropriate field or fallback to provided MA
        if window == 20 and indicator.ma_20 is not None:
            return float(indicator.ma_20)
        if window == 50 and indicator.ma_50 is not None:
            return float(indicator.ma_50)
        if window == 200 and indicator.ma_200 is not None:
            return float(indicator.ma_200)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce MA metadata value: {exc}")
        raise DslEvaluationError(
            f"Moving average for {symbol_val} window={window} not available"
        )

    def _eval_moving_average_return(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate moving-average-return via IndicatorService."""
        if not args:
            raise DslEvaluationError(
                "moving-average-return requires params and optional symbol"
            )

        # Signature may be (moving-average-return {:window N}) or (moving-average-return "SYM" {:window N})
        idx = 0
        symbol_val: str | None = None
        first = self._evaluate_node(args[0], correlation_id, trace)
        if isinstance(first, str):
            symbol_val = first
            idx = 1

        window = 21
        if len(args) > idx:
            params = self._evaluate_node(args[idx], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 21

        if symbol_val is None:
            raise DslEvaluationError(
                "moving-average-return requires an explicit symbol when evaluated standalone"
            )

        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            indicator_type="moving_average_return",
            parameters={"window": window},
        )
        indicator = self.indicator_service.get_indicator(request)
        # We only have a fixed ma_return_90 field; return any numeric present or fallback to metadata
        if window == 90 and indicator.ma_return_90 is not None:
            return float(indicator.ma_return_90)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce MAR metadata value: {exc}")
        raise DslEvaluationError(
            f"moving-average-return for {symbol_val} window={window} not available"
        )

    def _eval_cumulative_return(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate cumulative-return via IndicatorService."""
        if not args:
            raise DslEvaluationError("cumulative-return requires symbol and params")

        idx = 0
        symbol_val: str | None = None
        first = self._evaluate_node(args[0], correlation_id, trace)
        if isinstance(first, str):
            symbol_val = first
            idx = 1

        window = 60
        if len(args) > idx:
            params = self._evaluate_node(args[idx], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 60

        if symbol_val is None:
            raise DslEvaluationError(
                "cumulative-return requires an explicit symbol when evaluated standalone"
            )

        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            indicator_type="cumulative_return",
            parameters={"window": window},
        )
        indicator = self.indicator_service.get_indicator(request)
        if window == 60 and indicator.cum_return_60 is not None:
            return float(indicator.cum_return_60)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce CUMRET metadata value: {exc}")
        raise DslEvaluationError(
            f"cumulative-return for {symbol_val} window={window} not available"
        )

    def _eval_exponential_moving_average_price(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate exponential-moving-average-price via IndicatorService."""
        if not args:
            raise DslEvaluationError(
                "exponential-moving-average-price requires symbol and params"
            )

        symbol_val = self._evaluate_node(args[0], correlation_id, trace)
        if not isinstance(symbol_val, str):
            raise DslEvaluationError(f"Symbol must be string, got {type(symbol_val)}")

        window = 12
        if len(args) > 1:
            params = self._evaluate_node(args[1], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 12

        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            indicator_type="exponential_moving_average_price",
            parameters={"window": window},
        )
        indicator = self.indicator_service.get_indicator(request)
        if window == 12 and indicator.ema_12 is not None:
            return float(indicator.ema_12)
        if window == 26 and indicator.ema_26 is not None:
            return float(indicator.ema_26)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce EMA metadata value: {exc}")
        raise DslEvaluationError(f"EMA for {symbol_val} window={window} not available")

    def _eval_stdev_return(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate stdev-return via IndicatorService (percent units)."""
        if not args:
            raise DslEvaluationError("stdev-return requires symbol and params")

        idx = 0
        symbol_val: str | None = None
        first = self._evaluate_node(args[0], correlation_id, trace)
        if isinstance(first, str):
            symbol_val = first
            idx = 1

        window = 6
        if len(args) > idx:
            params = self._evaluate_node(args[idx], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 6

        if symbol_val is None:
            raise DslEvaluationError(
                "stdev-return requires an explicit symbol when evaluated standalone"
            )

        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            indicator_type="stdev_return",
            parameters={"window": window},
        )
        indicator = self.indicator_service.get_indicator(request)
        if window == 6 and indicator.stdev_return_6 is not None:
            return float(indicator.stdev_return_6)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce STDEV metadata value: {exc}")
        raise DslEvaluationError(
            f"stdev-return for {symbol_val} window={window} not available"
        )

    def _eval_max_drawdown(
        self, args: list[ASTNodeDTO], correlation_id: str, trace: TraceDTO
    ) -> float:
        """Evaluate max-drawdown via IndicatorService (percent magnitude)."""
        if not args:
            raise DslEvaluationError("max-drawdown requires symbol and params")

        idx = 0
        symbol_val: str | None = None
        first = self._evaluate_node(args[0], correlation_id, trace)
        if isinstance(first, str):
            symbol_val = first
            idx = 1

        window = 60
        if len(args) > idx:
            params = self._evaluate_node(args[idx], correlation_id, trace)
            if isinstance(params, dict):
                try:
                    window = int(params.get("window", window))
                except (ValueError, TypeError):
                    window = 60

        if symbol_val is None:
            raise DslEvaluationError(
                "max-drawdown requires an explicit symbol when evaluated standalone"
            )

        request = IndicatorRequestDTO(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            symbol=symbol_val,
            indicator_type="max_drawdown",
            parameters={"window": window},
        )
        indicator = self.indicator_service.get_indicator(request)
        if indicator.metadata and "value" in indicator.metadata:
            try:
                return float(indicator.metadata["value"])
            except Exception as exc:
                print(f"DEBUG: Failed to coerce MDD metadata value: {exc}")
        raise DslEvaluationError(
            f"max-drawdown for {symbol_val} window={window} not available"
        )
