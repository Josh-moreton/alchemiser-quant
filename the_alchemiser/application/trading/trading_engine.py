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
    >>> engine.display_multi_strategy_summary(result)

    DI Example:
    >>> container = ApplicationContainer.create_for_testing()
    >>> engine = TradingEngine.create_with_di(container=container)
    >>> result = engine.execute_multi_strategy()
"""

import logging
from datetime import datetime
from typing import Any, Protocol

from alpaca.trading.enums import OrderSide

from the_alchemiser.domain.strategies.strategy_manager import (
    MultiStrategyManager,
    StrategyType,
)
from the_alchemiser.domain.types import (
    AccountInfo,
    EnrichedAccountInfo,
    OrderDetails,
    PositionsDict,
)
from the_alchemiser.execution.account_service import AccountService
from the_alchemiser.infrastructure.adapters.legacy_portfolio_adapter import (
    LegacyPortfolioRebalancerAdapter,
)
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)

from ..execution.execution_manager import ExecutionManager
from ..reporting.reporting import (
    build_portfolio_state_data,
)
from ..types import MultiStrategyExecutionResult

# Conditional import for legacy portfolio rebalancer
try:
    # Try to import from the actual location - this will likely fail but is handled gracefully
    from the_alchemiser.legacy.portfolio_rebalancer.portfolio_rebalancer_legacy import (  # type: ignore[import-untyped]
        PortfolioRebalancer as _RuntimePortfolioRebalancer,
    )
except ImportError:  # pragma: no cover - runtime fallback when legacy module missing
    _RuntimePortfolioRebalancer = None


class LegacyPortfolioRebalancerStub:
    """Minimal fallback stub used at runtime if legacy module is not available."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list["StrategyType"]] | None = None,
    ) -> list["OrderDetails"]:
        return []


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

    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
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
        paper_trading: bool = True,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
        config: Settings | None = None,
        # NEW: DI-aware parameters
        trading_service_manager: Any = None,
        container: Any = None,
    ) -> None:
        """Initialize the TradingEngine with optional dependency injection.

        Args:
            paper_trading (bool): Whether to use paper trading account. Defaults to True.
            strategy_allocations (Dict[StrategyType, float], optional): Portfolio allocation
                between strategies. If None, uses equal allocation.
            ignore_market_hours (bool): Whether to ignore market hours when placing orders.
                Defaults to False.
            config: Configuration object. If None, loads from global config.
            trading_service_manager: Injected TradingServiceManager (DI mode)
            container: DI container for full DI mode

        Note:
            The engine supports three initialization modes:
            1. Traditional: paper_trading, config parameters (backward compatibility)
            2. Partial DI: injected trading_service_manager
            3. Full DI: container provides all dependencies
        """
        self.logger = logging.getLogger(__name__)

        # Type annotations for attributes that can have multiple types
        self.portfolio_rebalancer: Any  # Can be LegacyPortfolioRebalancerAdapter, _RuntimePortfolioRebalancer, or LegacyPortfolioRebalancerStub

        # Determine initialization mode
        if container is not None:
            # Full DI mode
            self._init_with_container(container, strategy_allocations, ignore_market_hours)
        elif trading_service_manager is not None:
            # Partial DI mode
            self._init_with_service_manager(
                trading_service_manager, strategy_allocations, ignore_market_hours
            )
        else:
            # Backward compatibility mode
            self._init_traditional(paper_trading, strategy_allocations, ignore_market_hours, config)

    def _init_with_container(
        self,
        container: Any,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool,
    ) -> None:
        """Initialize using full DI container."""
        self._container = container

        # Use correct services from container - provide correct objects to correct consumers
        try:
            self.logger.info("Initializing services from DI container")

            # AccountService implements the required protocols for TradingEngine
            self.account_service = container.services.account_service()

            # UnifiedDataProvider has get_data() method needed by strategies
            self.data_provider = container.infrastructure.data_provider()

            # AlpacaManager for trading operations - use its trading_client property
            alpaca_manager = container.infrastructure.alpaca_manager()
            self.trading_client = alpaca_manager.trading_client

            self.logger.info("Successfully initialized services from DI container")
        except Exception as e:
            self.logger.error(
                f"Failed to initialize services from DI container: {e}", exc_info=True
            )
            # Don't fallback to Mock - let the error propagate
            raise ConfigurationError(
                f"DI container failed to provide required services: {e}"
            ) from e

        # Get configuration from container with proper error handling
        try:
            self.paper_trading = container.config.paper_trading()
            config_dict = {
                "alpaca": {
                    "api_key": container.config.alpaca_api_key(),
                    "secret_key": container.config.alpaca_secret_key(),
                    "paper_trading": container.config.paper_trading(),
                }
            }
            self.logger.info(
                f"Successfully loaded config from DI container: paper_trading={self.paper_trading}"
            )
        except Exception as e:
            self.logger.error(f"Failed to load config from DI container: {e}", exc_info=True)
            raise ConfigurationError(f"DI container failed to provide configuration: {e}") from e

        self.ignore_market_hours = ignore_market_hours

        # Initialize other components using DI
        self._init_common_components(strategy_allocations, config_dict)

    def _init_with_service_manager(
        self,
        trading_service_manager: Any,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool,
    ) -> None:
        """Initialize using injected TradingServiceManager."""
        self._container = None
        self._trading_service_manager = trading_service_manager
        self.data_provider = trading_service_manager
        self.trading_client = trading_service_manager.alpaca_manager
        self.paper_trading = trading_service_manager.alpaca_manager.is_paper_trading
        self.ignore_market_hours = ignore_market_hours

        # Create minimal config for components
        config_dict: dict[str, Any] = {}

        self._init_common_components(strategy_allocations, config_dict)

    def _init_traditional(
        self,
        paper_trading: bool,
        strategy_allocations: dict[StrategyType, float] | None,
        ignore_market_hours: bool,
        config: Settings | None,
    ) -> None:
        """Initialize using traditional method (backward compatibility)."""
        self._container = None
        self.paper_trading = paper_trading
        self.ignore_market_hours = ignore_market_hours

        # Load configuration
        try:
            from the_alchemiser.infrastructure.config import load_settings

            self.config = config or load_settings()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration error: {e}")

        # Initialize data provider (existing logic)
        try:
            from the_alchemiser.infrastructure.data_providers.data_provider import (
                UnifiedDataProvider,
            )

            self.data_provider = UnifiedDataProvider(
                paper_trading=paper_trading, config=self.config
            )
            self.trading_client = self.data_provider.trading_client
        except Exception as e:
            self.logger.error(f"Failed to initialize data provider: {e}")
            raise

        config_dict = self.config.model_dump() if self.config else {}
        self._init_common_components(strategy_allocations, config_dict)

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
        from the_alchemiser.application.execution.smart_execution import SmartExecution

        try:
            self.order_manager = SmartExecution(
                trading_client=self.trading_client,
                data_provider=self.data_provider,
                ignore_market_hours=self.ignore_market_hours,
                config=config_dict,
            )
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize smart execution: {e}",
                context={"trading_client_type": type(self.trading_client).__name__},
            ) from e

        # Portfolio rebalancer
        try:
            # Use the trading service manager if available, otherwise use old portfolio rebalancer
            trading_manager = getattr(self, "_trading_service_manager", None)
            if trading_manager and hasattr(trading_manager, "alpaca_manager"):
                # This is a TradingServiceManager - use new system
                self.portfolio_rebalancer = LegacyPortfolioRebalancerAdapter(
                    trading_manager=trading_manager,
                    use_new_system=True,  # Enable enhanced features with legacy interface
                )
            else:
                # Fall back to original portfolio rebalancer for backward compatibility
                if _RuntimePortfolioRebalancer is not None:
                    self.portfolio_rebalancer = _RuntimePortfolioRebalancer(self)
                else:
                    # Use lightweight stub at runtime when legacy module is missing
                    self.portfolio_rebalancer = LegacyPortfolioRebalancerStub()
        except Exception as e:
            raise TradingClientError(
                f"Failed to initialize portfolio rebalancer: {e}",
                context={"engine_type": type(self).__name__},
            ) from e

        # Strategy manager - pass our data provider to ensure same trading mode
        try:
            self.strategy_manager = MultiStrategyManager(
                self.strategy_allocations,
                shared_data_provider=self.data_provider,  # Pass our data provider
                config=getattr(self, "config", None),
            )
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
            self.account_service = AccountService(self.data_provider)
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
        self._account_info_provider: AccountInfoProvider = self.account_service
        self._position_provider: PositionProvider = self.account_service
        self._price_provider: PriceProvider = self.account_service
        self._rebalancing_service: RebalancingService = self.portfolio_rebalancer
        self._multi_strategy_executor: MultiStrategyExecutor = self.execution_manager

        # Logging setup
        logging.info(f"TradingEngine initialized - Paper Trading: {self.paper_trading}")

    # --- Account and Position Methods ---
    def get_account_info(
        self,
    ) -> dict[str, Any]:  # TODO: Change to AccountInfo once data structure matches
        """Get comprehensive account information including P&L data.

        Retrieves detailed account information including portfolio value, equity,
        buying power, recent portfolio history, open positions, and closed P&L data.

        Returns:
            Dict: Account information containing:
                - account_number: Account identifier
                - portfolio_value: Total portfolio value
                - equity: Account equity
                - buying_power: Available buying power
                - cash: Available cash
                - day_trade_count: Number of day trades
                - status: Account status
                - portfolio_history: Recent portfolio performance
                - open_positions: Current open positions
                - recent_closed_pnl: Recent closed position P&L (last 7 days)

        Note:
            Returns empty dict if account information cannot be retrieved.
        """
        try:
            account_info = self._account_info_provider.get_account_info()

            # Convert AccountInfo to enriched dict with additional trading context
            enriched_info: dict[str, Any] = {
                "account_number": account_info["account_id"],
                "portfolio_value": account_info["portfolio_value"],
                "equity": account_info["equity"],
                "buying_power": account_info["buying_power"],
                "cash": account_info["cash"],
                "day_trade_count": account_info["day_trades_remaining"],
                "status": account_info["status"],
                "trading_mode": "paper" if self.paper_trading else "live",
                "market_hours_ignored": self.ignore_market_hours,
            }

            return enriched_info
        except DataProviderError as e:
            from the_alchemiser.infrastructure.logging.logging_utils import (
                get_logger,
                log_error_with_context,
            )

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_info_retrieval",
                function="get_account_info",
                trading_mode="paper" if self.paper_trading else "live",
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error retrieving account information: {e}")

            # Enhanced error handling
            try:
                from the_alchemiser.services.errors.error_handler import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="trading_engine",
                )
            except (ImportError, AttributeError):
                pass

            return {}
        except (TradingClientError, ConnectionError, TimeoutError, AttributeError) as e:
            from the_alchemiser.infrastructure.logging.logging_utils import (
                get_logger,
                log_error_with_context,
            )

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_info_client_error",
                function="get_account_info",
                trading_mode="paper" if self.paper_trading else "live",
                error_type=type(e).__name__,
            )
            logging.error(f"Client error retrieving account information: {e}")

            # Enhanced error handling
            try:
                from the_alchemiser.services.errors.error_handler import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="TradingEngine.get_account_info",
                    additional_data={"paper_trading": self.paper_trading},
                )
            except (ImportError, AttributeError):
                pass  # Fallback for backward compatibility

            return {}

    def get_enriched_account_info(self) -> EnrichedAccountInfo:
        """Get enriched account information including portfolio history and P&L data.

        This extends the basic AccountInfo with portfolio performance data suitable for
        display and reporting purposes.

        Returns:
            EnrichedAccountInfo with portfolio history and closed P&L data.
        """
        try:
            # Get base account info
            base_account = self._account_info_provider.get_account_info()

            # Create enriched account info starting with base data
            enriched: EnrichedAccountInfo = {
                "account_id": base_account["account_id"],
                "equity": base_account["equity"],
                "cash": base_account["cash"],
                "buying_power": base_account["buying_power"],
                "day_trades_remaining": base_account["day_trades_remaining"],
                "portfolio_value": base_account["portfolio_value"],
                "last_equity": base_account["last_equity"],
                "daytrading_buying_power": base_account["daytrading_buying_power"],
                "regt_buying_power": base_account["regt_buying_power"],
                "status": base_account["status"],
                "trading_mode": "paper" if self.paper_trading else "live",
                "market_hours_ignored": self.ignore_market_hours,
            }

            # Add portfolio history if available
            try:
                portfolio_history = self.data_provider.get_portfolio_history()
                if portfolio_history:
                    enriched["portfolio_history"] = {
                        "profit_loss": portfolio_history.get("profit_loss", []),
                        "profit_loss_pct": portfolio_history.get("profit_loss_pct", []),
                        "equity": portfolio_history.get("equity", []),
                        "timestamp": portfolio_history.get("timestamp", []),
                    }
            except (
                DataProviderError,
                ConnectionError,
                TimeoutError,
                KeyError,
                AttributeError,
            ) as e:
                logging.debug(f"Could not retrieve portfolio history: {e}")

            # Add recent closed P&L if available
            try:
                # Note: This would need to be implemented in data_provider
                # closed_pnl = self.data_provider.get_recent_closed_positions()
                # if closed_pnl:
                #     enriched["recent_closed_pnl"] = closed_pnl
                pass
            except (
                DataProviderError,
                ConnectionError,
                TimeoutError,
                KeyError,
                AttributeError,
            ) as e:
                logging.debug(f"Could not retrieve recent closed P&L: {e}")

            return enriched

        except (DataProviderError, TradingClientError, ConfigurationError, AttributeError) as e:
            logging.error(f"Failed to retrieve enriched account information: {e}")
            # Return minimal enriched account info
            default_account = _create_default_account_info("error")
            return {
                "account_id": default_account["account_id"],
                "equity": default_account["equity"],
                "cash": default_account["cash"],
                "buying_power": default_account["buying_power"],
                "day_trades_remaining": default_account["day_trades_remaining"],
                "portfolio_value": default_account["portfolio_value"],
                "last_equity": default_account["last_equity"],
                "daytrading_buying_power": default_account["daytrading_buying_power"],
                "regt_buying_power": default_account["regt_buying_power"],
                "status": default_account["status"],
                "trading_mode": "paper" if self.paper_trading else "live",
                "market_hours_ignored": self.ignore_market_hours,
            }

    def get_positions(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, Any] to PositionsDict
        """Get current positions via account service.

        Returns:
            Dict of current positions keyed by symbol with validated PositionInfo structure.
        """
        try:
            positions = self._position_provider.get_positions_dict()
            return positions
        except (DataProviderError, TradingClientError, ConnectionError, TimeoutError) as e:
            logging.error(f"Failed to retrieve positions: {e}")
            return {}

    def get_positions_dict(
        self,
    ) -> PositionsDict:  # Phase 18: Migrated from dict[str, dict[str, Any]] to PositionsDict
        """Get current positions as dictionary keyed by symbol.

        This is an alias for get_positions() to maintain backward compatibility.

        Returns:
            Dict of current positions keyed by symbol with validated PositionInfo structure.
        """
        return self.get_positions()

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol with engine-level validation.

        Args:
            symbol: Stock symbol to get price for.

        Returns:
            Current price as float, or 0.0 if price unavailable.
        """
        if not symbol or not isinstance(symbol, str):
            logging.warning(f"Invalid symbol provided to get_current_price: {symbol}")
            return 0.0

        try:
            price = self._price_provider.get_current_price(symbol.upper())

            # Engine-level validation
            if price and price > 0:
                logging.debug(f"Retrieved price for {symbol}: ${price:.2f}")
                return price
            else:
                logging.warning(f"Invalid price received for {symbol}: {price}")
                return 0.0

        except (DataProviderError, ConnectionError, TimeoutError, ValueError, AttributeError) as e:
            logging.error(f"Failed to get current price for {symbol}: {e}")
            return 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols with engine-level validation.

        Args:
            symbols: List of stock symbols to get prices for.

        Returns:
            Dict mapping symbols to current prices, excluding symbols with invalid prices.
        """
        if not symbols or not isinstance(symbols, list):
            logging.warning(f"Invalid symbols list provided: {symbols}")
            return {}

        # Clean and validate symbols
        valid_symbols = [s.upper() for s in symbols if isinstance(s, str) and s.strip()]

        if not valid_symbols:
            logging.warning("No valid symbols provided to get_current_prices")
            return {}

        try:
            prices = self._price_provider.get_current_prices(valid_symbols)

            # Engine-level validation and logging
            valid_prices = {}
            for symbol, price in prices.items():
                if price and price > 0:
                    valid_prices[symbol] = price
                else:
                    logging.warning(f"Invalid price for {symbol}: {price}")

            logging.debug(
                f"Retrieved {len(valid_prices)} valid prices out of {len(valid_symbols)} requested"
            )
            return valid_prices

        except (DataProviderError, ConnectionError, TimeoutError, ValueError, AttributeError) as e:
            logging.error(f"Failed to get current prices: {e}")
            return {}

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
        """Rebalance portfolio to target allocation with engine-level orchestration.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages.
            strategy_attribution: Dictionary mapping symbols to contributing strategies.

        Returns:
            List of executed orders during rebalancing as OrderDetails.
        """
        if not target_portfolio:
            logging.warning("Empty target portfolio provided to rebalance_portfolio")
            return []

        # Validate portfolio allocations
        total_allocation = sum(target_portfolio.values())
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")

        # Log rebalancing initiation
        logging.info(f"Initiating portfolio rebalancing with {len(target_portfolio)} symbols")
        logging.debug(f"Target allocations: {target_portfolio}")

        try:
            # Use composed rebalancing service (returns legacy dict format)
            raw_orders = self._rebalancing_service.rebalance_portfolio(
                target_portfolio, strategy_attribution
            )

            # Convert raw orders to OrderDetails
            orders: list[OrderDetails] = []
            for raw_order in raw_orders:
                order_details: OrderDetails = {
                    "id": raw_order.get("id", "unknown"),
                    "symbol": raw_order.get("symbol", ""),
                    "qty": raw_order.get("qty", 0.0),
                    "side": raw_order.get("side", "buy"),
                    "order_type": raw_order.get("order_type", "market"),
                    "time_in_force": raw_order.get("time_in_force", "day"),
                    "status": raw_order.get("status", "new"),
                    "filled_qty": raw_order.get("filled_qty", 0.0),
                    "filled_avg_price": raw_order.get("filled_avg_price", 0.0),
                    "created_at": raw_order.get("created_at", ""),
                    "updated_at": raw_order.get("updated_at", ""),
                }
                orders.append(order_details)

            # Engine-level post-processing
            if orders:
                logging.info(f"Portfolio rebalancing completed with {len(orders)} orders")
            else:
                logging.info("Portfolio rebalancing completed with no orders needed")

            return orders

        except (
            TradingClientError,
            DataProviderError,
            ConfigurationError,
            ValueError,
            AttributeError,
        ) as e:
            logging.error(f"Portfolio rebalancing failed: {e}")
            return []

    def execute_rebalancing(
        self, target_allocations: dict[str, float], mode: str = "market"
    ) -> dict[str, Any]:
        """
        Execute portfolio rebalancing with the specified mode.

        Args:
            target_allocations: Target allocation percentages by symbol
            mode: Rebalancing mode ('market', 'limit', 'paper') - currently unused but kept for compatibility

        Returns:
            Dictionary with trading summary and order details for compatibility
        """
        orders = self.rebalance_portfolio(target_allocations)

        # Create a summary structure for test compatibility
        return {
            "trading_summary": {"total_orders": len(orders), "orders_executed": orders},
            "orders": orders,
        }

    # --- Multi-Strategy Execution ---
    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """Execute all strategies and rebalance portfolio with engine orchestration.

        Returns:
            MultiStrategyExecutionResult with comprehensive execution details.
        """
        logging.info("Initiating multi-strategy execution")

        # Pre-execution validation
        try:
            account_info = self.get_account_info()
            if not account_info:
                logging.error(
                    "Cannot proceed with multi-strategy execution: account info unavailable"
                )
                return MultiStrategyExecutionResult(
                    success=False,
                    strategy_signals={},
                    consolidated_portfolio={},
                    orders_executed=[],
                    account_info_before=_create_default_account_info("error"),
                    account_info_after=_create_default_account_info("error"),
                    execution_summary={"error": "Failed to retrieve account information"},
                    final_portfolio_state={},
                )
        except (DataProviderError, TradingClientError, ConfigurationError, ValueError) as e:
            logging.error(f"Pre-execution validation failed: {e}")
            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info("pre_validation_error"),
                account_info_after=_create_default_account_info("pre_validation_error"),
                execution_summary={"error": f"Pre-execution validation failed: {e}"},
                final_portfolio_state={},
            )

        try:
            # Use composed multi-strategy executor
            result = self._multi_strategy_executor.execute_multi_strategy()

            # Engine-level post-processing
            if result.success:
                logging.info("Multi-strategy execution completed successfully")

                # Add engine context to result
                if result.execution_summary:
                    result.execution_summary["engine_mode"] = (
                        "paper" if self.paper_trading else "live"
                    )
                    result.execution_summary["market_hours_ignored"] = self.ignore_market_hours

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
                from the_alchemiser.services.errors.error_handler import handle_trading_error

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

            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=_create_default_account_info("execution_error"),
                account_info_after=_create_default_account_info("execution_error"),
                execution_summary={"error": f"Execution failed: {e}"},
                final_portfolio_state={},
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
            logging.error(f"Failed to archive daily strategy P&L: {e}")

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
        except (StrategyExecutionError, DataProviderError, AttributeError, ValueError) as e:
            logging.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

    def _build_portfolio_state_data(
        self,
        target_portfolio: dict[str, float],
        account_info: dict[str, Any],  # TODO: Change to AccountInfo once structure matches
        current_positions: dict[str, Any],  # TODO: Change to PositionsDict once structure matches
    ) -> dict[str, Any]:  # TODO: Change to ExecutionResult once structure matches
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
            logging.error(f"❌ Post-trade validation failed: {e}")

    def display_target_vs_current_allocations(
        self,
        target_portfolio: dict[str, float],
        account_info: dict[str, Any],
        current_positions: dict[str, Any],
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Display target vs current allocations and return calculated values.

        Shows a comparison between target portfolio weights and current position values,
        helping to visualize rebalancing needs.

        Args:
            target_portfolio (Dict[str, float]): Target allocation weights by symbol.
            account_info (Dict): Account information including portfolio value.
            current_positions (Dict): Current position data by symbol.

        Returns:
            Tuple[Dict[str, float], Dict[str, float]]: A tuple containing:
                - target_values: Target dollar values by symbol
                - current_values: Current market values by symbol

        Note:
            Uses Rich table formatting via cli_formatter for beautiful display.
        """
        from the_alchemiser.interface.cli.cli_formatter import render_target_vs_current_allocations
        from the_alchemiser.services.account.account_utils import (
            calculate_position_target_deltas,
            extract_current_position_values,
        )

        # Use helper functions to calculate values
        # Convert legacy dict to AccountInfo for the utility function
        account_info_typed: AccountInfo = {
            "account_id": account_info.get("account_number", "unknown"),
            "equity": account_info.get("equity", 0.0),
            "cash": account_info.get("cash", 0.0),
            "buying_power": account_info.get("buying_power", 0.0),
            "day_trades_remaining": account_info.get("day_trade_count", 0),
            "portfolio_value": account_info.get("portfolio_value", 0.0),
            "last_equity": account_info.get("equity", 0.0),
            "daytrading_buying_power": account_info.get("daytrading_buying_power", 0.0),
            "regt_buying_power": account_info.get("buying_power", 0.0),
            "status": "ACTIVE" if account_info.get("status") == "ACTIVE" else "INACTIVE",
        }
        target_values = calculate_position_target_deltas(target_portfolio, account_info_typed)
        current_values = extract_current_position_values(current_positions)

        # Use existing formatter for display
        render_target_vs_current_allocations(target_portfolio, account_info, current_positions)

        return target_values, current_values

    def display_multi_strategy_summary(
        self, execution_result: MultiStrategyExecutionResult
    ) -> None:
        """
        Display a summary of multi-strategy execution results using Rich
        Args:
            execution_result: The execution result to display
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        # Type annotation for orders_table that can be either Table or Panel
        orders_table: Table | Panel

        console = Console()

        if not execution_result.success:
            console.print(
                Panel(
                    f"[bold red]Execution failed: {execution_result.execution_summary.get('error', 'Unknown error')}[/bold red]",
                    title="Execution Result",
                    style="red",
                )
            )
            return

        # Portfolio allocation display
        portfolio_table = Table(title="Consolidated Portfolio", show_lines=False)
        portfolio_table.add_column("Symbol", style="bold cyan", justify="center")
        portfolio_table.add_column("Allocation", style="bold green", justify="right")
        portfolio_table.add_column("Visual", style="white", justify="left")

        sorted_portfolio = sorted(
            execution_result.consolidated_portfolio.items(), key=lambda x: x[1], reverse=True
        )

        for symbol, weight in sorted_portfolio:
            # Create visual bar
            bar_length = int(weight * 20)  # Scale to 20 chars max
            bar = "█" * bar_length + "░" * (20 - bar_length)

            portfolio_table.add_row(symbol, f"{weight:.1%}", f"[green]{bar}[/green]")

        # Orders executed table
        if execution_result.orders_executed:
            orders_table = Table(
                title=f"Orders Executed ({len(execution_result.orders_executed)})", show_lines=False
            )
            orders_table.add_column("Type", style="bold", justify="center")
            orders_table.add_column("Symbol", style="cyan", justify="center")
            orders_table.add_column("Quantity", style="white", justify="right")
            orders_table.add_column("Actual Value", style="green", justify="right")

            for order in execution_result.orders_executed:
                side = order.get("side", "")
                side_value = str(side).upper()  # Convert to uppercase for display

                side_color = "green" if side_value == "BUY" else "red"

                # Calculate actual filled value
                filled_qty = float(order.get("filled_qty", 0))
                filled_avg_price = float(order.get("filled_avg_price", 0) or 0)
                actual_value = filled_qty * filled_avg_price

                # Fall back to estimated value if no filled data available
                if actual_value == 0:
                    estimated_value = order.get("estimated_value", 0)
                    try:
                        # Handle various types that estimated_value might be
                        if isinstance(estimated_value, int | float):
                            actual_value = float(estimated_value)
                        elif isinstance(estimated_value, str):
                            actual_value = float(estimated_value)
                        else:
                            actual_value = 0.0
                    except (ValueError, TypeError):
                        actual_value = 0.0

                orders_table.add_row(
                    f"[{side_color}]{side_value}[/{side_color}]",
                    order.get("symbol", ""),
                    f"{order.get('qty', 0):.6f}",
                    f"${actual_value:.2f}",
                )
        else:
            orders_table = Panel(
                "[green]Portfolio already balanced - no trades needed[/green]",
                title="Orders Executed",
                style="green",
            )

        # Account summary
        if execution_result.account_info_after:
            # Try to get enriched account info for better display
            try:
                enriched_account = self.get_enriched_account_info()
                account = enriched_account
            except (DataProviderError, AttributeError, ValueError):
                # Convert AccountInfo to EnrichedAccountInfo format
                base_account = execution_result.account_info_after
                account = {
                    "account_id": base_account["account_id"],
                    "equity": base_account["equity"],
                    "cash": base_account["cash"],
                    "buying_power": base_account["buying_power"],
                    "day_trades_remaining": base_account["day_trades_remaining"],
                    "portfolio_value": base_account.get("portfolio_value", 0.0),
                    "last_equity": base_account.get("last_equity", 0.0),
                    "daytrading_buying_power": base_account.get("daytrading_buying_power", 0.0),
                    "regt_buying_power": base_account.get("regt_buying_power", 0.0),
                    "status": base_account.get("status", "INACTIVE"),  # Use valid literal
                    "trading_mode": "paper" if self.paper_trading else "live",
                    "market_hours_ignored": self.ignore_market_hours,
                }

            account_content = Text()
            account_content.append(
                f"Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}\n",
                style="bold green",
            )
            account_content.append(
                f"Cash Balance: ${float(account.get('cash', 0)):,.2f}\n", style="bold blue"
            )

            # Add portfolio history P&L if available
            portfolio_history = account.get("portfolio_history", {})
            if portfolio_history and "profit_loss" in portfolio_history:
                profit_loss = portfolio_history.get("profit_loss", [])
                profit_loss_pct = portfolio_history.get("profit_loss_pct", [])
                if profit_loss:
                    recent_pl = profit_loss[-1]
                    recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                    pl_color = "green" if recent_pl >= 0 else "red"
                    pl_sign = "+" if recent_pl >= 0 else ""
                    account_content.append(
                        f"Recent P&L: {pl_sign}${recent_pl:,.2f} ({pl_sign}{recent_pl_pct * 100:.2f}%)\n",
                        style=f"bold {pl_color}",
                    )

            account_panel = Panel(account_content, title="Account Summary", style="bold white")

        # Recent closed positions P&L table
        closed_pnl_table = None
        if execution_result.account_info_after:
            # Try to get enriched account info for recent closed P&L
            try:
                enriched_account = self.get_enriched_account_info()
                closed_pnl = enriched_account.get("recent_closed_pnl", [])
            except (DataProviderError, AttributeError, ValueError):
                # AccountInfo doesn't have recent_closed_pnl, so use empty list
                closed_pnl = []

            if closed_pnl:
                closed_pnl_table = Table(
                    title="Recent Closed Positions P&L (Last 7 Days)", show_lines=False
                )
                closed_pnl_table.add_column("Symbol", style="bold cyan", justify="center")
                closed_pnl_table.add_column("Realized P&L", style="bold", justify="right")
                closed_pnl_table.add_column("P&L %", style="bold", justify="right")
                closed_pnl_table.add_column("Trades", style="white", justify="center")

                total_realized_pnl = 0.0  # Initialize as float to handle float | int addition

                for position in closed_pnl[:8]:  # Show top 8 in CLI summary
                    symbol = position.get("symbol", "N/A")
                    realized_pnl = position.get("realized_pnl", 0)
                    realized_pnl_pct = position.get("realized_pnl_pct", 0)
                    trade_count = position.get("trade_count", 0)

                    total_realized_pnl += realized_pnl

                    # Color coding for P&L
                    pnl_color = "green" if realized_pnl >= 0 else "red"
                    pnl_sign = "+" if realized_pnl >= 0 else ""

                    closed_pnl_table.add_row(
                        symbol,
                        f"[{pnl_color}]{pnl_sign}${realized_pnl:,.2f}[/{pnl_color}]",
                        f"[{pnl_color}]{pnl_sign}{realized_pnl_pct:.2f}%[/{pnl_color}]",
                        str(trade_count),
                    )

                # Add total row
                if len(closed_pnl) > 0:
                    total_pnl_color = "green" if total_realized_pnl >= 0 else "red"
                    total_pnl_sign = "+" if total_realized_pnl >= 0 else ""
                    closed_pnl_table.add_row(
                        "[bold]TOTAL[/bold]",
                        f"[bold {total_pnl_color}]{total_pnl_sign}${total_realized_pnl:,.2f}[/bold {total_pnl_color}]",
                        "-",
                        "-",
                    )

        # Display everything
        console.print()
        console.print(portfolio_table)
        console.print()

        # Sonar: collapse redundant type check
        console.print(orders_table)
        console.print()

        # Display closed P&L table if available
        if closed_pnl_table:
            console.print(closed_pnl_table)
            console.print()

        console.print(account_panel)
        console.print()

        console.print(
            Panel(
                "[bold green]Multi-strategy execution completed successfully[/bold green]",
                title="Execution Complete",
                style="green",
            )
        )

    @classmethod
    def create_with_di(
        cls,
        container: Any = None,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
    ) -> "TradingEngine":
        """Factory method for creating TradingEngine with full DI.

        Args:
            container: DI container for dependency injection
            strategy_allocations: Strategy allocation weights
            ignore_market_hours: Whether to ignore market hours

        Returns:
            TradingEngine instance with all dependencies injected
        """
        return cls(
            container=container,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=ignore_market_hours,
        )


def main() -> None:
    """Test TradingEngine multi-strategy execution"""
    from rich.console import Console

    console = Console()

    logging.basicConfig(level=logging.WARNING)  # Reduced verbosity
    console.print("[bold cyan]Trading Engine Test[/bold cyan]")
    console.print("─" * 50)

    trader = TradingEngine(
        paper_trading=True, strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5}
    )

    console.print("[yellow]Executing multi-strategy...[/yellow]")
    result = trader.execute_multi_strategy()
    trader.display_multi_strategy_summary(result)

    console.print("[yellow]Getting performance report...[/yellow]")
    report = trader.get_multi_strategy_performance_report()
    if "error" not in report:
        console.print("[green]Performance report generated successfully[/green]")
        console.print(f"   Current positions: {len(report['current_positions'])}")
        console.print(f"   Strategy tracking: {len(report['performance_summary'])}")
    else:
        console.print(f"[red]Error generating report: {report['error']}[/red]")


if __name__ == "__main__":
    main()
