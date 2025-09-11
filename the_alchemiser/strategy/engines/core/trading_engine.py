#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Trading Engine for The Alchemiser.

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

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # Import for type checking only to avoid runtime dependency
    from the_alchemiser.strategy.schemas.strategies import StrategySignalDisplayDTO

from the_alchemiser.execution.brokers.account_service import (
    AccountService as TypedAccountService,
)
from the_alchemiser.execution.core.account_facade import AccountFacade
from the_alchemiser.execution.core.execution_schemas import ExecutionResultDTO
from the_alchemiser.execution.execution_protocols import MultiStrategyExecutor
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.execution.strategies.smart_execution import SmartExecution
from the_alchemiser.portfolio.core.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.config.bootstrap import (
    TradingBootstrapContext,
    bootstrap_from_container,
    bootstrap_from_service_manager,
    bootstrap_traditional,
)
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.logging.logging_utils import (
    get_logger,
    log_with_context,
)
from the_alchemiser.shared.mappers.execution_summary_mapping import (
    dict_to_execution_summary_dto,
    dict_to_portfolio_state_dto,
)
from the_alchemiser.shared.reporting.reporting import build_portfolio_state_data
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.shared.types.broker_enums import BrokerOrderSide
from the_alchemiser.shared.types.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.utils.context import create_error_context
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    EnrichedAccountInfo,
    OrderDetails,
    PositionsDict,
)
from the_alchemiser.strategy.managers.typed_strategy_manager import TypedStrategyManager

# Import application-layer ports for dependency injection
from the_alchemiser.strategy.registry.strategy_registry import StrategyType
from the_alchemiser.strategy.schemas.strategies import (
    StrategySignalDisplayDTO,
    run_all_strategies_mapping,
)

# --- Internal Application Protocols ---


class AccountInfoProvider(Protocol):
    """Protocol for account information retrieval."""

    def get_account_info(self) -> AccountInfo:
        """Get comprehensive account information."""
        ...


class PositionProvider(Protocol):
    """Protocol for position data retrieval."""

    def get_positions_dict(self) -> PositionsDict:
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
    ) -> list[OrderDetails]:
        """Rebalance portfolio to target allocation."""
        ...


# --- Utility Functions ---


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


