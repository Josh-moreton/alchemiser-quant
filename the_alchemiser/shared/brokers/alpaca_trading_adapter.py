"""Business Unit: shared | Status: current.

Alpaca trading operations adapter implementing TradingRepository protocol.

This adapter focuses specifically on trading operations including order placement,
cancellation, position management, and connection validation. It delegates to
the Alpaca TradingClient for all trading-related operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.models import TradeAccount
from alpaca.trading.requests import GetOrdersRequest

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_client
from the_alchemiser.shared.protocols.repository import TradingRepository

if TYPE_CHECKING:
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

    from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO

logger = logging.getLogger(__name__)


class AlpacaTradingAdapter(TradingRepository):
    """Alpaca trading operations adapter.
    
    Implements the TradingRepository protocol for all trading-related operations
    including order placement, cancellation, position queries, and account access.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
    ) -> None:
        """Initialize the trading adapter.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        
        # Initialize trading client
        self._trading_client = create_trading_client(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        
        logger.info(f"AlpacaTradingAdapter initialized - Paper: {paper}")

    @property
    def is_paper_trading(self) -> bool:
        """Check if this is paper trading."""
        return self._paper

    @property
    def trading_client(self) -> TradingClient:
        """Return underlying trading client for backward compatibility."""
        return self._trading_client

    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity."""
        try:
            positions = self._trading_client.get_all_positions()
            result = {}
            
            for pos in positions:
                symbol = self._extract_position_symbol(pos)
                quantity = self._extract_position_quantity(pos)
                
                if symbol is not None and quantity is not None and quantity != 0.0:
                    result[symbol] = quantity
                    
            logger.debug(f"Retrieved {len(result)} non-zero positions")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get positions dict: {e}")
            return {}

    def _extract_position_symbol(self, pos: Any) -> str | None:
        """Extract symbol from position object."""
        try:
            if hasattr(pos, "symbol"):
                return str(pos.symbol)
            elif isinstance(pos, dict) and "symbol" in pos:
                return str(pos["symbol"])
            return None
        except Exception:
            return None

    def _extract_position_quantity(self, pos: Any) -> float | None:
        """Extract quantity from position object."""
        try:
            if hasattr(pos, "qty"):
                qty_raw = getattr(pos, "qty", None)
                return float(qty_raw) if qty_raw is not None else None
            elif isinstance(pos, dict) and "qty" in pos:
                qty_raw = pos["qty"]
                return float(qty_raw) if qty_raw is not None else None
            return None
        except (ValueError, TypeError):
            return None

    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dictionary."""
        account_obj = self._get_account_object()
        if not account_obj:
            return None
            
        try:
            # Try to get dict representation
            data = account_obj.__dict__ if hasattr(account_obj, "__dict__") else None
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.debug(f"Falling back to manual account dict conversion: {exc}")
            
        # Fallback: build dict from known attributes
        return {
            "id": getattr(account_obj, "id", None),
            "account_number": getattr(account_obj, "account_number", None),
            "status": getattr(account_obj, "status", None),
            "currency": getattr(account_obj, "currency", None),
            "buying_power": getattr(account_obj, "buying_power", None),
            "cash": getattr(account_obj, "cash", None),
            "portfolio_value": getattr(account_obj, "portfolio_value", None),
            "equity": getattr(account_obj, "equity", None),
        }

    def _get_account_object(self) -> TradeAccount | None:
        """Get account object for internal use."""
        try:
            account = self._trading_client.get_account()
            logger.debug("Successfully retrieved account information")
            return account if isinstance(account, TradeAccount) else None
        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        try:
            account = self._get_account_object()
            if account and hasattr(account, "buying_power"):
                bp_raw = getattr(account, "buying_power", None)
                return float(bp_raw) if bp_raw is not None else None
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            return None

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        try:
            account = self._get_account_object()
            if account and hasattr(account, "portfolio_value"):
                pv_raw = getattr(account, "portfolio_value", None)
                return float(pv_raw) if pv_raw is not None else None
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            return None

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        from the_alchemiser.shared.brokers.alpaca_mappers import (
            create_failed_order_dto,
            create_success_order_dto,
            extract_action_from_request,
        )
        
        try:
            order = self._trading_client.submit_order(order_request)
            action = extract_action_from_request(order_request)
            return create_success_order_dto(order, action)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            symbol = getattr(order_request, "symbol", "unknown")
            action = extract_action_from_request(order_request)
            return create_failed_order_dto(symbol, action, str(e))

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrderDTO:
        """Place a market order with validation and execution result return."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest
        
        from the_alchemiser.shared.brokers.alpaca_mappers import create_error_dto
        
        try:
            # Validation
            normalized_symbol, side_normalized = self._validate_market_order_params(
                symbol, side, qty, notional
            )

            # Adjust quantity for complete exits
            final_qty = self._adjust_quantity_for_complete_exit(
                normalized_symbol,
                side_normalized,
                qty,
                is_complete_exit=is_complete_exit,
            )

            # Create order request
            order_request = MarketOrderRequest(
                symbol=normalized_symbol,
                qty=final_qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            # Use the place_order method that returns ExecutedOrderDTO
            return self.place_order(order_request)

        except ValueError as e:
            logger.error(f"Invalid order parameters: {e}")
            return create_error_dto(symbol, side, str(e), qty or 0.0)
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return create_error_dto(symbol, side, str(e), qty or 0.0)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(f"Successfully cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol."""
        try:
            request = GetOrdersRequest(
                status=QueryOrderStatus.OPEN, 
                symbols=[symbol] if symbol else None
            )
            open_orders = self._trading_client.get_orders(request)
            
            success_count = 0
            total_count = len(open_orders)
            
            for order in open_orders:
                try:
                    order_id = getattr(order, "id", None)
                    if order_id:
                        self._trading_client.cancel_order_by_id(str(order_id))
                        success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to cancel individual order: {e}")
                    
            logger.info(f"Cancelled {success_count}/{total_count} orders" + 
                       (f" for {symbol}" if symbol else ""))
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API."""
        try:
            close_order = self._trading_client.close_position(symbol)
            
            if close_order and hasattr(close_order, "id"):
                order_id = str(close_order.id)
                logger.info(f"Successfully liquidated position {symbol}, order ID: {order_id}")
                return order_id
            else:
                logger.warning(f"Liquidation order for {symbol} returned no order ID")
                return None
                
        except Exception as e:
            logger.error(f"Failed to liquidate position {symbol}: {e}")
            return None

    def validate_connection(self) -> bool:
        """Validate connection to trading service."""
        try:
            account = self._get_account_object()
            is_valid = account is not None
            logger.debug(f"Connection validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            return is_valid
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def _validate_market_order_params(
        self, symbol: str, side: str, qty: float | None, notional: float | None
    ) -> tuple[str, str]:
        """Validate market order parameters."""
        # Normalize symbol
        normalized_symbol = symbol.upper().strip()
        if not normalized_symbol:
            raise ValueError("Symbol cannot be empty")

        # Normalize side
        side_normalized = side.lower().strip()
        if side_normalized not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        # Validate qty/notional exclusivity
        if qty is not None and notional is not None:
            raise ValueError("Cannot specify both qty and notional")
        if qty is None and notional is None:
            raise ValueError("Must specify either qty or notional")

        # Validate values are positive
        if qty is not None and qty <= 0:
            raise ValueError(f"Quantity must be positive, got: {qty}")
        if notional is not None and notional <= 0:
            raise ValueError(f"Notional must be positive, got: {notional}")

        return normalized_symbol, side_normalized

    def _adjust_quantity_for_complete_exit(
        self,
        symbol: str,
        side: str,
        qty: float | None,
        *,
        is_complete_exit: bool = False,
    ) -> float | None:
        """Adjust quantity for complete position exits."""
        if not is_complete_exit or side != "sell" or qty is None:
            return qty

        try:
            # Get current position
            position = self._trading_client.get_open_position(symbol)
            if position:
                available_qty = float(getattr(position, "qty", 0))
                if available_qty > 0:
                    logger.info(
                        f"Complete exit: using available quantity {available_qty} "
                        f"instead of requested {qty}"
                    )
                    return available_qty
        except Exception as e:
            logger.warning(f"Could not get position for complete exit: {e}")

        return qty