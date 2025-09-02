#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Account Facade - Coordinated account, position, and price data access.

This facade provides a unified interface for account-related operations by coordinating
between existing services:
- AccountService: Core account info and positions
- PositionService: Enhanced position analysis (optional)
- MarketDataService: Price data and validation

The facade handles:
- Account ID normalization (UUID to string)
- Required field enforcement for AccountInfo compatibility
- Error handling and fallback coordination
- Type-safe delegation without duplicating business logic

Key Features:
- Reuses existing service methods for all operations
- Normalizes data for consistent TypedDict compliance
- Coordinates multiple services for enriched account data
- Maintains error handling parity with existing engine methods
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, cast

from the_alchemiser.execution.mappers.account_mapping import account_summary_to_typed
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    ClosedPositionData,
    EnrichedAccountInfo,
    PositionsDict,
)
from the_alchemiser.shared.schemas.accounts import (
    AccountMetricsDTO,
    AccountSummaryDTO,
    EnrichedAccountSummaryDTO,
)
from the_alchemiser.execution.brokers.account_service import AccountService
from the_alchemiser.shared.services.errors import handle_trading_error
from the_alchemiser.shared.types.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.strategy.data.market_data_service import MarketDataService
from the_alchemiser.portfolio.positions.position_service import PositionService
from the_alchemiser.utils.serialization import ensure_serialized_dict

logger = logging.getLogger(__name__)


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


