#!/usr/bin/env python3
"""Trading Engine for The Alchemiser.

Unified multi-strategy trading engine for Alpaca, supporting portfolio rebalancing,
strategy execution, reporting, and dashboard integration.

This is the main orchestrator that coordinates signal generation, execution, and reporting
across multiple trading strategies with comprehensive position management.

Example:
    Initialize and run multi-strategy trading:

    >>> engine = TradingEngine(paper_trading=True)
    >>> result = engine.execute_multi_strategy()
    >>> # Display handled by CLI layer

    DI Example:
    >>> container = ApplicationContainer.create_for_testing()
    >>> engine = TradingEngine.create_with_di(container=container)
    >>> result = engine.execute_multi_strategy()
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # Import for type checking only to avoid runtime dependency
    from the_alchemiser.application.mapping.strategies import StrategySignalDisplayDTO

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.smart_execution import SmartExecution
from the_alchemiser.application.mapping.execution_summary_mapping import (
    safe_dict_to_execution_summary_dto,
    safe_dict_to_portfolio_state_dto,
)
from the_alchemiser.application.mapping.strategies import (
    StrategySignalDisplayDTO,
)
from the_alchemiser.application.portfolio.services.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.application.trading.account_facade import AccountFacade
from the_alchemiser.application.trading.alpaca_client import AlpacaClient
from the_alchemiser.application.trading.bootstrap import (
    TradingBootstrapContext,
    bootstrap_from_container,
    bootstrap_from_service_manager,
    bootstrap_traditional,
)

# Import application-layer ports for dependency injection
from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager
from the_alchemiser.domain.types import (
    AccountInfo,
    EnrichedAccountInfo,
    OrderDetails,
    PositionsDict,
)
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.interfaces.schemas.execution import ExecutionResultDTO
from the_alchemiser.services.account.account_service import (
    AccountService as TypedAccountService,
)
from the_alchemiser.services.errors.context import create_error_context
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

from ..execution.execution_manager import ExecutionManager
from ..reporting.reporting import build_portfolio_state_data


class StrategyManagerAdapter:
    """Typed-backed adapter to provide run_all_strategies for callers.

    This adapter now uses pure mapping functions from application/mapping/strategies.py
    to convert typed signals to legacy format, removing ad-hoc dict transformations
    from the runtime path.
    """

    def __init__(
        self,
        market_data_port: Any,
        strategy_allocations: dict[StrategyType, float],
    ) -> None:
        self._typed = TypedStrategyManager(
            market_data_port=market_data_port,
            strategy_allocations=strategy_allocations,
        )

    def run_all_strategies(
        self,
    ) -> tuple[
        dict[StrategyType, "StrategySignalDisplayDTO"],
        dict[str, float],
        dict[str, list[StrategyType]],
    ]:
        """Execute all strategies and return results in legacy format.

        This method now delegates to pure mapping functions to convert typed signals
        to legacy format, ensuring no ad-hoc dict transformations in the runtime path.

        Returns:
            Tuple containing legacy signals dict, consolidated portfolio, and strategy attribution
        """
        from datetime import UTC, datetime

        from the_alchemiser.application.mapping.strategies import run_all_strategies_mapping

        # Generate typed signals from strategy manager
        aggregated = self._typed.generate_all_signals(datetime.now(UTC))

        # Use pure mapping function to convert to legacy format
        return run_all_strategies_mapping(aggregated, self._typed.strategy_allocations)

    # Expose strategy_allocations for reporting usage
    @property
    def strategy_allocations(self) -> dict[StrategyType, float]:
        return self._typed.strategy_allocations

    # Minimal performance summary placeholder for typed manager
    def get_strategy_performance_summary(self) -> dict[str, Any]:
        try:
            # If typed manager exposes a similar method, delegate
            from typing import cast

            return cast(dict[str, Any], self._typed.get_strategy_performance_summary())  # type: ignore[attr-defined]
        except AttributeError:
            # Strategy manager doesn't have performance summary method - return default structure
            return {
                st.name: {"pnl": 0.0, "trades": 0} for st in self._typed.strategy_allocations.keys()
            }
        except Exception as e:
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="get_strategy_performance_summary",
                component="StrategyManagerAdapter.get_strategy_performance_summary",
                function_name="get_strategy_performance_summary",
            )
            error_handler.handle_error_with_context(error=e, context=context, should_continue=False)
            raise StrategyExecutionError(
                f"Failed to retrieve strategy performance summary: {e}",
                strategy_name="TypedStrategyManager",
            ) from e


# Protocol definitions for dependency injection
class AccountInfoProvider(Protocol):
    """Protocol for account information retrieval."""

    def get_account_info(
        self,
    ) -> AccountInfo:  # Phase 17: Migrated from dict[str, Any] to AccountInfo
        """Get comprehensive account information."""
        ...


def _create_default_account_info(account_id: str = "unknown") -> AccountInfo:
    """Create a default AccountInfo structure for error cases."""
    return {
        "account_id": account_id,
        "equity": 0.0,
        "cash": 0.0,
        "buying_power": 0.0,
        "day_trades_remaining": 0,
        "portfolio_value": 0.0,
        "last_equity": 0.0,
        "daytrading_buying_power": 0.0,
        "regt_buying_power": 0.0,
        "status": "INACTIVE",
    }


class PositionProvider(Protocol):
    """Protocol for position data retrieval."""

    def get_positions_dict(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, dict[str, Any]] to PositionsDict
        """Get current positions keyed by symbol."""
        ...


class PriceProvider(Protocol):
    """Protocol for current price data retrieval."""

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a single symbol."""
        ...

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols."""
        ...


class RebalancingService(Protocol):
    """Protocol for portfolio rebalancing operations."""

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:  # Phase 18: Migrated from list[dict[str, Any]] to list[OrderDetails]
        """Rebalance portfolio to target allocation."""
        ...


class MultiStrategyExecutor(Protocol):
    """Protocol for multi-strategy execution."""

    def execute_multi_strategy(self) -> MultiStrategyExecutionResultDTO:
        """Execute all strategies and rebalance portfolio."""
        ...


class TradingEngine:
    """Unified multi-strategy trading engine for Alpaca.

    Coordinates signal generation, order execution, portfolio rebalancing, and reporting
    across multiple trading strategies. Supports both paper and live trading with
    comprehensive position management and performance tracking.

    Attributes:
        config: Configuration object containing trading parameters.
        paper_trading (bool): Whether using paper trading account.
        ignore_market_hours (bool): Whether to trade outside market hours.
        data_provider: Unified data provider for market data and account info.
        trading_client: Alpaca trading client for order execution.
        order_manager: Smart execution engine for order placement.
        portfolio_rebalancer: Portfolio rebalancing workflow manager.
        strategy_manager: Multi-strategy signal generation manager.
    """

    def __init__(
        self,
        bootstrap_context: TradingBootstrapContext | None = None,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
        # Backward compatibility parameters (deprecated)
        paper_trading: bool = True,
        config: Settings | None = None,
        trading_service_manager: Any = None,
        container: Any = None,
    ) -> None:
        """Initialize the TradingEngine with bootstrap context or legacy parameters.

        Args:
            bootstrap_context: Pre-configured dependency context (preferred)
            strategy_allocations: Portfolio allocation between strategies
            ignore_market_hours: Whether to ignore market hours when placing orders
            paper_trading: (Deprecated) Whether to use paper trading
            config: (Deprecated) Configuration object
            trading_service_manager: (Deprecated) Injected TradingServiceManager
            container: (Deprecated) DI container

        Note:
            New code should use bootstrap_context. Legacy parameters maintained
            for backward compatibility but emit deprecation warnings.
        """
        self.logger = logging.getLogger(__name__)

        # Type annotations for attributes that can have multiple types
        self.portfolio_rebalancer: Any  # PortfolioManagementFacade instance

        # Determine initialization mode
        if bootstrap_context is not None:
            # Modern bootstrap mode - preferred
            self._init_from_context(bootstrap_context, strategy_allocations, ignore_market_hours)
        elif container is not None:
            # Legacy Full DI mode - deprecated
            import warnings

            warnings.warn(
                "Direct container parameter is deprecated. "
                "Use bootstrap_from_container() and pass result as bootstrap_context.",
                DeprecationWarning,
                stacklevel=2,
            )
            context = bootstrap_from_container(container)
            self._init_from_context(context, strategy_allocations, ignore_market_hours)
        elif trading_service_manager is not None:
            # Legacy Partial DI mode - deprecated
            import warnings

            warnings.warn(
                "Direct trading_service_manager parameter is deprecated. "
                "Use bootstrap_from_service_manager() and pass result as bootstrap_context.",
                DeprecationWarning,
                stacklevel=2,
            )
            context = bootstrap_from_service_manager(trading_service_manager)
            self._init_from_context(context, strategy_allocations, ignore_market_hours)
        else:
            # Legacy Traditional mode - deprecated
            import warnings

            warnings.warn(
                "Direct TradingEngine() instantiation is deprecated. "
                "Use bootstrap_traditional() and pass result as bootstrap_context.",
                DeprecationWarning,
                stacklevel=2,
            )
            context = bootstrap_traditional(paper_trading, config)
            self._init_from_context(context, strategy_allocations, ignore_market_hours)

    def _init_from_context(
        self,
        context: TradingBootstrapContext,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool,
    ) -> None:
        """Initialize TradingEngine from bootstrap context.

        This is the main initialization path that uses a pre-configured
        dependency context from the bootstrap module.
        """
        # Extract dependencies from context
        self.account_service = context["account_service"]
        self._market_data_port = context["market_data_port"]
        self.data_provider = context["data_provider"]  # DataFrame-compatible adapter
        self._alpaca_manager = context["alpaca_manager"]
        self.trading_client = context["trading_client"]
        self._trading_service_manager = context["trading_service_manager"]
        self.paper_trading = context["paper_trading"]
        self.ignore_market_hours = ignore_market_hours

        # Set container to None since we're not using DI container directly
        self._container = None

        # Initialize common components
        self._init_common_components(strategy_allocations, context["config_dict"])

    def _init_common_components(
        self, strategy_allocations: dict[StrategyType, float] | None, config_dict: dict[str, Any]
    ) -> None:
        """Initialize components common to all initialization modes."""
        # Strategy allocations
        self.strategy_allocations = strategy_allocations or {
            StrategyType.NUCLEAR: 1.0 / 3.0,
            StrategyType.TECL: 1.0 / 3.0,
            StrategyType.KLM: 1.0 / 3.0,
        }

        # Order manager setup

        try:
            # Build an AlpacaClient once using the same authenticated trading client
            alpaca_manager: AlpacaManager
            if (
                hasattr(self, "_trading_service_manager")
                and self._trading_service_manager is not None
                and hasattr(self._trading_service_manager, "alpaca_manager")
            ):
                alpaca_manager = self._trading_service_manager.alpaca_manager
            elif hasattr(self, "_alpaca_manager"):
                alpaca_manager = self._alpaca_manager
            else:
                raise TradingClientError(
                    "TradingEngine missing AlpacaManager; initialize with DI or credentials"
                )

            alpaca_client = AlpacaClient(alpaca_manager, self.data_provider)
            self.order_manager = SmartExecution(
                order_executor=alpaca_client,
                data_provider=self.data_provider,
                ignore_market_hours=self.ignore_market_hours,
                config=config_dict,
            )
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize smart execution: {e}",
                context={"trading_client_type": type(self.trading_client).__name__},
            ) from e

        # Portfolio rebalancer and orchestrator
        try:
            # Require TradingServiceManager for portfolio operations
            trading_manager = getattr(self, "_trading_service_manager", None)
            if trading_manager is not None and hasattr(trading_manager, "alpaca_manager"):
                # Use modern portfolio management facade
                self.portfolio_rebalancer = PortfolioManagementFacade(
                    trading_manager=trading_manager,
                )
                # Initialize rebalancing orchestrator for sequential SELL→settle→BUY execution
                from the_alchemiser.application.portfolio.rebalancing_orchestrator import (
                    RebalancingOrchestrator,
                )

                self._rebalancing_orchestrator = RebalancingOrchestrator(
                    portfolio_facade=self.portfolio_rebalancer,
                    trading_client=self.trading_client,
                    paper_trading=self.paper_trading,
                    account_info_provider=self,  # Pass self to access get_account_info method
                )
            else:
                # No legacy fallbacks - fail fast and require proper DI setup
                raise ConfigurationError(
                    "TradingServiceManager is required for portfolio operations. "
                    "Please use TradingEngine factory methods or provide trading_service_manager parameter."
                )
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize portfolio rebalancer: {e}",
                context={"engine_type": type(self).__name__},
            ) from e

        # Strategy manager - use TypedStrategyManager directly (V2 migration)
        try:
            market_data_port = getattr(self, "_market_data_port", None)
            if market_data_port is None:
                raise ConfigurationError(
                    "Market data service unavailable for strategy manager initialization"
                )
            self.typed_strategy_manager = TypedStrategyManager(
                market_data_port=market_data_port,
                strategy_allocations=self.strategy_allocations,
            )
            # Provide compatibility property for CLI
            self.strategy_manager = self._create_strategy_manager_bridge()
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize strategy manager: {e}",
                context={
                    "initialization_mode": "DI",
                    "container_available": self._container is not None,
                },
            ) from e

        # Supporting services for composition-based access
        try:
            # Preserve DI-provided account_service if already set; otherwise wire the
            # typed AccountService to the AlpacaManager so it can supply both
            # account info and positions (MarketDataService lacks these).
            if not hasattr(self, "account_service") or self.account_service is None:
                # Reuse the AlpacaManager resolved earlier in this method
                self.account_service = TypedAccountService(alpaca_manager)

            # Initialize AccountFacade to coordinate account operations
            market_data_service = getattr(self, "_market_data_port", None)
            position_service = None  # Could be added later if needed
            self._account_facade = AccountFacade(
                account_service=self.account_service,
                market_data_service=market_data_service,
                position_service=position_service,
            )

            self.execution_manager = ExecutionManager(self)
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize account service or execution manager: {e}",
                context={
                    "initialization_mode": "DI",
                    "data_provider_type": type(self.data_provider).__name__,
                },
            ) from e

        # Compose dependencies for type-safe delegation
        self._account_info_provider: AccountInfoProvider = self._account_facade
        self._position_provider: PositionProvider = self._account_facade
        self._price_provider: PriceProvider = self._account_facade
        self._rebalancing_service: RebalancingService = self.portfolio_rebalancer
        self._multi_strategy_executor: MultiStrategyExecutor = self.execution_manager

        # Logging setup
        logging.info(f"TradingEngine initialized - Paper Trading: {self.paper_trading}")

    def _create_strategy_manager_bridge(self) -> Any:
        """Create a bridge object that provides run_all_strategies() interface for CLI compatibility."""

        class StrategyManagerBridge:
            def __init__(self, typed_manager: TypedStrategyManager):
                self._typed = typed_manager

            def run_all_strategies(
                self,
            ) -> tuple[
                dict[StrategyType, "StrategySignalDisplayDTO"],
                dict[str, float],
                dict[str, list[StrategyType]],
            ]:
                """Bridge method that converts typed signals to legacy format for CLI compatibility."""
                from datetime import UTC, datetime

                from the_alchemiser.application.mapping.strategies import run_all_strategies_mapping

                # Generate typed signals
                aggregated = self._typed.generate_all_signals(datetime.now(UTC))

                # Use pure mapping function to convert to legacy format
                return run_all_strategies_mapping(aggregated, self._typed.strategy_allocations)

            @property
            def strategy_allocations(self) -> dict[StrategyType, float]:
                return self._typed.strategy_allocations

            def get_strategy_performance_summary(self) -> dict[str, Any]:
                # Minimal implementation for compatibility
                return {
                    st.name: {"pnl": 0.0, "trades": 0}
                    for st in self._typed.strategy_allocations.keys()
                }

        return StrategyManagerBridge(self.typed_strategy_manager)

    # --- Account and Position Methods ---
    def get_account_info(self) -> AccountInfo:
        """Get basic typed account information for execution flows.

        Returns typed AccountInfo as required by MultiStrategyExecutionResultDTO.
        Use get_enriched_account_info for UI/reporting extras.

        Delegates to AccountFacade for normalized account information.
        """
        return self._account_facade.get_account_info()

    def get_enriched_account_info(self) -> EnrichedAccountInfo:
        """Get enriched account information including portfolio history and P&L data.

        This extends the basic AccountInfo with portfolio performance data suitable for
        display and reporting purposes.

        Delegates to AccountFacade for coordinated enriched account information.

        Returns:
            EnrichedAccountInfo with portfolio history and closed P&L data.
        """
        enriched = self._account_facade.get_enriched_account_info(paper_trading=self.paper_trading)
        # Update market_hours_ignored flag based on engine setting
        enriched["market_hours_ignored"] = self.ignore_market_hours
        return enriched

    def get_positions(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, Any] to PositionsDict
        """Get current positions via account facade delegation.

        Returns:
            Dict of current positions keyed by symbol with validated PositionInfo structure.
        """
        return self._account_facade.get_positions()

    def get_positions_dict(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, dict[str, Any]] to PositionsDict
        """Get current positions as dictionary keyed by symbol.

        This is an alias for get_positions() to maintain backward compatibility.

        Returns:
            Dict of current positions keyed by symbol with validated PositionInfo structure.
        """
        return self._account_facade.get_positions_dict()

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol via account facade delegation.

        Args:
            symbol: Stock symbol to get price for.

        Returns:
            Current price as float, or 0.0 if price unavailable.
        """
        return self._account_facade.get_current_price(symbol)

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols via account facade delegation.

        Args:
            symbols: List of stock symbols to get prices for.

        Returns:
            Dict mapping symbols to current prices, excluding symbols with invalid prices.
        """
        return self._account_facade.get_current_prices(symbols)

    # --- Order and Rebalancing Methods ---
    def wait_for_settlement(
        self, sell_orders: list[OrderDetails], max_wait_time: int = 60, poll_interval: float = 2.0
    ) -> bool:
        """Wait for sell orders to settle by polling their status.

        Args:
            sell_orders: List of sell order dictionaries with order_id keys.
            max_wait_time: Maximum time to wait in seconds. Defaults to 60.
            poll_interval: Polling interval in seconds. Defaults to 2.0.

        Returns:
            True if all orders settled successfully, False otherwise.
        """
        # Temporary conversion for legacy order_manager compatibility
        legacy_orders = []
        for order in sell_orders:
            legacy_order = dict(order)
            # Ensure compatibility by including both id and order_id keys
            if "id" in legacy_order and "order_id" not in legacy_order:
                legacy_order["order_id"] = legacy_order["id"]
            legacy_orders.append(legacy_order)
        return self.order_manager.wait_for_settlement(legacy_orders, max_wait_time, poll_interval)

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
    ) -> str | None:
        """Place a limit or market order using the smart execution engine.

        Args:
            symbol: Stock symbol to trade.
            qty: Quantity to trade.
            side: Order side (BUY or SELL).
            max_retries: Maximum number of retry attempts. Defaults to 3.
            poll_timeout: Timeout for order polling in seconds. Defaults to 30.
            poll_interval: Polling interval in seconds. Defaults to 2.0.
            slippage_bps: Maximum slippage in basis points. Defaults to None.

        Returns:
            Order ID if successful, None if failed.
        """
        return self.order_manager.place_order(
            symbol, qty, side, max_retries, poll_timeout, poll_interval, slippage_bps
        )

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:  # Phase 18: Migrated from list[dict[str, Any]] to list[OrderDetails]
        """Rebalance portfolio to target allocation with sequential execution to prevent buying power issues.

        Delegates to RebalancingOrchestrator for sequential SELL→settle→BUY execution
        to prevent buying power issues.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages.
            strategy_attribution: Dictionary mapping symbols to contributing strategies.

        Returns:
            List of executed orders during rebalancing as OrderDetails.
        """
        # Delegate to the rebalancing orchestrator for sequential execution
        return self._rebalancing_orchestrator.execute_full_rebalance_cycle(
            target_portfolio, strategy_attribution
        )

    def execute_rebalancing(
        self, target_allocations: dict[str, float], mode: str = "market"
    ) -> ExecutionResultDTO:
        """
        Execute portfolio rebalancing with the specified mode.

        Args:
            target_allocations: Target allocation percentages by symbol
            mode: Rebalancing mode ('market', 'limit', 'paper') - currently unused but kept for compatibility

        Returns:
            ExecutionResultDTO with comprehensive execution details
        """
        # Get account info before execution
        account_info_before = self.get_account_info()

        # Execute rebalancing
        orders = self.rebalance_portfolio(target_allocations)

        # Get account info after execution
        account_info_after = self.get_account_info()

        # Build execution summary
        execution_summary = {
            "total_orders": len(orders),
            "orders_executed": orders,
            "success_rate": 1.0 if orders else 0.0,
            "mode": mode,
        }

        # Build final portfolio state
        current_positions = self.get_positions()
        final_portfolio_state = self._build_portfolio_state_data(
            target_allocations, account_info_after, current_positions
        )

        return ExecutionResultDTO(
            orders_executed=orders,
            account_info_before=account_info_before,
            account_info_after=account_info_after,
            execution_summary=safe_dict_to_execution_summary_dto(execution_summary),
            final_portfolio_state=safe_dict_to_portfolio_state_dto(final_portfolio_state),
        )

    # --- Multi-Strategy Execution ---
    def execute_multi_strategy(self) -> MultiStrategyExecutionResultDTO:
        """Execute all strategies and rebalance portfolio with engine orchestration.

        Returns:
            MultiStrategyExecutionResultDTO with comprehensive execution details.
        """
        logging.info("Initiating multi-strategy execution")

        # Pre-execution validation
        try:
            self.get_account_info()
        except (DataProviderError, TradingClientError, ConfigurationError, ValueError) as e:
            logging.error(f"Pre-execution validation failed: {e}")
            return MultiStrategyExecutionResultDTO(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info("pre_validation_error"),
                account_info_after=_create_default_account_info("pre_validation_error"),
                execution_summary=safe_dict_to_execution_summary_dto(
                    {
                        "error": f"Pre-execution validation failed: {e}",
                        "mode": "error",
                        "account_info_before": _create_default_account_info("pre_validation_error"),
                        "account_info_after": _create_default_account_info("pre_validation_error"),
                    }
                ),
                final_portfolio_state=safe_dict_to_portfolio_state_dto({}),
            )

        try:
            # Use composed multi-strategy executor
            result = self._multi_strategy_executor.execute_multi_strategy()

            # Engine-level post-processing
            if result.success:
                logging.info("Multi-strategy execution completed successfully")

                # Engine execution completed successfully
                logging.info("Multi-strategy execution completed successfully")
                # Note: ExecutionSummaryDTO is immutable, so we can't add engine metadata here

            else:
                logging.warning("Multi-strategy execution completed with issues")

            return result

        except (
            StrategyExecutionError,
            TradingClientError,
            DataProviderError,
            ConfigurationError,
        ) as e:
            logging.error(f"Multi-strategy execution failed: {e}")

            # Enhanced error handling
            try:
                from the_alchemiser.services.errors import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="multi-strategy execution",
                    component="TradingEngine.execute_multi_strategy",
                    additional_data={
                        "paper_trading": self.paper_trading,
                        "ignore_market_hours": self.ignore_market_hours,
                    },
                )
            except (ImportError, AttributeError):
                pass  # Fallback for backward compatibility

            return MultiStrategyExecutionResultDTO(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info("execution_error"),
                account_info_after=_create_default_account_info("execution_error"),
                execution_summary=safe_dict_to_execution_summary_dto(
                    {
                        "error": f"Execution failed: {e}",
                        "mode": "error",
                        "account_info_before": _create_default_account_info("execution_error"),
                        "account_info_after": _create_default_account_info("execution_error"),
                    }
                ),
                final_portfolio_state=safe_dict_to_portfolio_state_dto({}),
            )

    # --- Reporting and Dashboard Methods ---
    def _archive_daily_strategy_pnl(self, pnl_summary: dict[str, Any]) -> None:  # noqa: ARG002
        """Archive daily strategy P&L for historical tracking."""
        try:
            from the_alchemiser.application.tracking.strategy_order_tracker import (
                get_strategy_tracker,
            )

            # Get current positions and prices
            current_positions = self.get_positions()
            symbols_in_portfolio = set(current_positions.keys())
            current_prices = self.get_current_prices(list(symbols_in_portfolio))

            # Archive the daily P&L snapshot
            tracker = get_strategy_tracker(paper_trading=self.paper_trading)
            tracker.archive_daily_pnl(current_prices)

            logging.info("Successfully archived daily strategy P&L snapshot")

        except (ImportError, AttributeError, ConnectionError, OSError) as e:
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="archive_daily_strategy_pnl",
                component="TradingEngine._archive_daily_strategy_pnl",
                function_name="_archive_daily_strategy_pnl",
                additional_data={"paper_trading": self.paper_trading},
            )
            error_handler.handle_error_with_context(
                error=e,
                context=context,
                should_continue=True,  # Non-critical archival failure
            )
            logging.error(f"Failed to archive daily strategy P&L: {e}")
            # This is not critical to trading execution, so we don't re-raise

    def get_multi_strategy_performance_report(
        self,
    ) -> dict[str, Any]:  # TODO: Change to StrategyPnLSummary once implementation updated
        """Generate comprehensive performance report for all strategies"""
        try:
            current_positions = self.get_positions()
            report = {
                "timestamp": datetime.now().isoformat(),
                "strategy_allocations": {
                    k.value: v for k, v in self.strategy_manager.strategy_allocations.items()
                },
                "current_positions": current_positions,
                "performance_summary": self.strategy_manager.get_strategy_performance_summary(),
            }
            return report
        except (
            StrategyExecutionError,
            DataProviderError,
            AttributeError,
            ValueError,
            RuntimeError,
        ) as e:
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="generate_multi_strategy_performance_report",
                component="TradingEngine.get_multi_strategy_performance_report",
                function_name="get_multi_strategy_performance_report",
            )
            error_handler.handle_error_with_context(error=e, context=context, should_continue=False)
            raise StrategyExecutionError(f"Failed to generate performance report: {e}") from e

    def _build_portfolio_state_data(
        self,
        target_portfolio: dict[str, float],
        account_info: AccountInfo,
        current_positions: PositionsDict,
    ) -> dict[str, Any]:
        """Build portfolio state data for reporting purposes."""
        return build_portfolio_state_data(target_portfolio, account_info, current_positions)

    def _trigger_post_trade_validation(
        self, strategy_signals: dict[StrategyType, Any], orders_executed: list[dict[str, Any]]
    ) -> None:
        """
        Trigger post-trade technical indicator validation for live trading.

        Enhanced with type safety validation for orders_executed.

        Args:
            strategy_signals: Strategy signals that led to trades
            orders_executed: List of executed orders (being migrated to typed structure)
        """
        try:
            # Enhanced order validation
            validated_symbols = set()
            invalid_orders = []

            # Validate each order and extract symbols
            for i, order in enumerate(orders_executed):
                symbol = order.get("symbol")
                if not symbol:
                    invalid_orders.append(f"Order {i}: Missing 'symbol' field")
                    continue

                if not isinstance(symbol, str):
                    invalid_orders.append(f"Order {i}: Symbol must be string, got {type(symbol)}")
                    continue

                validated_symbols.add(symbol.strip().upper())

            # Log validation issues
            if invalid_orders:
                logging.warning(f"⚠️ Order validation issues: {'; '.join(invalid_orders)}")

            if not validated_symbols:
                logging.warning(
                    "🔍 No valid symbols found in orders_executed for post-trade validation"
                )
                return

            # Rest of the original logic with validated symbols
            nuclear_symbols = []
            tecl_symbols = []

            for strategy_type, signal in strategy_signals.items():
                symbol = signal.get("symbol")
                if symbol and symbol != "NUCLEAR_PORTFOLIO" and symbol != "BEAR_PORTFOLIO":
                    if strategy_type == StrategyType.NUCLEAR:
                        nuclear_symbols.append(symbol)
                    elif strategy_type == StrategyType.TECL:
                        tecl_symbols.append(symbol)

            # Use validated symbols instead of unsafe extraction
            order_symbols = validated_symbols
            nuclear_strategy_symbols = [
                "SPY",
                "IOO",
                "TQQQ",
                "VTV",
                "XLF",
                "VOX",
                "UVXY",
                "BTAL",
                "QQQ",
                "SQQQ",
                "PSQ",
                "UPRO",
                "TLT",
                "IEF",
                "SMR",
                "BWXT",
                "LEU",
                "EXC",
                "NLR",
                "OKLO",
            ]
            tecl_strategy_symbols = ["XLK", "KMLM", "SPXL", "TECL", "BIL", "BSV", "UVXY", "SQQQ"]
            for symbol in order_symbols:
                if symbol in nuclear_strategy_symbols and symbol not in nuclear_symbols:
                    nuclear_symbols.append(symbol)
                elif symbol in tecl_strategy_symbols and symbol not in tecl_symbols:
                    tecl_symbols.append(symbol)
            nuclear_symbols = list(set(nuclear_symbols))[:5]
            tecl_symbols = list(set(tecl_symbols))[:5]
            if nuclear_symbols or tecl_symbols:
                logging.info(
                    f"🔍 Triggering post-trade validation for Nuclear: {nuclear_symbols}, TECL: {tecl_symbols}"
                )
            else:
                logging.info("🔍 No symbols to validate in post-trade validation")
        except (ValueError, AttributeError, KeyError, TypeError) as e:
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="post_trade_validation",
                component="TradingEngine._trigger_post_trade_validation",
                function_name="_trigger_post_trade_validation",
                additional_data={
                    "strategy_signals": {str(k): v for k, v in strategy_signals.items()},
                    "orders_executed_count": len(orders_executed),
                },
            )
            error_handler.handle_error_with_context(
                error=e,
                context=context,
                should_continue=True,  # Non-critical validation failure
            )
            logging.error(f"❌ Post-trade validation failed: {e}")
            # This is not critical to trading execution, so we don't re-raise

    def calculate_target_vs_current_allocations(
        self,
        target_portfolio: dict[str, float],
        account_info: AccountInfo | dict[str, Any],
        current_positions: dict[str, Any],
    ) -> tuple[dict[str, "Decimal"], dict[str, "Decimal"]]:  # Uses Decimal values
        """Pure calculation of target vs current allocations.

        Layering: remains in application layer; no interface/cli imports.
        """
        from the_alchemiser.application.trading.portfolio_calculations import (
            calculate_target_vs_current_allocations as _calc,
        )

        return _calc(target_portfolio, account_info, current_positions)

    @classmethod
    def create_with_di(
        cls,
        container: Any = None,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine with full DI (deprecated).

        Args:
            container: DI container for dependency injection
            strategy_allocations: Strategy allocation weights
            ignore_market_hours: Whether to ignore market hours

        Returns:
            TradingEngine instance with all dependencies injected

        Note:
            This method is deprecated. Use create_from_container() instead.
        """
        import warnings

        warnings.warn(
            "create_with_di() is deprecated. Use create_from_container() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.create_from_container(
            container=container,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours,
        )

    @classmethod
    def create_from_container(
        cls,
        container: Any,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine from DI container.

        Args:
            container: DI container for dependency injection
            strategy_allocations: Strategy allocation weights
            ignore_market_hours: Whether to ignore market hours

        Returns:
            TradingEngine instance with all dependencies injected
        """
        context = bootstrap_from_container(container)
        return cls(
            bootstrap_context=context,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours,
        )

    @classmethod
    def create_from_service_manager(
        cls,
        trading_service_manager: Any,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine from TradingServiceManager.

        Args:
            trading_service_manager: TradingServiceManager instance
            strategy_allocations: Strategy allocation weights
            ignore_market_hours: Whether to ignore market hours

        Returns:
            TradingEngine instance with all dependencies injected
        """
        context = bootstrap_from_service_manager(trading_service_manager)
        return cls(
            bootstrap_context=context,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours,
        )

    @classmethod
    def create_traditional(
        cls,
        paper_trading: bool = True,
        config: Settings | None = None,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine using traditional approach.

        Args:
            paper_trading: Whether to use paper trading
            config: Configuration settings
            strategy_allocations: Strategy allocation weights
            ignore_market_hours: Whether to ignore market hours

        Returns:
            TradingEngine instance with all dependencies initialized
        """
        context = bootstrap_traditional(paper_trading, config)
        return cls(
            bootstrap_context=context,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours,
        )


def main() -> None:
    """Test TradingEngine multi-strategy execution"""
    import logging

    logging.basicConfig(level=logging.WARNING)  # Reduced verbosity
    print("Trading Engine Test")
    print("─" * 50)

    # Use DI approach instead of deprecated traditional constructor
    try:
        from the_alchemiser.container.application_container import ApplicationContainer
        from the_alchemiser.main import TradingSystem

        # Initialize DI system
        TradingSystem()
        container = ApplicationContainer()

        trader = TradingEngine.create_from_container(
            container=container,
            strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
            ignore_market_hours=True,
        )
        trader.paper_trading = True
    except (ImportError, ConfigurationError, TradingClientError) as e:
        print(f"Failed to initialize with DI: {e}")
        print("Falling back to traditional method")
        trader = TradingEngine(
            paper_trading=True,
            strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
        )

    print("Executing multi-strategy...")
    result = trader.execute_multi_strategy()
    print(f"Execution result: success={result.success}")

    print("Getting performance report...")
    report = trader.get_multi_strategy_performance_report()
    if "error" not in report:
        print("Performance report generated successfully")
        print(f"   Current positions: {len(report['current_positions'])}")
        print(f"   Strategy tracking: {len(report['performance_summary'])}")
    else:
        print(f"Error generating report: {report['error']}")


if __name__ == "__main__":
    main()
