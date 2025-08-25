"""
Pure DSL evaluator for the S-expression Strategy Engine.

Evaluates parsed AST nodes into portfolio weights using whitelisted functions
and market data access. Provides deterministic evaluation with structured tracing.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Union

from the_alchemiser.domain.dsl.ast import (
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
from the_alchemiser.domain.dsl.errors import EvaluationError, IndicatorError, PortfolioError
from the_alchemiser.domain.math.indicators import TechnicalIndicators
from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort

# Type for evaluation results
Portfolio = dict[str, Decimal]
EvalResult = Union[float, bool, Portfolio]


class DSLEvaluator:
    """Pure evaluator for DSL AST nodes with market data access."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize evaluator with market data access.
        
        Args:
            market_data_port: Market data access interface
        """
        self.market_data_port = market_data_port
        self._indicator_cache: dict[str, Any] = {}
        self._trace_entries: list[dict[str, Any]] = []

    def evaluate(self, ast_node: ASTNode) -> EvalResult:
        """Evaluate AST node to produce result.
        
        Args:
            ast_node: AST node to evaluate
            
        Returns:
            Evaluation result (float, bool, or portfolio dict)
            
        Raises:
            EvaluationError: If evaluation fails
        """
        self._trace_entries.clear()
        self._indicator_cache.clear()

        try:
            result = self._evaluate_node(ast_node)
            return result
        except (EvaluationError, IndicatorError, PortfolioError):
            raise
        except Exception as e:
            raise EvaluationError(f"Unexpected evaluation error: {e}", ast_node=ast_node) from e

    def get_trace(self) -> list[dict[str, Any]]:
        """Get structured trace of evaluation decisions."""
        return self._trace_entries.copy()

    def _evaluate_node(self, node: ASTNode) -> EvalResult:
        """Evaluate a single AST node."""

        # Literals
        if isinstance(node, NumberLiteral):
            return node.value
        elif isinstance(node, Symbol):
            raise EvaluationError(f"Unresolved symbol: {node.name}", symbol=node.name)

        # Comparisons
        elif isinstance(node, GreaterThan):
            return self._evaluate_comparison(node, operator=">")
        elif isinstance(node, LessThan):
            return self._evaluate_comparison(node, operator="<")

        # Control flow
        elif isinstance(node, If):
            return self._evaluate_if(node)

        # Indicators
        elif isinstance(node, RSI):
            return self._evaluate_rsi(node)
        elif isinstance(node, MovingAveragePrice):
            return self._evaluate_moving_average_price(node)
        elif isinstance(node, MovingAverageReturn):
            return self._evaluate_moving_average_return(node)
        elif isinstance(node, CumulativeReturn):
            return self._evaluate_cumulative_return(node)
        elif isinstance(node, CurrentPrice):
            return self._evaluate_current_price(node)
        elif isinstance(node, StdevReturn):
            return self._evaluate_stdev_return(node)

        # Portfolio construction
        elif isinstance(node, Asset):
            return self._evaluate_asset(node)
        elif isinstance(node, Group):
            return self._evaluate_group(node)
        elif isinstance(node, WeightEqual):
            return self._evaluate_weight_equal(node)
        elif isinstance(node, WeightSpecified):
            return self._evaluate_weight_specified(node)
        elif isinstance(node, WeightInverseVolatility):
            return self._evaluate_weight_inverse_volatility(node)

        # Selectors
        elif isinstance(node, Filter):
            return self._evaluate_filter(node)

        # Strategy root
        elif isinstance(node, Strategy):
            return self._evaluate_strategy(node)

        # Generic function call
        elif isinstance(node, FunctionCall):
            raise EvaluationError(f"Unknown function: {node.function_name}")

        else:
            raise EvaluationError(f"Unknown AST node type: {type(node)}")

    def _evaluate_comparison(self, node: GreaterThan | LessThan, operator: str) -> bool:
        """Evaluate comparison operator."""
        left_result = self._evaluate_node(node.left)
        right_result = self._evaluate_node(node.right)

        # Ensure numeric values
        if not isinstance(left_result, (int, float)):
            raise EvaluationError(f"Left side of {operator} must be numeric, got {type(left_result)}")
        if not isinstance(right_result, (int, float)):
            raise EvaluationError(f"Right side of {operator} must be numeric, got {type(right_result)}")

        if operator == ">":
            result = left_result > right_result
        elif operator == "<":
            result = left_result < right_result
        else:
            raise EvaluationError(f"Unknown comparison operator: {operator}")

        # Trace the comparison
        self._trace_entries.append({
            "type": "comparison",
            "operator": operator,
            "left_value": left_result,
            "right_value": right_result,
            "result": result
        })

        return result

    def _evaluate_if(self, node: If) -> EvalResult:
        """Evaluate if conditional."""
        condition_result = self._evaluate_node(node.condition)

        # Condition must be boolean
        if not isinstance(condition_result, bool):
            raise EvaluationError("If condition must evaluate to boolean")

        if condition_result:
            result = self._evaluate_node(node.then_expr)
            branch = "then"
        elif node.else_expr is not None:
            result = self._evaluate_node(node.else_expr)
            branch = "else"
        else:
            # No else clause and condition is false
            raise EvaluationError("If condition false but no else clause provided")

        # Trace the branch decision
        self._trace_entries.append({
            "type": "conditional",
            "condition": condition_result,
            "branch_taken": branch,
            "result_type": type(result).__name__
        })

        return result

    def _evaluate_rsi(self, node: RSI) -> float:
        """Evaluate RSI indicator."""
        cache_key = f"rsi_{node.symbol}_{node.window}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get market data
                data = self.market_data_port.get_data(node.symbol, timeframe="1day", period="1y")
                if data.empty:
                    raise IndicatorError(f"No data available for {node.symbol}", indicator="rsi", symbol=node.symbol)

                # Calculate RSI using existing indicator
                rsi_series = TechnicalIndicators.rsi(data['close'], node.window)
                if rsi_series.empty:
                    raise IndicatorError(f"RSI calculation failed for {node.symbol}", indicator="rsi", symbol=node.symbol)

                # Get latest value
                latest_rsi = rsi_series.dropna().iloc[-1] if not rsi_series.dropna().empty else None
                if latest_rsi is None:
                    raise IndicatorError(f"No valid RSI value for {node.symbol}", indicator="rsi", symbol=node.symbol)

                result = float(latest_rsi)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"RSI calculation error for {node.symbol}: {e}", indicator="rsi", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "rsi",
            "symbol": node.symbol,
            "window": node.window,
            "value": result
        })

        return result

    def _evaluate_moving_average_price(self, node: MovingAveragePrice) -> float:
        """Evaluate moving average price indicator."""
        cache_key = f"ma_price_{node.symbol}_{node.window}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get market data
                data = self.market_data_port.get_data(node.symbol, timeframe="1day", period="1y")
                if data.empty:
                    raise IndicatorError(f"No data available for {node.symbol}", indicator="moving_average_price", symbol=node.symbol)

                # Calculate moving average using existing indicator
                ma_series = TechnicalIndicators.moving_average(data['close'], node.window)
                if ma_series.empty:
                    raise IndicatorError(f"Moving average calculation failed for {node.symbol}", indicator="moving_average_price", symbol=node.symbol)

                # Get latest value
                latest_ma = ma_series.dropna().iloc[-1] if not ma_series.dropna().empty else None
                if latest_ma is None:
                    raise IndicatorError(f"No valid moving average value for {node.symbol}", indicator="moving_average_price", symbol=node.symbol)

                result = float(latest_ma)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"Moving average calculation error for {node.symbol}: {e}", indicator="moving_average_price", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "moving_average_price",
            "symbol": node.symbol,
            "window": node.window,
            "value": result
        })

        return result

    def _evaluate_moving_average_return(self, node: MovingAverageReturn) -> float:
        """Evaluate moving average return indicator."""
        cache_key = f"ma_return_{node.symbol}_{node.window}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get market data
                data = self.market_data_port.get_data(node.symbol, timeframe="1day", period="1y")
                if data.empty:
                    raise IndicatorError(f"No data available for {node.symbol}", indicator="moving_average_return", symbol=node.symbol)

                # Calculate moving average return using existing indicator
                ma_return_series = TechnicalIndicators.moving_average_return(data['close'], node.window)
                if ma_return_series.empty:
                    raise IndicatorError(f"Moving average return calculation failed for {node.symbol}", indicator="moving_average_return", symbol=node.symbol)

                # Get latest value
                latest_ma_return = ma_return_series.dropna().iloc[-1] if not ma_return_series.dropna().empty else None
                if latest_ma_return is None:
                    raise IndicatorError(f"No valid moving average return value for {node.symbol}", indicator="moving_average_return", symbol=node.symbol)

                result = float(latest_ma_return)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"Moving average return calculation error for {node.symbol}: {e}", indicator="moving_average_return", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "moving_average_return",
            "symbol": node.symbol,
            "window": node.window,
            "value": result
        })

        return result

    def _evaluate_cumulative_return(self, node: CumulativeReturn) -> float:
        """Evaluate cumulative return indicator."""
        cache_key = f"cum_return_{node.symbol}_{node.window}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get market data
                data = self.market_data_port.get_data(node.symbol, timeframe="1day", period="1y")
                if data.empty:
                    raise IndicatorError(f"No data available for {node.symbol}", indicator="cumulative_return", symbol=node.symbol)

                # Calculate cumulative return using existing indicator
                cum_return_series = TechnicalIndicators.cumulative_return(data['close'], node.window)
                if cum_return_series.empty:
                    raise IndicatorError(f"Cumulative return calculation failed for {node.symbol}", indicator="cumulative_return", symbol=node.symbol)

                # Get latest value
                latest_cum_return = cum_return_series.dropna().iloc[-1] if not cum_return_series.dropna().empty else None
                if latest_cum_return is None:
                    raise IndicatorError(f"No valid cumulative return value for {node.symbol}", indicator="cumulative_return", symbol=node.symbol)

                result = float(latest_cum_return)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"Cumulative return calculation error for {node.symbol}: {e}", indicator="cumulative_return", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "cumulative_return",
            "symbol": node.symbol,
            "window": node.window,
            "value": result
        })

        return result

    def _evaluate_current_price(self, node: CurrentPrice) -> float:
        """Evaluate current price indicator."""
        cache_key = f"current_price_{node.symbol}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get current price from market data port
                current_price = self.market_data_port.get_current_price(node.symbol)
                if current_price is None:
                    raise IndicatorError(f"No current price available for {node.symbol}", indicator="current_price", symbol=node.symbol)

                result = float(current_price)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"Current price error for {node.symbol}: {e}", indicator="current_price", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "current_price",
            "symbol": node.symbol,
            "value": result
        })

        return result

    def _evaluate_stdev_return(self, node: StdevReturn) -> float:
        """Evaluate standard deviation of returns indicator."""
        cache_key = f"stdev_return_{node.symbol}_{node.window}"

        if cache_key in self._indicator_cache:
            result = self._indicator_cache[cache_key]
        else:
            try:
                # Get market data
                data = self.market_data_port.get_data(node.symbol, timeframe="1day", period="1y")
                if data.empty:
                    raise IndicatorError(f"No data available for {node.symbol}", indicator="stdev_return", symbol=node.symbol)

                # Calculate returns first
                returns = data['close'].pct_change().dropna()

                # Calculate rolling standard deviation of returns
                stdev_series = returns.rolling(window=node.window).std()
                if stdev_series.empty:
                    raise IndicatorError(f"Standard deviation calculation failed for {node.symbol}", indicator="stdev_return", symbol=node.symbol)

                # Get latest value
                latest_stdev = stdev_series.dropna().iloc[-1] if not stdev_series.dropna().empty else None
                if latest_stdev is None:
                    raise IndicatorError(f"No valid standard deviation value for {node.symbol}", indicator="stdev_return", symbol=node.symbol)

                result = float(latest_stdev)
                self._indicator_cache[cache_key] = result

            except Exception as e:
                if isinstance(e, IndicatorError):
                    raise
                raise IndicatorError(f"Standard deviation calculation error for {node.symbol}: {e}", indicator="stdev_return", symbol=node.symbol) from e

        # Trace indicator calculation
        self._trace_entries.append({
            "type": "indicator",
            "indicator": "stdev_return",
            "symbol": node.symbol,
            "window": node.window,
            "value": result
        })

        return result

    def _evaluate_asset(self, node: Asset) -> Portfolio:
        """Evaluate asset to single-asset portfolio."""
        portfolio = {node.symbol: Decimal('1.0')}

        # Trace portfolio construction
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "asset",
            "symbol": node.symbol,
            "name": node.name,
            "weights": portfolio
        })

        return portfolio

    def _evaluate_group(self, node: Group) -> Portfolio:
        """Evaluate group - just a metadata wrapper."""
        if len(node.expressions) != 1:
            # For simplicity, assume group contains one expression
            # Real implementation might handle multiple expressions differently
            raise PortfolioError(f"Group {node.name} should contain exactly one expression", operation="group")

        result = self._evaluate_node(node.expressions[0])
        if not isinstance(result, dict):
            raise PortfolioError("Group expression must evaluate to portfolio", operation="group")

        # Trace group evaluation
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "group",
            "name": node.name,
            "weights": result
        })

        return result

    def _evaluate_weight_equal(self, node: WeightEqual) -> Portfolio:
        """Evaluate equal weight portfolio."""
        portfolios = []

        for expr in node.expressions:
            result = self._evaluate_node(expr)
            if isinstance(result, dict):
                portfolios.append(result)
            else:
                raise PortfolioError(f"weight-equal expression must evaluate to portfolio, got {type(result)}", operation="weight_equal")

        # Flatten and equal-weight
        flattened = self._flatten_portfolios(portfolios)
        equal_weighted = self._equal_weight_portfolio(flattened)

        # Trace portfolio construction
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "weight_equal",
            "input_portfolios": len(portfolios),
            "weights": equal_weighted
        })

        return equal_weighted

    def _evaluate_weight_specified(self, node: WeightSpecified) -> Portfolio:
        """Evaluate explicitly weighted portfolio."""
        weighted_portfolios = []

        for weight, expr in node.weights_and_expressions:
            result = self._evaluate_node(expr)
            if isinstance(result, dict):
                # Scale the portfolio by the weight (convert weight to Decimal)
                weight_decimal = Decimal(str(weight))
                scaled = {symbol: w * weight_decimal for symbol, w in result.items()}
                weighted_portfolios.append(scaled)
            else:
                raise PortfolioError(f"weight-specified expression must evaluate to portfolio, got {type(result)}", operation="weight_specified")

        # Combine weighted portfolios
        combined = self._combine_portfolios(weighted_portfolios)
        normalized = self._normalize_portfolio(combined)

        # Trace portfolio construction
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "weight_specified",
            "input_weights": [w for w, _ in node.weights_and_expressions],
            "weights": normalized
        })

        return normalized

    def _evaluate_weight_inverse_volatility(self, node: WeightInverseVolatility) -> Portfolio:
        """Evaluate inverse volatility weighted portfolio."""
        # This is a simplified implementation - real implementation would need
        # to calculate volatility over the lookback period for each sub-portfolio
        portfolios = []

        for expr in node.expressions:
            result = self._evaluate_node(expr)
            if isinstance(result, dict):
                portfolios.append(result)
            else:
                raise PortfolioError(f"weight-inverse-volatility expression must evaluate to portfolio, got {type(result)}", operation="weight_inverse_volatility")

        # For now, just equal weight (TODO: implement proper inverse vol weighting)
        flattened = self._flatten_portfolios(portfolios)
        equal_weighted = self._equal_weight_portfolio(flattened)

        # Trace portfolio construction
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "weight_inverse_volatility",
            "lookback": node.lookback,
            "input_portfolios": len(portfolios),
            "weights": equal_weighted,
            "warning": "Using simplified equal weighting. Proper inverse volatility weighting not yet implemented."
        })

        return equal_weighted

    def _evaluate_filter(self, node: Filter) -> Portfolio:
        """Evaluate filter selector with metric-based asset selection."""
        # Evaluate the selector to get type and count
        if isinstance(node.selector, SelectTop):
            select_count = node.selector.count
            select_type = "top"
        elif isinstance(node.selector, SelectBottom):
            select_count = node.selector.count
            select_type = "bottom"
        else:
            raise EvaluationError(f"Unknown selector type: {type(node.selector)}", ast_node=node.selector)

        # Evaluate metric for each asset
        asset_metrics = []
        for asset_node in node.assets:
            # Get asset symbol
            if isinstance(asset_node, Asset):
                symbol = asset_node.symbol
            else:
                raise EvaluationError("Filter can only be applied to asset nodes", ast_node=asset_node)

            # Create a modified metric function with the asset symbol
            metric_value = self._evaluate_metric_for_symbol(node.metric_fn, symbol)
            asset_metrics.append((symbol, metric_value, asset_node))

        # Sort by metric value
        if select_type == "top":
            # For top selection, we want highest values first
            sorted_assets = sorted(asset_metrics, key=lambda x: x[1], reverse=True)
        else:
            # For bottom selection, we want lowest values first
            sorted_assets = sorted(asset_metrics, key=lambda x: x[1])

        # Select the requested number of assets
        selected_assets = sorted_assets[:select_count]

        # Create portfolios for selected assets
        selected_portfolios = []
        for symbol, metric_value, asset_node in selected_assets:
            portfolio = self._evaluate_node(asset_node)
            if isinstance(portfolio, dict):
                selected_portfolios.append(portfolio)
            else:
                raise PortfolioError(f"Asset must evaluate to portfolio, got {type(portfolio)}", operation="filter")

        # Equal weight the selected assets
        if selected_portfolios:
            flattened = self._flatten_portfolios(selected_portfolios)
            result = self._equal_weight_portfolio(flattened)
        else:
            result = {}

        # Trace filter operation
        self._trace_entries.append({
            "type": "portfolio",
            "operation": "filter",
            "selector_type": select_type,
            "selector_count": select_count,
            "total_assets": len(node.assets),
            "selected_assets": [asset[0] for asset in selected_assets],
            "metric_values": {asset[0]: asset[1] for asset in selected_assets},
            "weights": result
        })

        return result

    def _evaluate_metric_for_symbol(self, metric_fn: ASTNode, symbol: str) -> float:
        """Evaluate metric function for a specific symbol."""
        # Replace any symbol references in the metric function with the current symbol
        modified_metric = self._substitute_symbol_in_metric(metric_fn, symbol)

        # Evaluate the modified metric
        result = self._evaluate_node(modified_metric)

        if not isinstance(result, (int, float)):
            raise EvaluationError(f"Metric function must return numeric value, got {type(result)}")

        return float(result)

    def _substitute_symbol_in_metric(self, metric_fn: ASTNode, symbol: str) -> ASTNode:
        """Substitute symbol parameter in metric function for filter evaluation."""
        # For metrics that take symbol as first parameter, we need to create a new instance
        # with the provided symbol

        if isinstance(metric_fn, RSI):
            # Use the metric's window but substitute the symbol
            return RSI(symbol=symbol, window=metric_fn.window)
        elif isinstance(metric_fn, StdevReturn):
            return StdevReturn(symbol=symbol, window=metric_fn.window)
        elif isinstance(metric_fn, MovingAverageReturn):
            return MovingAverageReturn(symbol=symbol, window=metric_fn.window)
        elif isinstance(metric_fn, MovingAveragePrice):
            return MovingAveragePrice(symbol=symbol, window=metric_fn.window)
        elif isinstance(metric_fn, CumulativeReturn):
            return CumulativeReturn(symbol=symbol, window=metric_fn.window)
        elif isinstance(metric_fn, CurrentPrice):
            return CurrentPrice(symbol=symbol)
        else:
            raise EvaluationError(f"Unsupported metric function for filter: {type(metric_fn)}", ast_node=metric_fn)

    def _evaluate_strategy(self, node: Strategy) -> Portfolio:
        """Evaluate strategy root node."""
        result = self._evaluate_node(node.expression)
        if not isinstance(result, dict):
            raise PortfolioError(f"Strategy must evaluate to portfolio, got {type(result)}", operation="strategy")

        # Trace strategy evaluation
        self._trace_entries.append({
            "type": "strategy",
            "name": node.name,
            "metadata": node.metadata,
            "final_weights": result
        })

        return result

    def _flatten_portfolios(self, portfolios: list[Portfolio]) -> list[str]:
        """Flatten portfolios to list of unique symbols."""
        symbols: set[str] = set()
        for portfolio in portfolios:
            symbols.update(portfolio.keys())
        return list(symbols)

    def _equal_weight_portfolio(self, symbols: list[str]) -> Portfolio:
        """Create equal-weight portfolio from symbols."""
        if not symbols:
            return {}

        weight = Decimal('1.0') / Decimal(str(len(symbols)))
        return dict.fromkeys(symbols, weight)

    def _combine_portfolios(self, portfolios: list[Portfolio]) -> Portfolio:
        """Combine multiple portfolios by summing weights."""
        combined: dict[str, Decimal] = {}
        for portfolio in portfolios:
            for symbol, weight in portfolio.items():
                combined[symbol] = combined.get(symbol, Decimal('0.0')) + weight
        return combined

    def _normalize_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Normalize portfolio weights to sum to 1.0."""
        if not portfolio:
            return {}

        total_weight = sum(portfolio.values())
        if total_weight == Decimal('0.0'):
            raise PortfolioError("Cannot normalize portfolio with zero total weight", operation="normalize")

        return {symbol: weight / total_weight for symbol, weight in portfolio.items()}