class AccountFacade:
    """Unified facade for account, position, and price data coordination.

    This facade coordinates between multiple services to provide consistent,
    normalized account data without duplicating business logic.
    """

    def __init__(
        self,
        account_service: AccountService,
        market_data_service: MarketDataService | None = None,
        position_service: PositionService | None = None,
    ) -> None:
        """Initialize the account facade.

        Args:
            account_service: Required account service for core operations
            market_data_service: Optional market data service for price validation
            position_service: Optional position service for enhanced analysis

        """
        self._account_service = account_service
        self._market_data_service = market_data_service
        self._position_service = position_service
        self.logger = logging.getLogger(__name__)

    def get_account_info(self) -> AccountInfo:
        """Get basic account information with normalization and validation.

        Delegates to AccountService.get_account_info() and ensures:
        - Account ID is normalized to string (handles UUID objects)
        - All required AccountInfo fields are present
        - Values are properly typed

        Returns:
            AccountInfo with normalized and validated fields

        """
        try:
            # Delegate to account service for core account info
            account_info = self._account_service.get_account_info()

            # Always normalize account_id to string since Alpaca returns UUID objects
            # but AccountInfo TypedDict expects string
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

        except (
            DataProviderError,
            TradingClientError,
            ConnectionError,
            TimeoutError,
            AttributeError,
        ) as e:
            self.logger.error(f"Failed to retrieve account information: {e}")

            # Enhanced error handling for context
            try:
                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="AccountFacade.get_account_info",
                )
            except (ImportError, AttributeError):
                pass  # Fallback for backward compatibility

            return _create_default_account_info("error")

    def get_enriched_account_info(self, paper_trading: bool = True) -> EnrichedAccountInfo:
        """Get enriched account information with portfolio history and performance data.

        Coordinates between AccountService and potential AlpacaManager access for
        portfolio history data not available through standard service interfaces.

        Args:
            paper_trading: Whether using paper trading mode for context

        Returns:
            EnrichedAccountInfo with portfolio history when available

        """
        try:
            # Get base account info through our normalized method
            base_account = self.get_account_info()

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
                "trading_mode": "paper" if paper_trading else "live",
                "market_hours_ignored": False,  # Default value, can be updated by caller
            }

            # Add portfolio history using service abstraction (no repository reach-through)
            portfolio_history = self._account_service.get_portfolio_history()
            if portfolio_history:
                enriched["portfolio_history"] = {
                    "profit_loss": portfolio_history.get("profit_loss", []),
                    "profit_loss_pct": portfolio_history.get("profit_loss_pct", []),
                    "equity": portfolio_history.get("equity", []),
                    "timestamp": portfolio_history.get("timestamp", []),
                }

            # Add recent closed P&L if available via service abstraction
            closed_pnl = self._account_service.get_recent_closed_positions()
            if closed_pnl:
                sanitized: list[dict[str, object]] = []
                for item in closed_pnl:
                    if isinstance(item, dict):
                        sanitized.append(
                            {
                                "symbol": str(item.get("symbol", "")),
                                "realized_pnl": float(item.get("realized_pnl", 0.0)),
                                "realized_pnl_pct": float(item.get("realized_pnl_pct", 0.0)),
                                "trade_count": int(item.get("trade_count", 0)),
                            }
                        )
                enriched["recent_closed_pnl"] = cast("list[ClosedPositionData]", sanitized)

            return enriched

        except (DataProviderError, TradingClientError, AttributeError) as e:
            self.logger.error(f"Failed to retrieve enriched account information: {e}")
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
                "trading_mode": "paper" if paper_trading else "live",
                "market_hours_ignored": False,
            }

    def get_positions(self) -> PositionsDict:
        """Get current positions via account service delegation.

        Delegates to AccountService.get_positions_dict() which handles:
        - Position retrieval from account repository
        - Non-zero quantity filtering
        - Side determination (long/short)
        - Proper typing for PositionsDict

        Returns:
            PositionsDict with current positions keyed by symbol

        """
        try:
            return self._account_service.get_positions_dict()
        except (
            DataProviderError,
            TradingClientError,
            ConnectionError,
            TimeoutError,
        ) as e:
            self.logger.error(f"Failed to retrieve positions: {e}")
            return {}

    def get_positions_dict(self) -> PositionsDict:
        """Get current positions as dictionary keyed by symbol.

        This is an alias for get_positions() to maintain protocol compatibility
        with PositionProvider protocol.

        Returns:
            PositionsDict with current positions keyed by symbol

        """
        return self.get_positions()

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol with validation and fallback coordination.

        Coordinates between MarketDataService (preferred) and AccountService (fallback)
        for price retrieval with proper validation.

        Args:
            symbol: Stock symbol to get price for

        Returns:
            Current price as float, or 0.0 if price unavailable

        """
        if not symbol or not isinstance(symbol, str):
            self.logger.warning(f"Invalid symbol provided to get_current_price: {symbol}")
            return 0.0

        symbol = symbol.upper()

        try:
            # Prefer MarketDataService if available for better validation and caching
            if self._market_data_service is not None:
                price = self._market_data_service.get_validated_price(symbol)
                if price is not None and price > 0:
                    self.logger.debug(
                        f"Retrieved price from MarketDataService for {symbol}: ${price:.2f}"
                    )
                    return price

            # Fallback to AccountService price method
            price = self._account_service.get_current_price(symbol)

            # Facade-level validation
            if price and price > 0:
                self.logger.debug(f"Retrieved price from AccountService for {symbol}: ${price:.2f}")
                return price
            self.logger.warning(f"Invalid price received for {symbol}: {price}")
            return 0.0

        except (
            DataProviderError,
            ConnectionError,
            TimeoutError,
            ValueError,
            AttributeError,
            NotImplementedError,
        ) as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            return 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols with coordination and validation.

        Coordinates between services for batch price retrieval with proper validation
        and error handling.

        Args:
            symbols: List of stock symbols to get prices for

        Returns:
            Dict mapping symbols to current prices, excluding symbols with invalid prices

        """
        if not symbols or not isinstance(symbols, list):
            self.logger.warning(f"Invalid symbols list provided: {symbols}")
            return {}

        # Clean and validate symbols
        valid_symbols = [s.upper() for s in symbols if isinstance(s, str) and s.strip()]

        if not valid_symbols:
            self.logger.warning("No valid symbols provided to get_current_prices")
            return {}

        try:
            # Try MarketDataService batch method if available
            if self._market_data_service is not None:
                try:
                    # MarketDataService may not have batch method, fall back to individual calls
                    if hasattr(self._market_data_service, "get_current_prices"):
                        prices = cast(Any, self._market_data_service).get_current_prices(
                            valid_symbols
                        )
                        if prices:
                            # Validate prices
                            valid_prices = {}
                            for symbol, price in prices.items():
                                if price and price > 0:
                                    valid_prices[symbol] = price
                                else:
                                    self.logger.warning(
                                        f"Invalid price from MarketDataService for {symbol}: {price}"
                                    )
                            return valid_prices
                    else:
                        # Fall back to individual calls through MarketDataService
                        valid_prices = {}
                        for symbol in valid_symbols:
                            price = self._market_data_service.get_validated_price(symbol)
                            if price is not None and price > 0:
                                valid_prices[symbol] = price
                            else:
                                self.logger.warning(
                                    f"Invalid price from MarketDataService for {symbol}: {price}"
                                )
                        return valid_prices
                except (AttributeError, NotImplementedError):
                    # Fall through to AccountService
                    pass

            # Fallback to AccountService batch method
            prices = self._account_service.get_current_prices(valid_symbols)

            # Facade-level validation and logging
            valid_prices = {}
            for symbol, price in prices.items():
                if price and price > 0:
                    valid_prices[symbol] = price
                else:
                    self.logger.warning(f"Invalid price from AccountService for {symbol}: {price}")

            self.logger.debug(
                f"Retrieved {len(valid_prices)} valid prices out of {len(valid_symbols)} requested"
            )
            return valid_prices

        except (
            DataProviderError,
            ConnectionError,
            TimeoutError,
            ValueError,
            AttributeError,
            NotImplementedError,
        ) as e:
            self.logger.error(f"Failed to get current prices: {e}")
            return {}

    # --- Typed Domain Integration Methods ---

    def _build_minimal_summary(self) -> dict[str, Any]:
        """Internal helper to construct a minimal fallback summary.

        Returns:
            Serialized dictionary containing minimal account summary data.

        """
        default_account = _create_default_account_info("error")
        minimal_metrics = AccountMetricsDTO(
            cash_ratio=Decimal("0.0"),
            market_exposure=Decimal("0.0"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("0.0"),
        )
        minimal_summary = AccountSummaryDTO(
            account_id=default_account["account_id"],
            equity=Decimal(str(default_account["equity"])),
            cash=Decimal(str(default_account["cash"])),
            market_value=Decimal("0.0"),
            buying_power=Decimal(str(default_account["buying_power"])),
            last_equity=Decimal(str(default_account["last_equity"])),
            day_trade_count=0,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=minimal_metrics,
        )
        enriched_dto = EnrichedAccountSummaryDTO(raw=dict(default_account), summary=minimal_summary)
        return ensure_serialized_dict(enriched_dto)

    def get_enriched_account_summary(self) -> dict[str, Any]:
        """Get enriched account summary using typed domain objects.

        This method provides integration with the typed domain system by:
        - Getting raw account summary from AccountService
        - Converting to typed domain objects using existing mappers
        - Returning serialized dictionary representation

        Returns:
            Serialized dictionary with both raw and typed account summary data.

        """
        try:
            # Get comprehensive account summary from service
            raw_summary = self._account_service.get_account_summary()

            # Convert to typed domain objects using existing mappers
            typed_summary = account_summary_to_typed(raw_summary)

            # Create AccountSummaryDTO directly with proper types
            summary_dto = AccountSummaryDTO(
                account_id=typed_summary.account_id,
                equity=typed_summary.equity.amount,
                cash=typed_summary.cash.amount,
                market_value=typed_summary.market_value.amount,
                buying_power=typed_summary.buying_power.amount,
                last_equity=typed_summary.last_equity.amount,
                day_trade_count=typed_summary.day_trade_count,
                pattern_day_trader=typed_summary.pattern_day_trader,
                trading_blocked=typed_summary.trading_blocked,
                transfers_blocked=typed_summary.transfers_blocked,
                account_blocked=typed_summary.account_blocked,
                calculated_metrics=AccountMetricsDTO(
                    cash_ratio=typed_summary.calculated_metrics.cash_ratio,
                    market_exposure=typed_summary.calculated_metrics.market_exposure,
                    leverage_ratio=typed_summary.calculated_metrics.leverage_ratio,
                    available_buying_power_ratio=typed_summary.calculated_metrics.available_buying_power_ratio,
                ),
            )

            enriched_dto = EnrichedAccountSummaryDTO(raw=raw_summary, summary=summary_dto)
            return ensure_serialized_dict(enriched_dto)

        except (
            DataProviderError,
            TradingClientError,
            ConnectionError,
            TimeoutError,
            ValueError,
        ) as e:
            self.logger.error(f"Failed to get enriched account summary (service error): {e}")
            return self._build_minimal_summary()
        except Exception:  # pragma: no cover - unexpected
            self.logger.exception("Unexpected error building enriched account summary")
            return self._build_minimal_summary()
