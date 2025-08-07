#!/usr/bin/env python3
"""
Multi-Strategy Portfolio Manager

This module manages multiple trading strategies running in parallel with portfolio allocation.
It tracks positions for each strategy separately to prevent confusion and enables proper
portfolio management across multiple strategy signals.

Key Features:
- Portfolio allocation between strategies (e.g., 50% Nuclear, 50% TECL)
- Position tracking per strategy
- Strategy execution coordination
- Consolidated reporting
- Registry-based strategy management for static analysis
"""

import logging
from datetime import datetime
from typing import Any

from the_alchemiser.core.registry import StrategyRegistry, StrategyType
from the_alchemiser.core.trading.nuclear_signals import ActionType

# Phase 6 - Strategy Layer Types
from ..exceptions import (
    DataProviderError,
    StrategyExecutionError,
)

__all__ = ["StrategyType"]


class StrategyPosition:
    """Represents a position held by a specific strategy"""

    def __init__(
        self,
        strategy_type: StrategyType,
        symbol: str,
        allocation: float,
        reason: str,
        timestamp: datetime,
    ):
        self.strategy_type = strategy_type
        self.symbol = symbol
        self.allocation = allocation  # Percentage of strategy's allocation
        self.reason = reason
        self.timestamp = timestamp

    def to_dict(self) -> dict[str, Any]:  # TODO: Phase 6 - Migrate to StrategyPositionData
        return {
            "strategy_type": self.strategy_type.value,
            "symbol": self.symbol,
            "allocation": self.allocation,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(
        cls, data: dict[str, Any]
    ) -> "StrategyPosition":  # TODO: Phase 6 - Migrate parameter to StrategyPositionData
        return cls(
            strategy_type=StrategyType(data["strategy_type"]),
            symbol=data["symbol"],
            allocation=data["allocation"],
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class MultiStrategyManager:
    """Manages multiple trading strategies with portfolio allocation"""

    def __init__(
        self,
        strategy_allocations: dict[StrategyType, float] | None = None,
        shared_data_provider: Any = None,
        config: Any = None,
    ):
        """
        Initialize multi-strategy manager

        Args:
            strategy_allocations: Dict mapping strategy types to portfolio percentages
                                Example: {StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5}
            shared_data_provider: Shared UnifiedDataProvider instance (optional)
            config: Configuration object. If None, will load from global config.
        """
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import load_settings

            config = load_settings()
        self.config = config

        # Default allocation from registry if not specified
        if strategy_allocations is None:
            self.strategy_allocations = StrategyRegistry.get_default_allocations()
        else:
            # Filter to only include enabled strategies
            self.strategy_allocations = {
                strategy_type: allocation
                for strategy_type, allocation in strategy_allocations.items()
                if StrategyRegistry.is_strategy_enabled(strategy_type)
            }

            # Remove strategies with zero allocation to keep clean allocations dict
            self.strategy_allocations = {
                k: v for k, v in self.strategy_allocations.items() if v > 0
            }

        # Validate allocations sum to 1.0
        total_allocation = sum(self.strategy_allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Strategy allocations must sum to 1.0, got {total_allocation}")

        # Use provided shared_data_provider, or create one if not given
        if shared_data_provider is None:
            from the_alchemiser.core.data.data_provider import UnifiedDataProvider

            shared_data_provider = UnifiedDataProvider(paper_trading=True)

        # Create strategy engines using the registry
        self.strategy_engines = {}
        for strategy_type in self.strategy_allocations.keys():
            try:
                engine = StrategyRegistry.create_strategy_engine(
                    strategy_type, data_provider=shared_data_provider
                )
                self.strategy_engines[strategy_type] = engine
                logging.info(
                    f"{strategy_type.value} strategy initialized with {self.strategy_allocations[strategy_type]:.1%} allocation"
                )
            except StrategyExecutionError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_initialization",
                    strategy_type=strategy_type.value,
                    error_type=type(e).__name__,
                )
                logging.error(f"Failed to initialize {strategy_type.value} strategy: {e}")
                # Remove from allocations if initialization failed
                del self.strategy_allocations[strategy_type]
            except DataProviderError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_initialization_data_error",
                    strategy_type=strategy_type.value,
                    error_type=type(e).__name__,
                )
                logging.error(
                    f"Data provider error initializing {strategy_type.value} strategy: {e}"
                )
                # Remove from allocations if initialization failed
                del self.strategy_allocations[strategy_type]
            except Exception as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_initialization",
                    strategy_type=strategy_type.value,
                    error_type="unexpected_error",
                    original_error=type(e).__name__,
                )
                logging.error(f"Unexpected error initializing {strategy_type.value} strategy: {e}")
                # Remove from allocations if initialization failed
                del self.strategy_allocations[strategy_type]

        logging.info(
            f"MultiStrategyManager initialized with allocations: {self.strategy_allocations}"
        )

    def run_all_strategies(
        self,
    ) -> tuple[
        dict[StrategyType, dict[str, Any]], dict[str, float], dict[str, list[StrategyType]]
    ]:  # ⚠️ Phase 6 - Will migrate to StrategySignal after strategy engines updated
        """
        Run all enabled strategies and generate consolidated portfolio allocation

        Returns:
            Tuple of (strategy_signals, consolidated_portfolio, strategy_attribution)
        """

        strategy_signals: dict[StrategyType, dict[str, Any]] = (
            {}
        )  # ⚠️ Phase 6 - Will migrate to StrategySignal after strategy engines updated
        consolidated_portfolio: dict[str, float] = {}
        strategy_attribution: dict[str, list[StrategyType]] = {}

        # Step 1: Collect all required symbols from enabled strategies
        all_symbols = set()
        for _strategy_type, engine in self.strategy_engines.items():
            if hasattr(engine, "all_symbols"):
                all_symbols.update(engine.all_symbols)

        market_data = {}

        # Fetch data for all required symbols using shared data provider
        # Get data provider from first available engine
        shared_data_provider = None
        for engine in self.strategy_engines.values():
            if hasattr(engine, "data_provider"):
                shared_data_provider = engine.data_provider
                break

        if not shared_data_provider:
            raise RuntimeError("No data provider available from strategy engines")

        for symbol in all_symbols:
            data = shared_data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")

        # Market data fetched successfully
        logging.debug(
            f"Fetched market data for {len(market_data)} symbols using shared data provider"
        )

        # Step 2: Run each enabled strategy
        for strategy_type, engine in self.strategy_engines.items():
            try:
                logging.info(f"Executing {strategy_type.value} strategy...")

                if strategy_type == StrategyType.NUCLEAR:
                    indicators = engine.calculate_indicators(market_data)
                    result = engine.evaluate_nuclear_strategy(indicators, market_data)
                    strategy_signals[strategy_type] = {
                        "symbol": result[0],
                        "action": result[1],
                        "reason": result[2],
                        "indicators": indicators,
                        "market_data": market_data,
                    }
                    logging.debug(f"Nuclear strategy: {result[1]} {result[0]} - {result[2]}")

                elif strategy_type == StrategyType.TECL:
                    indicators = engine.calculate_indicators(market_data)
                    result = engine.evaluate_tecl_strategy(indicators, market_data)
                    strategy_signals[strategy_type] = {
                        "symbol": result[0],
                        "action": result[1],
                        "reason": result[2],
                        "indicators": indicators,
                        "market_data": market_data,
                    }
                    logging.debug(f"TECL strategy: {result[1]} {result[0]} - {result[2]}")

                elif strategy_type == StrategyType.KLM:
                    indicators = engine.calculate_indicators(market_data)
                    result = engine.evaluate_ensemble(indicators, market_data)

                    # Verify tuple has expected 4 elements to prevent IndexError
                    if len(result) < 4:
                        raise StrategyExecutionError(
                            f"KLM strategy returned incomplete result tuple: expected 4 elements, got {len(result)}",
                            strategy_name="KLM",
                        )

                    strategy_signals[strategy_type] = {
                        "symbol": result[0],  # symbol_or_allocation
                        "action": result[1],  # action
                        "reason": result[2],  # enhanced_reason
                        "variant_name": result[3],  # selected_variant_name
                        "indicators": indicators,
                        "market_data": market_data,
                    }
                    logging.info(f"KLM ensemble result: {result[1]} {result[0]} - {result[3]}")
                    logging.debug(
                        f"KLM ensemble: {result[1]} {result[0]} - {result[2]} [{result[3]}]"
                    )

            except StrategyExecutionError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_execution",
                    strategy_type=strategy_type.value,
                    error_type=type(e).__name__,
                )
                logging.error(f"Strategy execution error for {strategy_type.value}: {e}")
                strategy_signals[strategy_type] = {
                    "symbol": "BIL",  # Safe default
                    "action": ActionType.HOLD.value,
                    "reason": f"{strategy_type.value} strategy error: {e}",
                    "indicators": {},
                    "market_data": market_data,
                }
            except DataProviderError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_execution_data_error",
                    strategy_type=strategy_type.value,
                    error_type=type(e).__name__,
                )
                logging.error(f"Data provider error running {strategy_type.value} strategy: {e}")
                strategy_signals[strategy_type] = {
                    "symbol": "BIL",  # Safe default
                    "action": ActionType.HOLD.value,
                    "reason": f"{strategy_type.value} data error: {e}",
                    "indicators": {},
                    "market_data": {},
                }
            except Exception as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "strategy_execution",
                    strategy_type=strategy_type.value,
                    error_type="unexpected_error",
                    original_error=type(e).__name__,
                )
                logging.error(f"Unexpected error running {strategy_type.value} strategy: {e}")
                strategy_signals[strategy_type] = {
                    "symbol": "BIL",  # Safe default
                    "action": ActionType.HOLD.value,
                    "reason": f"{strategy_type.value} strategy error: {e}",
                    "indicators": {},
                    "market_data": {},
                }

        # Create consolidated portfolio allocation with strategy attribution
        logging.info(
            f"Creating consolidated portfolio from {len(strategy_signals)} strategy signals"
        )
        for strategy_type, signal_data in strategy_signals.items():
            logging.info(
                f"Processing {strategy_type.value} strategy: {signal_data['action']} {signal_data['symbol']}"
            )

            if signal_data["action"] == ActionType.BUY.value:
                # Skip strategies not in our allocation (e.g., KLM-only portfolio)
                if strategy_type not in self.strategy_allocations:
                    logging.warning(f"Strategy {strategy_type.value} not in allocations - skipping")
                    continue

                strategy_allocation = self.strategy_allocations[strategy_type]
                logging.info(f"{strategy_type.value} has {strategy_allocation:.1%} allocation")

                # Handle portfolio vs single symbol signals
                symbol_or_allocation = signal_data["symbol"]

                if isinstance(symbol_or_allocation, dict):
                    # Multi-asset allocation (e.g., from TECL strategy {'UVXY': 0.25, 'BIL': 0.75})
                    for symbol, weight in symbol_or_allocation.items():
                        total_weight = strategy_allocation * weight
                        if symbol in consolidated_portfolio:
                            consolidated_portfolio[symbol] += total_weight
                        else:
                            consolidated_portfolio[symbol] = total_weight

                        # Track strategy attribution
                        if symbol not in strategy_attribution:
                            strategy_attribution[symbol] = []
                        if strategy_type not in strategy_attribution[symbol]:
                            strategy_attribution[symbol].append(strategy_type)

                elif symbol_or_allocation in [
                    "NUCLEAR_PORTFOLIO",
                    "BEAR_PORTFOLIO",
                    "UVXY_BTAL_PORTFOLIO",
                ]:
                    # Named multi-asset portfolio signal - get actual allocations
                    if strategy_type == StrategyType.NUCLEAR:
                        portfolio = self._get_nuclear_portfolio_allocation(signal_data)
                    else:
                        portfolio = self._get_strategy_portfolio_allocation(
                            signal_data, strategy_type
                        )

                    for symbol, weight in portfolio.items():
                        total_weight = strategy_allocation * weight
                        if symbol in consolidated_portfolio:
                            consolidated_portfolio[symbol] += total_weight
                        else:
                            consolidated_portfolio[symbol] = total_weight

                        # Track strategy attribution
                        if symbol not in strategy_attribution:
                            strategy_attribution[symbol] = []
                        if strategy_type not in strategy_attribution[symbol]:
                            strategy_attribution[symbol].append(strategy_type)

                else:
                    # Single symbol signal
                    symbol = symbol_or_allocation
                    if symbol in consolidated_portfolio:
                        consolidated_portfolio[symbol] += strategy_allocation
                    else:
                        consolidated_portfolio[symbol] = strategy_allocation

                    # Track strategy attribution
                    if symbol not in strategy_attribution:
                        strategy_attribution[symbol] = []
                    if strategy_type not in strategy_attribution[symbol]:
                        strategy_attribution[symbol].append(strategy_type)

        # Note: Position tracking should only happen when trades are actually executed
        # Signal generation should not create position records

        logging.debug(f"Consolidated portfolio: {consolidated_portfolio}")
        logging.debug(f"Strategy attribution: {strategy_attribution}")
        return strategy_signals, consolidated_portfolio, strategy_attribution

    def _get_nuclear_portfolio_allocation(
        self, signal_data: dict[str, Any]
    ) -> dict[str, float]:  # TODO: Phase 6 - Migrate parameter to StrategySignal
        """Extract portfolio allocation from Nuclear strategy signal"""
        indicators = signal_data.get("indicators", {})
        market_data = signal_data.get("market_data", {})

        # Get the nuclear engine from our strategy engines
        nuclear_engine = self.strategy_engines.get(StrategyType.NUCLEAR)
        if not nuclear_engine:
            logging.error("Nuclear engine not available for portfolio allocation")
            return {"SPY": 1.0}  # Safe fallback

        if signal_data["symbol"] == "NUCLEAR_PORTFOLIO":
            # Bull market nuclear portfolio - extract actual weights from strategy engine
            portfolio = nuclear_engine.strategy.get_nuclear_portfolio(indicators, market_data)
            return {symbol: data["weight"] for symbol, data in portfolio.items()}

        elif signal_data["symbol"] == "BEAR_PORTFOLIO":
            # Bear market portfolio - extract from the combination logic using inverse volatility
            try:
                # Get the two bear subgroup signals
                bear1_signal = nuclear_engine.strategy.bear_subgroup_1(indicators)
                bear2_signal = nuclear_engine.strategy.bear_subgroup_2(indicators)
                bear1_symbol = bear1_signal[0]
                bear2_symbol = bear2_signal[0]

                # If both strategies recommend the same symbol, use 100% allocation
                if bear1_symbol == bear2_symbol:
                    return {bear1_symbol: 1.0}

                # Otherwise, use inverse volatility weighting to combine them
                try:
                    bear_portfolio = (
                        nuclear_engine.strategy.combine_bear_strategies_with_inverse_volatility(
                            bear1_symbol, bear2_symbol, indicators
                        )
                    )
                    return {symbol: data["weight"] for symbol, data in bear_portfolio.items()}

                except StrategyExecutionError as e:
                    from the_alchemiser.core.error_handler import TradingSystemErrorHandler

                    error_handler = TradingSystemErrorHandler()

                    # Log the error with proper categorization
                    error_handler.handle_error(
                        error=e,
                        component="nuclear_strategy",
                        context="bear_portfolio_volatility_calculation",
                        additional_data={
                            "bear1_symbol": bear1_symbol,
                            "bear2_symbol": bear2_symbol,
                            "fallback_action": "equal_weight_allocation",
                        },
                    )

                    # Use conservative fallback allocation
                    logging.warning(
                        f"Bear portfolio volatility calculation failed (strategy error): {e}, using conservative fallback"
                    )
                    return {bear1_symbol: 0.6, bear2_symbol: 0.4}
                except DataProviderError as e:
                    from the_alchemiser.core.error_handler import TradingSystemErrorHandler

                    error_handler = TradingSystemErrorHandler()

                    # Log the error with proper categorization
                    error_handler.handle_error(
                        error=e,
                        component="nuclear_strategy",
                        context="bear_portfolio_data_error",
                        additional_data={
                            "bear1_symbol": bear1_symbol,
                            "bear2_symbol": bear2_symbol,
                            "fallback_action": "equal_weight_allocation",
                        },
                    )

                    # Use conservative fallback allocation
                    logging.warning(f"Bear portfolio data error: {e}, using conservative fallback")
                    return {bear1_symbol: 0.6, bear2_symbol: 0.4}
                except Exception as e:
                    from the_alchemiser.core.error_handler import TradingSystemErrorHandler

                    error_handler = TradingSystemErrorHandler()

                    # Log the error with proper categorization
                    error_handler.handle_error(
                        error=e,
                        component="nuclear_strategy",
                        context="bear_portfolio_allocation",
                        additional_data={
                            "bear1_symbol": bear1_symbol,
                            "bear2_symbol": bear2_symbol,
                            "fallback_action": "equal_weight_allocation",
                        },
                    )

                    # Use conservative fallback allocation
                    logging.warning(
                        f"Bear portfolio volatility calculation failed: {e}, using conservative fallback"
                    )
                    return {bear1_symbol: 0.6, bear2_symbol: 0.4}

            except StrategyExecutionError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "bear_portfolio_allocation",
                    function="get_nuclear_portfolio_allocation",
                    error_type=type(e).__name__,
                )
                logging.error(f"Strategy execution error in bear portfolio allocation: {e}")
                # Safe fallback - single defensive position
                return {"SQQQ": 1.0}
            except DataProviderError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "bear_portfolio_data_error",
                    function="get_nuclear_portfolio_allocation",
                    error_type=type(e).__name__,
                )
                logging.error(f"Data provider error in bear portfolio allocation: {e}")
                # Safe fallback - single defensive position
                return {"SQQQ": 1.0}
            except Exception as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "bear_portfolio_allocation",
                    function="get_nuclear_portfolio_allocation",
                    error_type="unexpected_error",
                    original_error=type(e).__name__,
                )
                logging.error(f"Unexpected error calculating bear portfolio allocation: {e}")
                # Safe fallback - single defensive position
                return {"SQQQ": 1.0}

        elif signal_data["symbol"] == "UVXY_BTAL_PORTFOLIO":
            # Volatility hedge portfolio - these are the standard weights used by the strategy
            # This could be enhanced to be dynamic based on market conditions if needed
            return {"UVXY": 0.75, "BTAL": 0.25}

        return {}

    def _get_strategy_portfolio_allocation(
        self, signal_data: dict[str, Any], strategy_type: StrategyType
    ) -> dict[str, float]:
        """Extract portfolio allocation from any strategy signal"""
        if strategy_type == StrategyType.TECL:
            # Handle both single symbol and multi-asset allocations from TECL strategy
            symbol_or_allocation = signal_data["symbol"]

            if isinstance(symbol_or_allocation, dict):
                # Multi-asset allocation (e.g., {'UVXY': 0.25, 'BIL': 0.75})
                return symbol_or_allocation
            else:
                # Single symbol allocation
                return {symbol_or_allocation: 1.0}

        return {}

    def _update_position_tracking(
        self, strategy_signals: dict[StrategyType, Any], consolidated_portfolio: dict[str, float]
    ) -> None:
        """
        Update position tracking with current strategy positions

        WARNING: This method should ONLY be called when trades are actually executed,
        not during signal generation. Signal generation should not create position records.
        Position tracking should be handled by the StrategyOrderTracker in the execution layer.
        """
        logging.warning(
            "_update_position_tracking called - this should only happen during trade execution"
        )
        try:
            new_positions: dict[StrategyType, list[Any]] = {
                strategy: [] for strategy in StrategyType
            }

            for strategy_type, signal_data in strategy_signals.items():
                if signal_data["action"] == ActionType.BUY.value:
                    strategy_allocation = self.strategy_allocations[strategy_type]

                    # Create position record for each symbol this strategy wants to hold
                    for symbol, total_weight in consolidated_portfolio.items():
                        # Calculate this strategy's contribution to this position
                        strategy_weight = (
                            total_weight / strategy_allocation if strategy_allocation > 0 else 0
                        )

                        # Only record if this strategy actually contributed to this position
                        if strategy_weight > 0.001:  # Minimum threshold
                            position = StrategyPosition(
                                strategy_type=strategy_type,
                                symbol=symbol,
                                allocation=strategy_weight,
                                reason=signal_data["reason"],
                                timestamp=datetime.now(),
                            )
                            new_positions[strategy_type].append(position)

            # Position tracking between runs is disabled
            logging.debug("Position tracking disabled - not saving positions")

        except StrategyExecutionError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "position_tracking_update",
                function="_update_position_tracking",
                error_type=type(e).__name__,
            )
            logging.error(f"Strategy execution error updating position tracking: {e}")
        except (AttributeError, KeyError) as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "position_tracking_data_error",
                function="_update_position_tracking",
                error_type=type(e).__name__,
            )
            logging.error(f"Data structure error updating position tracking: {e}")
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "position_tracking_update",
                function="_update_position_tracking",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error updating position tracking: {e}")

    def get_strategy_performance_summary(
        self,
    ) -> dict[str, Any]:  # TODO: Phase 6 - Migrate to StrategyPnLSummary
        """Get a summary of each strategy's recent performance and current positions"""
        # Position tracking between runs is disabled
        positions: dict[StrategyType, list[Any]] = {
            strategy: [] for strategy in StrategyType
        }  # TODO: Phase 6 - Migrate to list[StrategyPositionData]

        summary: dict[str, Any] = {  # TODO: Phase 6 - Migrate to StrategyPnLSummary
            "timestamp": datetime.now().isoformat(),
            "strategy_allocations": {k.value: v for k, v in self.strategy_allocations.items()},
            "strategies": {},
        }

        for strategy_type, position_list in positions.items():
            strategy_summary = {
                "allocation": self.strategy_allocations[strategy_type],
                "current_positions": len(position_list),
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "allocation": pos.allocation,
                        "reason": pos.reason,
                        "age_hours": (datetime.now() - pos.timestamp).total_seconds() / 3600,
                    }
                    for pos in position_list
                ],
            }
            summary["strategies"][strategy_type.value] = strategy_summary

        return summary


def main() -> None:
    """Test the multi-strategy manager"""
    import pprint

    # Create manager with 50/50 allocation
    manager = MultiStrategyManager({StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5})

    print("🚀 Running Multi-Strategy Analysis")
    print("=" * 50)

    # Run all strategies
    strategy_signals, consolidated_portfolio, _ = manager.run_all_strategies()

    print("\n📊 Strategy Signals:")
    for strategy, signal in strategy_signals.items():
        print(f"  {strategy.value}: {signal['action']} {signal['symbol']} - {signal['reason']}")

    print("\n🎯 Consolidated Portfolio:")
    for symbol, weight in consolidated_portfolio.items():
        print(f"  {symbol}: {weight:.1%}")

    print("\n📈 Strategy Performance Summary:")
    summary = manager.get_strategy_performance_summary()
    pprint.pprint(summary)


if __name__ == "__main__":
    main()
