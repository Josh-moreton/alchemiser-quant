"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Alpaca data adapter - thin wrapper around shared.brokers.AlpacaManager
for portfolio-specific data access.

This adapter provides a clean interface for portfolio_v2 to access positions,
prices, and account data. It handles error mapping, type conversion (to Decimal),
and structured logging with correlation IDs for distributed tracing.

Thread-safety: This adapter is stateless except for the AlpacaManager reference.
Thread-safety depends on the AlpacaManager instance provided.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "portfolio_v2.adapters.alpaca_data_adapter"


@dataclass(frozen=True)
class AccountInfo:
    """Complete account information from Alpaca.

    Contains all capital-related fields for proper margin-aware trading.
    """

    cash: Decimal  # Settled cash balance
    buying_power: Decimal | None  # Total buying power (cash + margin)
    equity: Decimal | None  # Account equity (net liquidation value)
    portfolio_value: Decimal | None  # Total portfolio value
    initial_margin: Decimal | None  # Margin used to open positions
    maintenance_margin: Decimal | None  # Margin required to maintain positions


class AlpacaDataAdapter:
    """Adapter for accessing portfolio data via shared AlpacaManager.

    Provides a clean interface for portfolio_v2 to access positions,
    prices, and account data without directly depending on Alpaca APIs.

    This adapter:
    - Converts broker data to Decimal for monetary precision
    - Maps broker exceptions to DataProviderError
    - Supports correlation_id/causation_id for distributed tracing
    - Uses structured logging for production observability

    Thread-safety: Stateless except for AlpacaManager reference.
    Thread-safety depends on the provided AlpacaManager instance.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize adapter with AlpacaManager instance.

        Args:
            alpaca_manager: Shared AlpacaManager instance for broker API access.
                Must be authenticated and configured for the desired environment
                (paper or live trading).

        Raises:
            TypeError: If alpaca_manager is None or not an AlpacaManager instance

        """
        if alpaca_manager is None:
            raise TypeError("alpaca_manager cannot be None")
        self._alpaca_manager = alpaca_manager

    def get_positions(
        self,
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> dict[str, Decimal]:
        """Get current positions as symbol -> quantity mapping.

        Returns available quantity (qty_available) which excludes shares tied up
        in open orders. Falls back to total quantity (qty) if qty_available is
        not available from the broker.

        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID linking to triggering event

        Returns:
            Dictionary mapping symbol (uppercase) to quantity as Decimal.
            Returns empty dict if no positions exist.
            All quantities are non-negative Decimals with proper precision.

        Raises:
            DataProviderError: If positions cannot be retrieved from broker,
                position data is malformed, or conversion to Decimal fails.

        Pre-conditions:
            - AlpacaManager must be authenticated and connected

        Post-conditions:
            - All returned symbols are uppercase strings
            - All quantities are non-negative Decimals
            - Empty dict returned if no positions (not None)

        Thread-safety:
            Depends on AlpacaManager thread-safety

        """
        logger.debug(
            "Fetching current positions",
            module=MODULE_NAME,
            action="get_positions",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        try:
            # Get positions from AlpacaManager
            raw_positions = self._alpaca_manager.get_positions()

            # Convert to symbol -> quantity mapping with Decimal precision
            # Use qty_available instead of qty to account for shares tied up in open orders
            positions = {}
            for position in raw_positions:
                symbol = str(position.symbol).upper()
                # Use qty_available if available, fallback to qty for compatibility
                available_qty = getattr(position, "qty_available", None)
                if available_qty is not None:
                    quantity = Decimal(str(available_qty))
                else:
                    # Fallback to total qty if qty_available is not available
                    quantity = Decimal(str(position.qty))
                positions[symbol] = quantity

            logger.debug(
                "Retrieved positions",
                module=MODULE_NAME,
                action="get_positions",
                position_count=len(positions),
                symbols=sorted(positions.keys()),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            return positions

        except (AttributeError, KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to retrieve positions",
                module=MODULE_NAME,
                action="get_positions",
                error_type=e.__class__.__name__,
                error_message=str(e),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            raise DataProviderError(
                f"Failed to retrieve positions: {e}",
                context={
                    "operation": "get_positions",
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            ) from e

    def get_current_prices(
        self,
        symbols: list[str],
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> dict[str, Decimal]:
        """Get current prices for specified symbols.

        Fetches prices sequentially for each symbol. For large symbol lists (>50),
        this may be slow and could hit rate limits.

        Args:
            symbols: List of trading symbols. Empty strings and None values will be
                filtered out. Symbols are automatically uppercased.
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID linking to triggering event

        Returns:
            Dictionary mapping symbol (uppercase) to current price as Decimal.
            Returns empty dict if no valid symbols provided.
            All prices are positive Decimals.

        Raises:
            DataProviderError: If price retrieval fails, a symbol has invalid price
                (None or <= 0), or conversion to Decimal fails.

        Pre-conditions:
            - AlpacaManager must be authenticated and connected
            - Market should be open for real-time prices (stale prices returned when closed)

        Post-conditions:
            - All returned symbols are uppercase strings
            - All prices are positive Decimals (> 0)
            - Empty dict returned if no valid symbols (not None)

        Thread-safety:
            Depends on AlpacaManager thread-safety

        Notes:
            - May hit rate limits with >100 symbols
            - Sequential fetching may be slow for large symbol lists
            - Consider batching if broker supports it

        """
        # Filter and validate symbols
        if not symbols:
            return {}

        valid_symbols = [
            s.strip().upper() for s in symbols if s and isinstance(s, str) and s.strip()
        ]
        if not valid_symbols:
            logger.warning(
                "No valid symbols after filtering",
                module=MODULE_NAME,
                action="get_current_prices",
                original_count=len(symbols),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            return {}

        logger.debug(
            "Fetching current prices",
            module=MODULE_NAME,
            action="get_current_prices",
            symbol_count=len(valid_symbols),
            symbols=sorted(valid_symbols),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        try:
            prices = {}

            # Get prices individually using structured pricing approach
            # Future enhancement: Migrate to batch API if available for better performance
            for symbol in valid_symbols:
                raw_price = self._alpaca_manager.get_current_price(symbol)

                if raw_price is None or raw_price <= 0:
                    # Invalid price data from broker
                    error_msg = f"Invalid price for {symbol}: {raw_price}"
                    logger.error(
                        "Invalid price data",
                        module=MODULE_NAME,
                        action="get_current_prices",
                        symbol=symbol,
                        raw_price=raw_price,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    )
                    raise DataProviderError(
                        error_msg,
                        context={
                            "symbol": symbol,
                            "raw_price": raw_price,
                            "operation": "get_current_prices",
                            "correlation_id": correlation_id,
                        },
                    )

                prices[symbol] = Decimal(str(raw_price))

            logger.debug(
                "Retrieved prices",
                module=MODULE_NAME,
                action="get_current_prices",
                symbol_count=len(prices),
                symbols=sorted(prices.keys()),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            return prices

        except DataProviderError:
            # Re-raise our own exceptions
            raise
        except (AttributeError, KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to retrieve prices",
                module=MODULE_NAME,
                action="get_current_prices",
                error_type=e.__class__.__name__,
                error_message=str(e),
                symbols=valid_symbols,
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            raise DataProviderError(
                f"Failed to retrieve prices: {e}",
                context={
                    "operation": "get_current_prices",
                    "symbols": valid_symbols,
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            ) from e

    def get_account_cash(
        self,
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> Decimal:
        """Get current cash balance.

        Returns the cash available for trading from the broker account.

        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID linking to triggering event

        Returns:
            Cash balance as Decimal. May be negative if account is in margin call.

        Raises:
            DataProviderError: If account information cannot be retrieved,
                account data is malformed, or cash field is missing.

        Pre-conditions:
            - AlpacaManager must be authenticated and connected

        Post-conditions:
            - Returns a Decimal value (may be negative for margin accounts)

        Thread-safety:
            Depends on AlpacaManager thread-safety

        """
        logger.debug(
            "Fetching account cash balance",
            module=MODULE_NAME,
            action="get_account_cash",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        try:
            account_info = self._alpaca_manager.get_account()
            if not account_info:
                error_msg = "Account information unavailable"
                logger.error(
                    error_msg,
                    module=MODULE_NAME,
                    action="get_account_cash",
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                )
                raise DataProviderError(
                    error_msg,
                    context={
                        "operation": "get_account_cash",
                        "correlation_id": correlation_id,
                    },
                )

            # account_info is now dict[str, Any], so access cash key directly
            cash_value = account_info.get("cash")
            if cash_value is None:
                error_msg = "Cash information not available in account"
                logger.error(
                    error_msg,
                    module=MODULE_NAME,
                    action="get_account_cash",
                    account_keys=list(account_info.keys()),
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                )
                raise DataProviderError(
                    error_msg,
                    context={
                        "operation": "get_account_cash",
                        "available_keys": list(account_info.keys()),
                        "correlation_id": correlation_id,
                    },
                )

            cash = Decimal(str(cash_value))

            logger.debug(
                "Retrieved cash balance",
                module=MODULE_NAME,
                action="get_account_cash",
                cash_balance_usd=str(cash),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            return cash

        except DataProviderError:
            # Re-raise our own exceptions
            raise
        except (AttributeError, KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to retrieve cash balance",
                module=MODULE_NAME,
                action="get_account_cash",
                error_type=e.__class__.__name__,
                error_message=str(e),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            raise DataProviderError(
                f"Failed to retrieve cash balance: {e}",
                context={
                    "operation": "get_account_cash",
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            ) from e

    def get_account_info(
        self,
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> AccountInfo:
        """Get complete account information including margin data.

        Returns cash, buying power, equity, and margin information for
        proper capital management in both cash and margin accounts.

        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID linking to triggering event

        Returns:
            AccountInfo with all available capital and margin fields.
            Margin fields may be None if not available from broker.

        Raises:
            DataProviderError: If account information cannot be retrieved
                or cash field is missing (cash is required).

        Pre-conditions:
            - AlpacaManager must be authenticated and connected

        Post-conditions:
            - Returns AccountInfo with at least cash field populated
            - Margin fields are None if not available from broker

        Thread-safety:
            Depends on AlpacaManager thread-safety

        """
        logger.debug(
            "Fetching complete account information",
            module=MODULE_NAME,
            action="get_account_info",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        try:
            account_data = self._alpaca_manager.get_account()
            if not account_data:
                error_msg = "Account information unavailable"
                logger.error(
                    error_msg,
                    module=MODULE_NAME,
                    action="get_account_info",
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                )
                raise DataProviderError(
                    error_msg,
                    context={
                        "operation": "get_account_info",
                        "correlation_id": correlation_id,
                    },
                )

            # Cash is required
            cash_value = account_data.get("cash")
            if cash_value is None:
                error_msg = "Cash information not available in account"
                logger.error(
                    error_msg,
                    module=MODULE_NAME,
                    action="get_account_info",
                    account_keys=list(account_data.keys()),
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                )
                raise DataProviderError(
                    error_msg,
                    context={
                        "operation": "get_account_info",
                        "available_keys": list(account_data.keys()),
                        "correlation_id": correlation_id,
                    },
                )

            cash = Decimal(str(cash_value))

            # Extract optional margin fields with safe conversion
            def _safe_decimal(value: object) -> Decimal | None:
                if value is None:
                    return None
                try:
                    return Decimal(str(value))
                except (ValueError, TypeError):
                    return None

            buying_power = _safe_decimal(account_data.get("buying_power"))
            equity = _safe_decimal(account_data.get("equity"))
            portfolio_value = _safe_decimal(account_data.get("portfolio_value"))
            initial_margin = _safe_decimal(account_data.get("initial_margin"))
            maintenance_margin = _safe_decimal(account_data.get("maintenance_margin"))

            account_info = AccountInfo(
                cash=cash,
                buying_power=buying_power,
                equity=equity,
                portfolio_value=portfolio_value,
                initial_margin=initial_margin,
                maintenance_margin=maintenance_margin,
            )

            logger.debug(
                "Retrieved complete account information",
                module=MODULE_NAME,
                action="get_account_info",
                cash=str(cash),
                buying_power=str(buying_power) if buying_power else "N/A",
                equity=str(equity) if equity else "N/A",
                initial_margin=str(initial_margin) if initial_margin else "N/A",
                maintenance_margin=str(maintenance_margin) if maintenance_margin else "N/A",
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

            return account_info

        except DataProviderError:
            # Re-raise our own exceptions
            raise
        except (AttributeError, KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed to retrieve account information",
                module=MODULE_NAME,
                action="get_account_info",
                error_type=e.__class__.__name__,
                error_message=str(e),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            raise DataProviderError(
                f"Failed to retrieve account information: {e}",
                context={
                    "operation": "get_account_info",
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            ) from e

    def liquidate_all_positions(
        self,
        *,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> bool:
        """Liquidate all positions by calling Alpaca's close_all_positions API.

        WARNING: This operation is NOT idempotent. Calling it multiple times
        may attempt to close the same positions repeatedly (though the broker
        should handle this gracefully).

        Args:
            correlation_id: Optional correlation ID for distributed tracing
            causation_id: Optional causation ID linking to triggering event

        Returns:
            True if liquidation was successful (positions were closed),
            False if no positions were closed or liquidation failed.

        Note:
            Unlike other methods in this adapter, this method returns False on
            failure instead of raising an exception. This is intentional to allow
            the caller to handle liquidation failures gracefully (e.g., during
            negative cash balance recovery).

        Side effects:
            - Closes all open positions in the account
            - Cancels all open orders (cancel_orders=True)
            - May result in realized gains/losses
            - Account state will be modified

        Pre-conditions:
            - AlpacaManager must be authenticated and connected
            - Market should be open for immediate execution

        Post-conditions:
            - On success: All positions are closed or closing
            - On failure: Some positions may be partially closed

        Thread-safety:
            Depends on AlpacaManager thread-safety
            NOT safe to call concurrently from multiple threads

        """
        logger.warning(
            "Attempting to liquidate all positions due to negative cash balance",
            module=MODULE_NAME,
            action="liquidate_all_positions",
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

        try:
            result = self._alpaca_manager.close_all_positions(cancel_orders=True)

            if result:
                logger.info(
                    "Successfully liquidated positions",
                    module=MODULE_NAME,
                    action="liquidate_all_positions",
                    positions_closed=len(result),
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                )
                return True

            logger.warning(
                "No positions were liquidated (account may already be empty)",
                module=MODULE_NAME,
                action="liquidate_all_positions",
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            return False

        except Exception as e:
            # Note: We catch generic Exception here intentionally because
            # liquidation is a recovery operation and we don't want to fail
            # the caller with an exception. The caller checks the return value.
            logger.error(
                "Failed to liquidate all positions",
                module=MODULE_NAME,
                action="liquidate_all_positions",
                error_type=e.__class__.__name__,
                error_message=str(e),
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            return False
