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
from typing import Any, Protocol, cast

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.smart_execution import SmartExecution
from the_alchemiser.application.portfolio.services.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.application.trading.alpaca_client import AlpacaClient
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
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

from ..execution.execution_manager import ExecutionManager
from ..reporting.reporting import build_portfolio_state_data


class StrategyManagerAdapter:
    """Typed-backed adapter to provide run_all_strategies for callers.

    This avoids importing legacy modules by wrapping TypedStrategyManager.
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
    ) -> tuple[dict[StrategyType, dict[str, Any]], dict[str, float], dict[str, list[StrategyType]]]:
        from datetime import UTC, datetime

        aggregated = self._typed.generate_all_signals(datetime.now(UTC))

        def to_legacy_dict(signal: Any) -> dict[str, Any]:
            symbol_value = signal.symbol.value
            symbol_str = "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value
            return {
                "symbol": symbol_str,
                "action": signal.action,
                "confidence": float(signal.confidence.value),
                "reasoning": signal.reasoning,
                "allocation_percentage": float(signal.target_allocation.value),
            }

        legacy_signals: dict[StrategyType, dict[str, Any]] = {}
        consolidated_portfolio: dict[str, float] = {}

        for st, signals in aggregated.get_signals_by_strategy().items():
            if not signals:
                legacy_signals[st] = {
                    "symbol": "N/A",
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "No signal produced",
                    "allocation_percentage": 0.0,
                }
            else:
                legacy_signals[st] = to_legacy_dict(signals[0])

        # Build consolidated portfolio from all signals
        for strategy_type, signals in aggregated.get_signals_by_strategy().items():
            strategy_allocation = self._typed.strategy_allocations.get(strategy_type, 0.0)

            for signal in signals:
                if signal.action in ["BUY", "LONG"]:
                    symbol_str = signal.symbol.value

                    # Use the actual signal allocation for individual symbols
                    if symbol_str != "PORT":
                        # Calculate individual allocation as signal proportion * strategy allocation
                        individual_allocation = (
                            float(signal.target_allocation.value) * strategy_allocation
                        )
                        # If symbol already exists, add to allocation (multiple strategies can recommend same symbol)
                        if symbol_str in consolidated_portfolio:
                            consolidated_portfolio[symbol_str] += individual_allocation
                        else:
                            consolidated_portfolio[symbol_str] = individual_allocation

        return legacy_signals, consolidated_portfolio, {}

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
        except Exception:
            # Provide a basic empty summary structure
            return {
                st.name: {"pnl": 0.0, "trades": 0} for st in self._typed.strategy_allocations.keys()
            }


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
        self.portfolio_rebalancer: Any  # PortfolioManagementFacade instance

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
            # Backward compatibility mode - deprecated
            import warnings

            warnings.warn(
                "Direct TradingEngine() instantiation is deprecated. "
                "Use TradingEngine.create_with_di() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
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

            # Data provider shim (pandas DataFrame) for current strategy engines
            self.data_provider = container.infrastructure.data_provider()

            # AlpacaManager for trading operations - use its trading_client property
            alpaca_manager = container.infrastructure.alpaca_manager()
            self.trading_client = alpaca_manager.trading_client

            # Typed market data port for migrated codepaths
            self._market_data_port = container.infrastructure.market_data_service()

            self.logger.info("Successfully initialized services from DI container")
        except (AttributeError, ImportError, ConfigurationError) as e:
            self.logger.error(
                f"Failed to initialize services from DI container: {e}", exc_info=True
            )
            raise ConfigurationError(
                f"DI container failed to provide required services: {e}"
            ) from e

        # Get configuration from container with proper error handling
        try:
            # Acquire TradingServiceManager for enhanced portfolio operations
            try:
                self._trading_service_manager = container.services.trading_service_manager()
            except (AttributeError, ConfigurationError, ImportError):
                # Optional; portfolio rebalancer will fail fast later if required
                self._trading_service_manager = None  # pragma: no cover

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
        except (AttributeError, ValueError, ConfigurationError) as e:
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
        # Use typed MarketDataService for both typed port and pandas-compat provider
        # so strategies get a consistent implementation exposing get_data (temporary compat).
        try:
            alpaca_manager = trading_service_manager.alpaca_manager
            self.data_provider = MarketDataService(alpaca_manager)
        except Exception as e:
            raise ConfigurationError(
                f"TradingServiceManager missing AlpacaManager for market data: {e}"
            ) from e
        # Use the actual Alpaca TradingClient for correct market-hours and order queries
        try:
            self.trading_client = trading_service_manager.alpaca_manager.trading_client
        except Exception as e:
            raise ConfigurationError(f"TradingServiceManager missing trading client: {e}") from e
        self.paper_trading = trading_service_manager.alpaca_manager.is_paper_trading
        # Provide typed market data port in this mode
        try:
            self._market_data_port = MarketDataService(trading_service_manager.alpaca_manager)
        except Exception:
            self._market_data_port = None
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

        # Initialize repositories/services without legacy facade
        try:
            # Load credentials via SecretsManager to avoid legacy provider
            from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager
            from the_alchemiser.services.trading.trading_service_manager import (
                TradingServiceManager,
            )

            sm = SecretsManager()
            api_key, secret_key = sm.get_alpaca_keys(paper_trading=paper_trading)
            if not api_key or not secret_key:
                raise ConfigurationError(
                    "Missing Alpaca credentials for traditional initialization"
                )

            # Core repositories/services
            self._alpaca_manager = AlpacaManager(str(api_key), str(secret_key), paper_trading)
            self.trading_client = self._alpaca_manager.trading_client

            # Use typed market data service for both provider (pandas compat) and typed port
            self._market_data_port = MarketDataService(self._alpaca_manager)
            self.data_provider = self._market_data_port

            # Optional enhanced service manager for downstream ops
            self._trading_service_manager = TradingServiceManager(
                str(api_key), str(secret_key), paper=paper_trading
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
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

        try:
            # Build an AlpacaClient once using the same authenticated trading client
            alpaca_manager: AlpacaManager
            if hasattr(self, "_trading_service_manager") and hasattr(
                self._trading_service_manager, "alpaca_manager"
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

        # Portfolio rebalancer
        try:
            # Require TradingServiceManager for portfolio operations
            trading_manager = getattr(self, "_trading_service_manager", None)
            if trading_manager and hasattr(trading_manager, "alpaca_manager"):
                # Use modern portfolio management facade
                self.portfolio_rebalancer = PortfolioManagementFacade(
                    trading_manager=trading_manager,
                )
            else:
                # No legacy fallbacks - fail fast and require proper DI setup
                raise ConfigurationError(
                    "TradingServiceManager is required for portfolio operations. "
                    "Please use TradingEngine.create_with_di() or provide trading_service_manager parameter."
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

    def _create_strategy_manager_bridge(self) -> Any:
        """Create a bridge object that provides run_all_strategies() interface for CLI compatibility."""

        class StrategyManagerBridge:
            def __init__(self, typed_manager: TypedStrategyManager):
                self._typed = typed_manager

            def run_all_strategies(
                self,
            ) -> tuple[
                dict[StrategyType, dict[str, Any]], dict[str, float], dict[str, list[StrategyType]]
            ]:
                """Bridge method that converts typed signals to legacy format for CLI compatibility."""
                from datetime import UTC, datetime

                aggregated = self._typed.generate_all_signals(datetime.now(UTC))

                # Convert typed signals to legacy format
                legacy_signals: dict[StrategyType, dict[str, Any]] = {}
                consolidated_portfolio: dict[str, float] = {}

                for strategy_type, signals in aggregated.get_signals_by_strategy().items():
                    if signals:
                        # Use first signal as representative
                        signal = signals[0]
                        symbol_value = signal.symbol.value
                        symbol_str = "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value

                        legacy_signals[strategy_type] = {
                            "symbol": symbol_str,
                            "action": signal.action,
                            "confidence": float(signal.confidence.value),
                            "reasoning": signal.reasoning,
                            "allocation_percentage": float(signal.target_allocation.value) * 100,
                        }

                        # Build portfolio allocation
                        if signal.action in ["BUY", "LONG"] and symbol_str != "PORT":
                            strategy_allocation = self._typed.strategy_allocations.get(
                                strategy_type, 0.0
                            )
                            individual_allocation = (
                                float(signal.target_allocation.value) * strategy_allocation
                            )
                            consolidated_portfolio[symbol_str] = individual_allocation
                    else:
                        legacy_signals[strategy_type] = {
                            "symbol": "N/A",
                            "action": "HOLD",
                            "confidence": 0.0,
                            "reasoning": "No signal produced",
                            "allocation_percentage": 0.0,
                        }

                return legacy_signals, consolidated_portfolio, {}

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
        """
        try:
            account_info = self._account_info_provider.get_account_info()

            # Always normalize account_id to string since Alpaca returns UUID objects
            # but Pydantic AccountInfo expects string
            if "account_id" in account_info:
                # Create a mutable copy as a regular dict, not TypedDict
                account_info_dict = dict(account_info)
                account_info_dict["account_id"] = str(account_info_dict["account_id"])
                # Type cast back to AccountInfo after modification
                account_info = cast(AccountInfo, account_info_dict)

            # Ensure required keys are present (defensive normalization)
            required_keys = {
                "account_id",
                "equity",
                "cash",
                "buying_power",
                "day_trades_remaining",
                "portfolio_value",
                "last_equity",
                "daytrading_buying_power",
                "regt_buying_power",
                "status",
            }
            if not all(k in account_info for k in required_keys):  # pragma: no cover
                # Normalize explicitly for TypedDict compatibility
                base = _create_default_account_info(str(account_info.get("account_id", "unknown")))
                normalized: AccountInfo = {
                    "account_id": str(account_info.get("account_id", base["account_id"])),
                    "equity": float(account_info.get("equity", base["equity"])),
                    "cash": float(account_info.get("cash", base["cash"])),
                    "buying_power": float(account_info.get("buying_power", base["buying_power"])),
                    "day_trades_remaining": int(
                        account_info.get("day_trades_remaining", base["day_trades_remaining"])
                    ),
                    "portfolio_value": float(
                        account_info.get("portfolio_value", base["portfolio_value"])
                    ),
                    "last_equity": float(account_info.get("last_equity", base["last_equity"])),
                    "daytrading_buying_power": float(
                        account_info.get("daytrading_buying_power", base["daytrading_buying_power"])
                    ),
                    "regt_buying_power": float(
                        account_info.get("regt_buying_power", base["regt_buying_power"])
                    ),
                    "status": (
                        "ACTIVE"
                        if str(account_info.get("status", base["status"])) == "ACTIVE"
                        else "INACTIVE"
                    ),
                }
                return normalized

            return account_info
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
                from the_alchemiser.services.errors import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="trading_engine",
                )
            except (ImportError, AttributeError):
                pass

            return _create_default_account_info("data_error")
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
                from the_alchemiser.services.errors import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="TradingEngine.get_account_info",
                    additional_data={"paper_trading": self.paper_trading},
                )
            except (ImportError, AttributeError):
                pass  # Fallback for backward compatibility

            return _create_default_account_info("client_error")

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
        """Rebalance portfolio to target allocation with sequential execution to prevent buying power issues.

        Executes sells first, waits for settlement via WebSocket monitoring, then executes buys
        with refreshed buying power to prevent insufficient funds errors.

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
        logging.info(
            f"🚀 Initiating sequential portfolio rebalancing with {len(target_portfolio)} symbols"
        )
        logging.debug(f"Target allocations: {target_portfolio}")

        try:
            all_orders: list[OrderDetails] = []

            # Phase 1: Execute SELL orders to free buying power
            sell_orders = self._execute_sell_orders_phase(target_portfolio, strategy_attribution)
            all_orders.extend(sell_orders)

            # Phase 2: Wait for sell order settlements and buying power refresh
            self._wait_for_buying_power_refresh(sell_orders)

            # Phase 3: Execute BUY orders with refreshed buying power
            buy_orders = self._execute_buy_orders_phase(target_portfolio, strategy_attribution)
            all_orders.extend(buy_orders)

            # Final summary
            sell_count = len(sell_orders)
            buy_count = len(buy_orders)
            logging.info(
                f"✅ Sequential portfolio rebalancing completed: "
                f"{sell_count} SELLs, {buy_count} BUYs, {len(all_orders)} total orders"
            )

            return all_orders

        except (
            TradingClientError,
            DataProviderError,
            ConfigurationError,
            ValueError,
            AttributeError,
        ) as e:
            logging.error(f"Sequential portfolio rebalancing failed: {e}")
            return []

    def _execute_sell_orders_phase(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute only SELL orders from the rebalancing plan."""
        logging.info("🔄 Phase 1: Executing SELL orders to free buying power")

        # Execute only SELL phase via facade to avoid BP validation block
        phase_fn = getattr(self._rebalancing_service, "rebalance_portfolio_phase", None)
        if callable(phase_fn):
            all_orders = phase_fn(target_portfolio, phase="sell")
        else:
            all_orders = self._rebalancing_service.rebalance_portfolio(
                target_portfolio, strategy_attribution
            )

        # Filter for SELL orders only
        sell_orders = []
        for order_details in all_orders:
            if order_details["side"] == "sell":
                sell_orders.append(order_details)

        if sell_orders:
            logging.info(f"Executing {len(sell_orders)} SELL orders")
            for order in sell_orders:
                logging.info(f"SELL {order['symbol']}: {order['qty']} shares")
        else:
            logging.info("No SELL orders needed")

        return sell_orders

    def _execute_buy_orders_phase(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute only BUY orders with refreshed buying power."""
        logging.info("🔄 Phase 3: Executing BUY orders with refreshed buying power")
        # Get fresh account info to update buying power
        account_info = self.get_account_info()
        # AccountInfo is a TypedDict; use key access for mypy compatibility
        current_buying_power = float(account_info["buying_power"])  # key access on TypedDict
        logging.info(f"Current buying power: ${current_buying_power:,.2f}")

        # Execute only BUY phase via facade to leverage scaled buys
        phase_fn = getattr(self._rebalancing_service, "rebalance_portfolio_phase", None)
        if callable(phase_fn):
            all_orders = phase_fn(target_portfolio, phase="buy")
        else:
            all_orders = self._rebalancing_service.rebalance_portfolio(
                target_portfolio, strategy_attribution
            )

        # Filter for BUY orders only
        buy_orders: list[OrderDetails] = []
        for order_details in all_orders:
            if order_details["side"] == "buy":
                buy_orders.append(order_details)

        if buy_orders:
            logging.info(f"Executing {len(buy_orders)} BUY orders")
            for order in buy_orders:
                logging.info(f"BUY {order['symbol']}: {order['qty']} shares")
        else:
            logging.info("No BUY orders needed")

        return buy_orders

    def _wait_for_buying_power_refresh(self, sell_orders: list[OrderDetails]) -> None:
        """Wait for sell order settlements and buying power to refresh via WebSocket monitoring."""
        if not sell_orders:
            return

        logging.info("⏳ Phase 2: Waiting for sell order settlements and buying power refresh...")

        # Extract order IDs for monitoring
        sell_order_ids = [order["id"] for order in sell_orders if order["id"] != "unknown"]

        if not sell_order_ids:
            logging.warning("No valid order IDs to monitor, using time-based delay")
            import time

            time.sleep(5)  # Fallback delay
            return

        try:
            # Use WebSocket monitoring to track order completion
            # Get API credentials for WebSocket monitoring
            from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager
            from the_alchemiser.infrastructure.websocket.websocket_order_monitor import (
                OrderCompletionMonitor,
            )

            sm = SecretsManager()
            api_key, secret_key = sm.get_alpaca_keys(paper_trading=self.paper_trading)

            monitor = OrderCompletionMonitor(self.trading_client, api_key, secret_key)

            # Wait for all sell orders to complete (30 second timeout)
            completion_result = monitor.wait_for_order_completion(
                sell_order_ids, max_wait_seconds=30
            )

            # Check if orders completed successfully
            if completion_result["status"] == "completed":
                completed_order_ids = completion_result["orders_completed"]
                logging.info(
                    f"✅ {len(completed_order_ids)} sell orders completed, buying power should be refreshed"
                )
            elif completion_result["status"] == "timeout":
                completed_order_ids = completion_result["orders_completed"]
                logging.warning(
                    f"⏰ WebSocket monitoring timed out. {len(completed_order_ids)} orders completed out of {len(sell_order_ids)}"
                )
            else:  # error status
                logging.error(f"❌ WebSocket monitoring error: {completion_result['message']}")
                completed_order_ids = completion_result["orders_completed"]

            # Brief additional delay to ensure buying power propagation
            import time

            time.sleep(2)

        except Exception as e:
            logging.warning(f"WebSocket monitoring failed, using fallback delay: {e}")
            import time

            time.sleep(10)  # Fallback delay if WebSocket fails

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
            execution_summary=execution_summary,
            final_portfolio_state=final_portfolio_state,
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
            logging.error(f"❌ Post-trade validation failed: {e}")

    def display_target_vs_current_allocations(
        self,
        target_portfolio: dict[str, float],
        account_info: AccountInfo | dict[str, Any],
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
        # Accept both legacy display shape and typed AccountInfo
        def _to_float(v: Any, default: float = 0.0) -> float:
            try:
                if v is None:
                    return default
                return float(v)
            except (TypeError, ValueError):
                return default

        def _to_int(v: Any, default: int = 0) -> int:
            try:
                if v is None:
                    return default
                return int(v)
            except (TypeError, ValueError):
                return default

        # Safely derive day_trades_remaining from either key
        day_trades_remaining_val = 0
        if isinstance(account_info, dict):
            v1 = account_info.get("day_trades_remaining")
            v2 = account_info.get("day_trade_count")
            for _v in (v1, v2):
                day_trades_remaining_val = _to_int(_v, 0)
                if day_trades_remaining_val != 0:
                    break

        account_info_typed: AccountInfo = {
            "account_id": str(
                (account_info.get("account_id") if isinstance(account_info, dict) else None)
                or (account_info.get("account_number") if isinstance(account_info, dict) else None)
                or "unknown"
            ),
            "equity": _to_float(account_info.get("equity", 0.0), 0.0),
            "cash": _to_float(account_info.get("cash", 0.0), 0.0),
            "buying_power": _to_float(account_info.get("buying_power", 0.0), 0.0),
            "day_trades_remaining": day_trades_remaining_val,
            "portfolio_value": _to_float(
                (account_info.get("portfolio_value") if isinstance(account_info, dict) else None)
                or (account_info.get("equity", 0.0) if isinstance(account_info, dict) else 0.0),
                0.0,
            ),
            "last_equity": _to_float(
                (account_info.get("last_equity") if isinstance(account_info, dict) else None)
                or (account_info.get("equity", 0.0) if isinstance(account_info, dict) else 0.0),
                0.0,
            ),
            "daytrading_buying_power": _to_float(
                (
                    account_info.get("daytrading_buying_power")
                    if isinstance(account_info, dict)
                    else None
                )
                or (
                    account_info.get("buying_power", 0.0) if isinstance(account_info, dict) else 0.0
                ),
                0.0,
            ),
            "regt_buying_power": _to_float(
                (account_info.get("regt_buying_power") if isinstance(account_info, dict) else None)
                or (
                    account_info.get("buying_power", 0.0) if isinstance(account_info, dict) else 0.0
                ),
                0.0,
            ),
            "status": (
                "ACTIVE"
                if str(account_info.get("status", "INACTIVE")).upper() == "ACTIVE"
                else "INACTIVE"
            ),
        }
        target_values = calculate_position_target_deltas(target_portfolio, account_info_typed)
        current_values = extract_current_position_values(current_positions)

        # Use existing formatter for display
        # Ensure a plain dict is passed to the renderer to satisfy its signature
        render_target_vs_current_allocations(
            target_portfolio,
            dict(account_info) if isinstance(account_info, dict) else dict(account_info_typed),
            current_positions,
        )

        return target_values, current_values

    def display_multi_strategy_summary(
        self, execution_result: MultiStrategyExecutionResultDTO
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

    # Use DI approach instead of deprecated traditional constructor
    try:
        from the_alchemiser.container.application_container import ApplicationContainer
        from the_alchemiser.main import TradingSystem

        # Initialize DI system
        TradingSystem()
        container = ApplicationContainer()

        trader = TradingEngine.create_with_di(
            container=container,
            strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
            ignore_market_hours=True,
        )
        trader.paper_trading = True
    except (ImportError, ConfigurationError, TradingClientError) as e:
        console.print(f"[red]Failed to initialize with DI: {e}[/red]")
        console.print("[yellow]Falling back to traditional method[/yellow]")
        trader = TradingEngine(
            paper_trading=True,
            strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5},
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