# --- Main Trading Engine Class ---


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
        bootstrap_context: TradingBootstrapContext,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> None:
        """Initialize the TradingEngine with bootstrap context.

        Args:
            bootstrap_context: Pre-configured dependency context (required)
            strategy_allocations: Portfolio allocation between strategies
            ignore_market_hours: Whether to ignore market hours when placing orders

        Note:
            This constructor now requires bootstrap_context. Use bootstrap functions
            to create the context:
            - bootstrap_from_container()
            - bootstrap_from_service_manager()
            - bootstrap_traditional()

        """
        self.logger = logging.getLogger(__name__)

        # Type annotations for attributes that can have multiple types
        self.portfolio_rebalancer: Any  # PortfolioManagementFacade instance

        # Initialize from bootstrap context
        self._init_from_context(
            bootstrap_context, strategy_allocations, ignore_market_hours
        )

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
        self._init_common_components(strategy_allocations)

    def _init_common_components(
        self,
        strategy_allocations: dict[StrategyType, float] | None,
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
            # Use AlpacaManager directly with SmartExecution (Phase 3: consolidation completed)
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

            # Use AlpacaManager directly instead of AlpacaClient wrapper
            self.order_manager = SmartExecution(
                order_executor=alpaca_manager,
                data_provider=self.data_provider,
                ignore_market_hours=self.ignore_market_hours,
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
            if trading_manager is not None and hasattr(
                trading_manager, "alpaca_manager"
            ):
                # Use modern portfolio management facade
                self.portfolio_rebalancer = PortfolioManagementFacade(
                    trading_manager=trading_manager,
                )
                # Initialize rebalancing orchestrator facade for sequential SELL→settle→BUY execution
                from the_alchemiser.portfolio.core.rebalancing_orchestrator_facade import (
                    RebalancingOrchestratorFacade,
                )

                self._rebalancing_orchestrator = RebalancingOrchestratorFacade(
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

            self.execution_manager = self._trading_service_manager

            # Create proper ExecutionManager for multi-strategy coordination
            # The TradingServicesFacade is for focused execution tasks
            # Multi-strategy execution requires the dedicated ExecutionManager
            
            # NEW: Try execution_v2 first, fallback to legacy
            try:
                from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager as ExecutionManagerV2
                
                # Create execution_v2 manager with AlpacaManager
                self._execution_manager_v2 = ExecutionManagerV2(self._alpaca_manager)
                self.use_execution_v2 = True
                self.logger.info("✅ Using NEW execution_v2 module")
                
                # Set up execution adapter for legacy interface compatibility
                class ExecutionV2Adapter:
                    """Adapter to make execution_v2 compatible with legacy MultiStrategyExecutor interface."""
                    
                    def __init__(self, execution_manager_v2):
                        self.execution_manager_v2 = execution_manager_v2
                    
                    def execute_rebalance_plan(self, plan):
                        """Execute rebalance plan using execution_v2."""
                        result = self.execution_manager_v2.execute_rebalance_plan(plan)
                        
                        # Convert to legacy format for compatibility
                        return [{
                            "symbol": order.symbol,
                            "action": order.action,
                            "quantity": float(order.shares),
                            "order_id": order.order_id,
                            "success": order.success,
                            "error": order.error_message,
                        } for order in result.orders]
                    
                    def execute_multi_strategy(self, signals=None, portfolio=None, attribution=None):
                        """Legacy fallback method for compatibility."""
                        # This should not be called if we're using execution_v2 properly
                        raise NotImplementedError("Legacy execution not available with execution_v2")
                
                self._execution_manager_for_multi_strategy = ExecutionV2Adapter(self._execution_manager_v2)
                
            except ImportError as import_error:
                self.logger.warning(f"⚠️ execution_v2 not available ({import_error}), using legacy execution")
                self.use_execution_v2 = False
                
                # Fallback to legacy execution
                from the_alchemiser.execution.core.manager import ExecutionManager
                self._execution_manager_for_multi_strategy = ExecutionManager(self)
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
        # Use the proper ExecutionManager for multi-strategy execution
        self._multi_strategy_executor: MultiStrategyExecutor = (
            self._execution_manager_for_multi_strategy
        )

        # Logging setup
        logging.info(f"TradingEngine initialized - Paper Trading: {self.paper_trading}")

    def _create_strategy_manager_bridge(self) -> Any:
        """Create a bridge object that provides run_all_strategies() interface for CLI compatibility."""

        class StrategyManagerBridge:
            def __init__(self, typed_manager: TypedStrategyManager) -> None:
                self._typed = typed_manager

            def run_all_strategies(
                self,
            ) -> tuple[
                dict[StrategyType, StrategySignalDisplayDTO],
                dict[str, float],
                dict[str, list[StrategyType]],
            ]:
                """Bridge method that converts typed signals to CLI-compatible format for CLI compatibility."""
                # Generate typed signals
                aggregated = self._typed.generate_all_signals(datetime.now(UTC))

                # Use pure mapping function to convert to CLI-compatible format
                return run_all_strategies_mapping(
                    aggregated, self._typed.strategy_allocations
                )

            @property
            def strategy_allocations(self) -> dict[StrategyType, float]:
                return self._typed.strategy_allocations

            def get_strategy_performance_summary(self) -> dict[str, Any]:
                """Get strategy performance summary with consistent error handling."""
                try:
                    # If typed manager exposes a similar method, delegate
                    from typing import cast

                    return cast(dict[str, Any], self._typed.get_strategy_performance_summary())  # type: ignore[attr-defined]
                except AttributeError:
                    # Strategy manager doesn't have performance summary method - return default structure
                    return {
                        st.name: {"pnl": 0.0, "trades": 0}
                        for st in self._typed.strategy_allocations
                    }
                except Exception as e:
                    from the_alchemiser.shared.errors.error_handler import (
                        TradingSystemErrorHandler,
                    )
                    from the_alchemiser.shared.utils.context import (
                        create_error_context,
                    )

                    error_handler = TradingSystemErrorHandler()
                    context = create_error_context(
                        operation="get_strategy_performance_summary",
                        component="TradingEngine.StrategyManagerBridge.get_strategy_performance_summary",
                        function_name="get_strategy_performance_summary",
                    )
                    error_handler.handle_error_with_context(
                        error=e, context=context, should_continue=False
                    )
                    raise StrategyExecutionError(
                        f"Failed to retrieve strategy performance summary: {e}",
                        strategy_name="TypedStrategyManager",
                    ) from e

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
        enriched = self._account_facade.get_enriched_account_info(
            paper_trading=self.paper_trading
        )
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
    ) -> (
        PositionsDict
    ):  # Phase 18: Migrated from dict[str, dict[str, Any]] to PositionsDict
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
        self,
        sell_orders: list[OrderDetails],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """Wait for sell orders to settle by polling their status.

        Args:
            sell_orders: List of sell order dictionaries with order_id keys.
            max_wait_time: Maximum time to wait in seconds. Defaults to 60.
            poll_interval: Polling interval in seconds. Defaults to 2.0.

        Returns:
            True if all orders settled successfully, False otherwise.

        """
        # Convert OrderDetails to dict format for order_manager compatibility
        compatible_orders = []
        for order in sell_orders:
            compatible_order = dict(order)
            # Ensure compatibility by including both id and order_id keys
            if "id" in compatible_order and "order_id" not in compatible_order:
                compatible_order["order_id"] = compatible_order["id"]
            compatible_orders.append(compatible_order)
        return self.order_manager.wait_for_settlement(
            compatible_orders, max_wait_time, poll_interval
        )

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: BrokerOrderSide,  # BrokerOrderSide only; enforce broker abstraction
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
    ) -> str | None:
        """Place a limit or market order using the smart execution engine.

        Order placement consolidated: delegates to SmartExecution.place_order()
        which routes through CanonicalOrderExecutor for unified execution pathway.

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
    ) -> list[
        OrderDetails
    ]:  # Phase 18: Migrated from list[dict[str, Any]] to list[OrderDetails]
        """Rebalance portfolio to target allocation with sequential execution to prevent buying power issues.

        Delegates to RebalancingOrchestrator for sequential SELL→settle→BUY execution
        to prevent buying power issues.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages.
            strategy_attribution: Dictionary mapping symbols to contributing strategies.

        Returns:
            List of executed orders during rebalancing as OrderDetails.

        """
        # === ENHANCED LOGGING: TRADING ENGINE ENTRY POINT ===
        logging.info("=== TRADING ENGINE REBALANCE_PORTFOLIO ENTRY ===")
        logging.info(f"ENGINE TYPE: {type(self).__name__}")
        logging.info(f"RECEIVED_TARGET_PORTFOLIO_TYPE: {type(target_portfolio)}")
        logging.info(
            f"RECEIVED_TARGET_PORTFOLIO_COUNT: {len(target_portfolio) if target_portfolio else 0}"
        )
        logging.info(
            f"RECEIVED_STRATEGY_ATTRIBUTION_TYPE: {type(strategy_attribution)}"
        )

        # Data validation and detailed logging
        if not target_portfolio:
            logging.error(
                "❌ CRITICAL: Empty target_portfolio received by TradingEngine"
            )
            logging.error("❌ This indicates portfolio consolidation failed upstream")
            return []

        # Log received portfolio in detail
        logging.info("=== RECEIVED TARGET PORTFOLIO BREAKDOWN ===")
        total_allocation = sum(target_portfolio.values())
        logging.info(f"Total allocation received: {total_allocation:.4f}")

        for symbol, allocation in target_portfolio.items():
            if allocation > 0.001:  # Log meaningful allocations
                logging.info(
                    f"  RECEIVED: {symbol} = {allocation:.4f} ({allocation * 100:.2f}%)"
                )

        # Validate allocation integrity
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(
                f"⚠️ Portfolio allocation integrity check: total={total_allocation:.4f}, expected~1.0"
            )

        # Log orchestrator details
        logging.info(
            f"ORCHESTRATOR_TYPE: {type(self._rebalancing_orchestrator).__name__}"
        )
        logging.info(
            f"ORCHESTRATOR_EXISTS: {self._rebalancing_orchestrator is not None}"
        )

        # Get current account state for comparison
        try:
            account_info = self.get_account_info()
            current_positions = self.get_positions_dict()

            equity_raw = account_info.get("equity")
            if equity_raw is None:
                raise ValueError(
                    "Equity not available in account info. "
                    "Cannot determine portfolio value for rebalancing."
                )

            try:
                current_portfolio_value = float(equity_raw)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid equity format: {equity_raw}") from e

            logging.info("=== CURRENT ACCOUNT STATE FOR REBALANCING ===")
            logging.info(f"Current portfolio value: ${current_portfolio_value:,.2f}")
            logging.info(
                f"Current buying power: ${float(account_info.get('buying_power', 0)):,.2f}"
            )
            logging.info(f"Current positions count: {len(current_positions)}")

            # Calculate expected trades
            expected_trades = []
            for symbol, target_allocation in target_portfolio.items():
                target_value = target_allocation * current_portfolio_value
                position_info: dict[str, Any] = current_positions.get(symbol, {})
                current_value = (
                    float(position_info.get("market_value", 0))
                    if position_info
                    else 0.0
                )
                trade_amount = target_value - current_value

                if abs(trade_amount) > 1.0:  # Significant trade threshold
                    action = "BUY" if trade_amount > 0 else "SELL"
                    expected_trades.append(
                        {
                            "symbol": symbol,
                            "action": action,
                            "amount": abs(trade_amount),
                            "target_value": target_value,
                            "current_value": current_value,
                        }
                    )
                    logging.info(
                        f"  EXPECTED_TRADE: {action} {symbol} ${abs(trade_amount):,.2f}"
                    )

            logging.info(f"EXPECTED_TRADES_COUNT: {len(expected_trades)}")

        except Exception as e:
            logging.error(
                f"❌ CRITICAL: Cannot proceed with rebalancing - failed to get account state: {e}"
            )
            logging.error(
                "❌ Rebalancing requires current portfolio value for safe execution"
            )
            # Return empty list rather than proceeding with unknown portfolio state
            return []

        # === DATA TRANSFER POINT: TO ORCHESTRATOR ===
        logging.info("=== DATA TRANSFER: HANDING OFF TO REBALANCING ORCHESTRATOR ===")
        logging.info(
            f"HANDOFF_DATA_CHECKSUM: {len(target_portfolio)} symbols, total={sum(target_portfolio.values()):.4f}"
        )

        # === ENHANCED DATA TRANSFER VERIFICATION ===
        logging.info("=== CRITICAL DATA VERIFICATION BEFORE ORCHESTRATOR ===")

        # Verify the target_portfolio passed from ExecutionManager
        logging.info(f"TRADING_ENGINE_RECEIVED_TYPE: {type(target_portfolio)}")
        logging.info(
            f"TRADING_ENGINE_RECEIVED_COUNT: {len(target_portfolio) if target_portfolio else 0}"
        )

        if target_portfolio:
            # Create integrity checksum for cross-validation
            received_total = sum(target_portfolio.values())
            received_checksum = f"symbols:{len(target_portfolio)}_total:{received_total:.6f}_hash:{hash(frozenset(target_portfolio.items()))}"
            logging.info(f"TRADING_ENGINE_RECEIVED_CHECKSUM: {received_checksum}")

            # Verify data integrity matches expectations
            if abs(received_total - 1.0) > 0.05:
                logging.error(
                    f"❌ TRADING_ENGINE_DATA_INTEGRITY_FAILED: total={received_total:.6f}, expected~1.0"
                )
            else:
                logging.info(
                    f"✅ TRADING_ENGINE_DATA_INTEGRITY_PASSED: total={received_total:.6f}"
                )

            # Log each symbol allocation received
            logging.info("=== TRADING_ENGINE_RECEIVED_ALLOCATIONS ===")
            for symbol, allocation in target_portfolio.items():
                logging.info(
                    f"TRADING_ENGINE_RECEIVED: {symbol} = {allocation:.6f} ({allocation * 100:.2f}%)"
                )

            # Verify expected symbols are present - GENERAL CHECK FOR ANY SYMBOLS
            received_symbols = set(target_portfolio.keys())
            logging.info(f"RECEIVED_SYMBOLS_COUNT: {len(received_symbols)}")
            logging.info(f"RECEIVED_SYMBOLS: {received_symbols}")

            # Check for ANY meaningful allocations
            meaningful_allocations = {
                s: a for s, a in target_portfolio.items() if a > 0.001
            }
            if len(meaningful_allocations) == 0:
                logging.error("❌ CRITICAL: NO MEANINGFUL ALLOCATIONS FOR ANY SYMBOLS!")
                logging.error(
                    "❌ UNIVERSAL FAILURE: No symbols have allocations > 0.1%"
                )
            else:
                logging.info(
                    f"✅ MEANINGFUL_ALLOCATIONS_FOUND: {len(meaningful_allocations)} symbols"
                )

        else:
            logging.error("❌ CRITICAL: TRADING_ENGINE_RECEIVED_EMPTY_PORTFOLIO")
            logging.error(
                "❌ This confirms the data loss occurred upstream in ExecutionManager!"
            )

        # Enhanced orchestrator information
        logging.info(
            f"ORCHESTRATOR_TYPE_DETAIL: {type(self._rebalancing_orchestrator)}"
        )
        logging.info(
            f"ORCHESTRATOR_MODULE: {getattr(type(self._rebalancing_orchestrator), '__module__', 'unknown')}"
        )
        logging.info(
            f"ORCHESTRATOR_EXISTS: {self._rebalancing_orchestrator is not None}"
        )

        if hasattr(self._rebalancing_orchestrator, "portfolio_facade"):
            facade_type = type(
                getattr(self._rebalancing_orchestrator, "portfolio_facade", None)
            )
            logging.info(f"ORCHESTRATOR_FACADE_TYPE: {facade_type}")

        # Convert portfolio value to Decimal for orchestrator
        from decimal import Decimal

        portfolio_value_decimal = Decimal(str(current_portfolio_value))

        # Log the portfolio value being passed
        logging.info(f"PORTFOLIO_VALUE_BEING_PASSED: ${portfolio_value_decimal}")

        try:
            # Delegate to the rebalancing orchestrator for sequential execution
            # The RebalancingOrchestratorFacade provides a synchronous interface
            # Pass the correctly calculated portfolio value to avoid recalculation
            logging.info(
                f"PASSING_PORTFOLIO_VALUE_TO_ORCHESTRATOR: ${portfolio_value_decimal}"
            )

            orders_result: list[OrderDetails] = (
                self._rebalancing_orchestrator.execute_full_rebalance_cycle(
                    target_portfolio, strategy_attribution, portfolio_value_decimal
                )
            )

            # === EXECUTION RESULTS ANALYSIS ===
            logging.info("=== TRADING ENGINE EXECUTION RESULTS ===")
            logging.info(f"ORCHESTRATOR_RETURNED_TYPE: {type(orders_result)}")
            logging.info(
                f"ORCHESTRATOR_RETURNED_COUNT: {len(orders_result) if orders_result else 0}"
            )

            if orders_result:
                logging.info("✅ ORDERS RECEIVED FROM ORCHESTRATOR:")
                for i, order in enumerate(orders_result):
                    logging.info(f"  Order {i + 1}: {order}")
                    if isinstance(order, dict):
                        side = order.get("side", "UNKNOWN")
                        symbol = order.get("symbol", "UNKNOWN")
                        qty = order.get("qty", 0)
                        logging.info(f"    Details: {side} {qty} {symbol}")
            else:
                logging.error("❌ NO ORDERS RETURNED FROM ORCHESTRATOR")
                logging.error(
                    "❌ UNIVERSAL ORCHESTRATOR FAILURE: Expected ANY trades but got 0 orders"
                )
                if expected_trades:
                    logging.error(
                        f"❌ SYSTEMIC TRADE LOSS: Expected {len(expected_trades)} trades across ALL symbols but got 0 orders"
                    )
                    for trade in expected_trades:
                        logging.error(
                            f"❌ LOST: {trade['action']} {trade['symbol']} ${trade['amount']:,.2f}"
                        )

            # Final validation
            expected_count = len(expected_trades)
            actual_count = len(orders_result) if orders_result else 0
            if expected_count > 0 and actual_count == 0:
                logging.critical(
                    "🚨 CRITICAL UNIVERSAL TRADE LOSS at TradingEngine level"
                )
                logging.critical(
                    f"🚨 SYSTEMIC FAILURE: Expected {expected_count} orders for ANY symbols, received {actual_count}"
                )
                logging.critical(
                    "🚨 This indicates a fundamental breakdown in the trading pipeline"
                )

            logging.info(
                f"FINAL_VALIDATION: expected_trades={expected_count}, actual_orders={actual_count}"
            )
            logging.info("=== TRADING ENGINE REBALANCE_PORTFOLIO EXIT ===")

            return orders_result

        except Exception as e:
            logging.error(f"❌ ORCHESTRATOR EXCEPTION: {e}")
            logging.error(f"❌ Exception type: {type(e).__name__}")
            logging.exception("Full orchestrator exception traceback:")
            logging.error("❌ Falling back to empty orders list")
            return []

    def execute_rebalancing(
        self, target_allocations: dict[str, float], mode: str = "market"
    ) -> ExecutionResultDTO:
        """Execute portfolio rebalancing with the specified mode.

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
        final_portfolio_state = build_portfolio_state_data(
            target_allocations, account_info_after, current_positions
        )

        return ExecutionResultDTO(
            orders_executed=orders,
            account_info_before=account_info_before,
            account_info_after=account_info_after,
            execution_summary=dict_to_execution_summary_dto(execution_summary),
            final_portfolio_state=dict_to_portfolio_state_dto(final_portfolio_state),
        )

    # --- Multi-Strategy Execution ---
    def execute_multi_strategy(
        self,
        pre_calculated_signals: Any = None,
        pre_calculated_portfolio: dict[str, float] | None = None,
        pre_calculated_attribution: Any = None,
    ) -> MultiStrategyExecutionResultDTO:
        """Execute all strategies and rebalance portfolio with engine orchestration.

        Args:
            pre_calculated_signals: Pre-calculated strategy signals to avoid double calculation
            pre_calculated_portfolio: Pre-calculated consolidated portfolio
            pre_calculated_attribution: Pre-calculated strategy attribution

        Returns:
            MultiStrategyExecutionResultDTO with comprehensive execution details.

        """
        logging.info("Initiating multi-strategy execution")

        # Pre-execution validation
        try:
            self.get_account_info()
        except (
            DataProviderError,
            TradingClientError,
            ConfigurationError,
            ValueError,
        ) as e:
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="pre_execution_validation",
                component="TradingEngine.execute_multi_strategy",
                function_name="execute_multi_strategy",
                additional_data={
                    "paper_trading": self.paper_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )
            error_handler.handle_error_with_context(
                error=e, context=context, should_continue=False
            )
            logging.error(f"Pre-execution validation failed: {e}")
            return MultiStrategyExecutionResultDTO(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info(
                    "pre_validation_error"
                ),
                account_info_after=_create_default_account_info("pre_validation_error"),
                execution_summary=dict_to_execution_summary_dto(
                    {
                        "error": f"Pre-execution validation failed: {e}",
                        "mode": "error",
                        "account_info_before": _create_default_account_info(
                            "pre_validation_error"
                        ),
                        "account_info_after": _create_default_account_info(
                            "pre_validation_error"
                        ),
                    }
                ),
                final_portfolio_state=None,
            )

        try:
            # === TRADE FLOW DEBUG START ===
            logging.info("=== TRADE FLOW DEBUG START ===")
            logging.info(
                f"Pre-calculated signals received: {len(pre_calculated_signals) if pre_calculated_signals else 'None'}"
            )
            logging.info(
                f"Pre-calculated portfolio received: {len(pre_calculated_portfolio) if pre_calculated_portfolio else 'None'}"
            )

            if pre_calculated_signals:
                for strategy, signals in pre_calculated_signals.items():
                    logging.info(f"Strategy {strategy} signals: {signals}")

            if pre_calculated_portfolio:
                logging.info(
                    f"Pre-calculated portfolio state: {pre_calculated_portfolio}"
                )
                # Log any significant allocations
                for symbol, allocation in pre_calculated_portfolio.items():
                    if allocation > 0.01:  # Log allocations > 1%
                        logging.info(
                            f"ALLOCATION: {symbol}: {allocation:.3f} ({allocation * 100:.1f}%)"
                        )

            if hasattr(self, 'use_execution_v2') and self.use_execution_v2:
                logging.info("🚀 Using execution_v2 for order placement")
            else:
                logging.info("⚠️ Using legacy execution module")
                
            logging.info("Calling _multi_strategy_executor.execute_multi_strategy()...")

            # NEW APPROACH: Generate rebalance plan DTO from portfolio allocation
            # and execute it directly instead of recalculating trades
            try:
                # Convert portfolio allocation to target weights for rebalance plan
                target_weights = {
                    symbol: Decimal(str(allocation))
                    for symbol, allocation in pre_calculated_portfolio.items()
                }

                # Get portfolio rebalancing service directly from the facade
                portfolio_service = self.portfolio_rebalancer.rebalancing_service

                # Create rebalance plan DTO directly from target weights
                rebalance_plan = portfolio_service.create_rebalance_plan_dto(
                    target_weights=target_weights,
                    correlation_id=f"trading_engine_{id(self)}",
                )

                if rebalance_plan and rebalance_plan.items:
                    logging.info(
                        f"Generated rebalance plan with {len(rebalance_plan.items)} trades"
                    )

                    # Execute the rebalance plan directly without recalculation
                    orders_executed = (
                        self._multi_strategy_executor.execute_rebalance_plan(
                            rebalance_plan
                        )
                    )

                    # Convert StrategyType keys to string keys for DTO compatibility
                    strategy_signals_str = {}
                    if pre_calculated_signals:
                        for k, v in pre_calculated_signals.items():
                            key = k.value if hasattr(k, "value") else str(k)
                            strategy_signals_str[key] = v

                    portfolio_allocation_str = {}
                    if pre_calculated_portfolio:
                        for k, v in pre_calculated_portfolio.items():
                            key = k.value if hasattr(k, "value") else str(k)
                            portfolio_allocation_str[key] = v

                    strategy_attribution_str = {}
                    if pre_calculated_attribution:
                        for k, v in pre_calculated_attribution.items():
                            key = k.value if hasattr(k, "value") else str(k)
                            strategy_attribution_str[key] = v

                    # Create execution result manually since we bypassed execute_multi_strategy
                    # Create placeholder AccountInfo instances
                    from the_alchemiser.shared.value_objects.core_types import (
                        AccountInfo,
                    )
                    from the_alchemiser.shared.schemas.execution_summary import (
                        ExecutionSummary,
                        AllocationSummary,
                        TradingSummary,
                        StrategyPnLSummary,
                    )

                    # Placeholder account info since we don't have real account data in this flow
                    placeholder_account = AccountInfo(
                        account_id="placeholder",
                        equity=0.0,
                        cash=0.0,
                        buying_power=0.0,
                        day_trades_remaining=0,
                        portfolio_value=0.0,
                        last_equity=0.0,
                        daytrading_buying_power=0.0,
                        regt_buying_power=0.0,
                        status="ACTIVE",
                    )

                    # Placeholder execution summary
                    placeholder_execution_summary = ExecutionSummary(
                        allocations=AllocationSummary(
                            cash_used=Decimal("0"),
                            total_value=Decimal("0"),
                            strategies_allocated=0,
                            target_allocation={},
                            total_allocation=Decimal(
                                "100.0"
                            ),  # Add missing required field
                            num_positions=len(
                                orders_executed
                            ),  # Add missing required field
                            largest_position_pct=Decimal(
                                "50.0"
                            ),  # Add missing required field (TECL=50%)
                        ),
                        strategy_summary={},
                        trading_summary=TradingSummary(
                            total_orders=len(orders_executed),
                            orders_executed=len(
                                [o for o in orders_executed if o.get("order_id")]
                            ),
                            success_rate=(
                                Decimal("0.0")
                                if len(orders_executed) == 0
                                else Decimal(
                                    str(
                                        len(
                                            [
                                                o
                                                for o in orders_executed
                                                if o.get("order_id")
                                            ]
                                        )
                                        / len(orders_executed)
                                    )
                                )
                            ),
                            total_value=Decimal("0"),
                        ),
                        pnl_summary=StrategyPnLSummary(
                            total_pnl=Decimal("0"),
                            best_performer=None,
                            worst_performer=None,
                            num_profitable=0,
                        ),
                        account_info_before=placeholder_account,
                        account_info_after=placeholder_account,
                        mode="paper",
                        engine_mode="direct_dto",
                        error=(
                            None if len(orders_executed) > 0 else "No orders executed"
                        ),
                    )

                    result = MultiStrategyExecutionResultDTO(
                        success=len(orders_executed) > 0,
                        orders_executed=orders_executed,
                        strategy_signals=strategy_signals_str,
                        portfolio_allocation=portfolio_allocation_str,
                        strategy_attribution=strategy_attribution_str,
                        consolidated_portfolio={},  # Add required field
                        account_info_before=placeholder_account,
                        account_info_after=placeholder_account,
                        execution_summary=placeholder_execution_summary,
                        error_message=(
                            None if len(orders_executed) > 0 else "No orders executed"
                        ),
                    )

                    logging.info(
                        f"Direct DTO execution completed: {len(orders_executed)} orders"
                    )

                else:
                    logging.info("No rebalance plan generated - no trades needed")

                    # Create empty success result
                    result = MultiStrategyExecutionResultDTO(
                        success=True,
                        orders_executed=[],
                        strategy_signals=pre_calculated_signals,
                        portfolio_allocation=pre_calculated_portfolio,
                        strategy_attribution=pre_calculated_attribution,
                        execution_summary=None,
                        error_message="No rebalancing needed",
                    )

            except Exception as e:
                logging.error(f"Failed to execute via rebalance plan DTO: {e}")
                logging.info("Falling back to legacy execute_multi_strategy method")

                # Fallback to legacy method
                result = self._multi_strategy_executor.execute_multi_strategy(
                    pre_calculated_signals,
                    pre_calculated_portfolio,
                    pre_calculated_attribution,
                )

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
            error_handler = TradingSystemErrorHandler()
            context = create_error_context(
                operation="multi_strategy_execution",
                component="TradingEngine.execute_multi_strategy",
                function_name="execute_multi_strategy",
                additional_data={
                    "paper_trading": self.paper_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )
            error_handler.handle_error_with_context(
                error=e, context=context, should_continue=False
            )
            logging.error(f"Multi-strategy execution failed: {e}")

            # Enhanced error handling (fail-fast; no legacy import fallback)
            from the_alchemiser.shared.errors.error_handler import handle_trading_error

            handle_trading_error(
                error=e,
                context="multi-strategy execution",
                component="TradingEngine.execute_multi_strategy",
                additional_data={
                    "paper_trading": self.paper_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )
            handle_trading_error(
                error=e,
                context="multi-strategy execution",
                component="TradingEngine.execute_multi_strategy",
                additional_data={
                    "paper_trading": self.paper_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )

            return MultiStrategyExecutionResultDTO(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info("execution_error"),
                account_info_after=_create_default_account_info("execution_error"),
                execution_summary=dict_to_execution_summary_dto(
                    {
                        "error": f"Execution failed: {e}",
                        "mode": "error",
                        "account_info_before": _create_default_account_info(
                            "execution_error"
                        ),
                        "account_info_after": _create_default_account_info(
                            "execution_error"
                        ),
                    }
                ),
                final_portfolio_state=None,
            )

    # --- Reporting and Dashboard Methods ---
    def _archive_daily_strategy_pnl(self, pnl_summary: dict[str, Any]) -> None:
        """Archive daily strategy P&L for historical tracking."""
        try:
            from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
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
    ) -> dict[
        str, Any
    ]:  # TODO: Change to StrategyPnLSummary once implementation updated
        """Generate comprehensive performance report for all strategies."""
        try:
            current_positions = self.get_positions()
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "strategy_allocations": {
                    k.value: v
                    for k, v in self.strategy_manager.strategy_allocations.items()
                },
                "current_positions": current_positions,
                "performance_summary": self.strategy_manager.get_strategy_performance_summary(),
            }
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
            error_handler.handle_error_with_context(
                error=e, context=context, should_continue=False
            )
            raise StrategyExecutionError(
                f"Failed to generate performance report: {e}"
            ) from e

    def _trigger_post_trade_validation(
        self,
        strategy_signals: dict[StrategyType, Any],
        orders_executed: list[dict[str, Any]],
    ) -> None:
        """Trigger post-trade technical indicator validation for live trading.

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
                    invalid_orders.append(
                        f"Order {i}: Symbol must be string, got {type(symbol)}"
                    )
                    continue

                validated_symbols.add(symbol.strip().upper())

            # Log validation issues
            if invalid_orders:
                logging.warning(
                    f"⚠️ Order validation issues: {'; '.join(invalid_orders)}"
                )

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
                if (
                    symbol
                    and symbol != "NUCLEAR_PORTFOLIO"
                    and symbol != "BEAR_PORTFOLIO"
                ):
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
            tecl_strategy_symbols = [
                "XLK",
                "KMLM",
                "SPXL",
                "TECL",
                "BIL",
                "BSV",
                "UVXY",
                "SQQQ",
            ]
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
                    "strategy_signals": {
                        str(k): v for k, v in strategy_signals.items()
                    },
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

    @classmethod
    def create_from_container(
        cls,
        container: Any,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> TradingEngine:
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
    ) -> TradingEngine:
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
    ) -> TradingEngine:
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
    """Test TradingEngine multi-strategy execution (fail-fast DI only)."""
    logging.basicConfig(level=logging.WARNING)  # Reduced verbosity
    logger = get_logger(__name__)

    logger.info(
        "trading_engine_test_started",
        extra={"component": "TradingEngine.main", "operation": "test_initialization"},
    )

    # Modern DI initialization (no legacy fallback). Any failure should surface immediately.
    # These imports are kept at function level to avoid circular imports at module load time
    # since main.py indirectly imports this module through CLI components
    from the_alchemiser.main import TradingSystem
    from the_alchemiser.shared.config.container import (
        ApplicationContainer,
    )

    TradingSystem()  # Initialize DI system side-effects
    container = ApplicationContainer()

    trader = TradingEngine.create_from_container(
        container=container,
        strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
        ignore_market_hours=True,
    )
    trader.paper_trading = True

    logger.info(
        "executing_multi_strategy",
        extra={
            "component": "TradingEngine.main",
            "operation": "strategy_execution",
            "paper_trading": True,
            "strategy_allocations": {"NUCLEAR": 0.5, "TECL": 0.5},
        },
    )
    result = trader.execute_multi_strategy()

    log_with_context(
        logger,
        logging.INFO,
        "multi_strategy_execution_completed",
        component="TradingEngine.main",
        operation="execution_result",
        success=result.success,
    )

    logger.info(
        "generating_performance_report",
        extra={
            "component": "TradingEngine.main",
            "operation": "performance_report_generation",
        },
    )
    report = trader.get_multi_strategy_performance_report()
    if "error" not in report:
        log_with_context(
            logger,
            logging.INFO,
            "performance_report_generated_successfully",
            component="TradingEngine.main",
            operation="performance_report_result",
            current_positions_count=len(report["current_positions"]),
            strategy_tracking_count=len(report["performance_summary"]),
        )
    else:
        log_with_context(
            logger,
            logging.ERROR,
            "performance_report_generation_failed",
            component="TradingEngine.main",
            operation="performance_report_error",
            error=str(report["error"]),
        )


if __name__ == "__main__":
    main()
