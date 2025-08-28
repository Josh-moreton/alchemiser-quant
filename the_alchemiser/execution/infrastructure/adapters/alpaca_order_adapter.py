"""Business Unit: order execution/placement | Status: current.

Alpaca order adapter for execution context.

Handles order placement, cancellation, and execution operations via Alpaca API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.application.mapping.alpaca_dto_mapping import (
    alpaca_order_to_execution_result,
    create_error_execution_result,
)
from the_alchemiser.domain.interfaces import TradingRepository
from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO
from the_alchemiser.shared_kernel.infrastructure.base_alpaca_adapter import BaseAlpacaAdapter

if TYPE_CHECKING:
    from the_alchemiser.interfaces.schemas.orders import RawOrderEnvelope

logger = logging.getLogger(__name__)


class AlpacaOrderAdapter(BaseAlpacaAdapter, TradingRepository):
    """Alpaca adapter for order execution operations."""

    def place_order(self, order_request: Any) -> RawOrderEnvelope:
        """Place an order using the raw order request.

        Args:
            order_request: Order request object

        Returns:
            RawOrderEnvelope with order details

        """
        try:
            client = self.get_trading_client()
            order = client.submit_order(order_request)

            from the_alchemiser.interfaces.schemas.orders import RawOrderEnvelope

            return RawOrderEnvelope(
                order_id=order.id,
                symbol=order.symbol,
                quantity=float(order.qty),
                side=order.side.value,
                order_type=order.order_type.value,
                status=order.status.value,
                raw_order=order,
            )
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            raise

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResultDTO:
        """Get execution result for an order.

        Args:
            order_id: Order ID to check

        Returns:
            OrderExecutionResultDTO with execution details

        """
        try:
            client = self.get_trading_client()
            order = client.get_order_by_id(order_id)
            return alpaca_order_to_execution_result(order)
        except Exception as e:
            self.logger.error(f"Failed to get order execution result for {order_id}: {e}")
            return create_error_execution_result(order_id, str(e))

    def place_market_order(
        self,
        symbol: str,
        quantity: float | None = None,
        side: str = "buy",
        time_in_force: str = "day",
        notional: float | None = None,
    ) -> str:
        """Place a market order.

        Args:
            symbol: Symbol to trade
            quantity: Number of shares (mutually exclusive with notional)
            side: Order side ('buy' or 'sell')
            time_in_force: Time in force ('day', 'gtc', etc.)
            notional: Dollar amount (mutually exclusive with quantity)

        Returns:
            Order ID

        """
        try:
            client = self.get_trading_client()

            # Convert side to Alpaca enum
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            # Convert time in force
            tif_map = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK,
            }
            tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)

            # Create order request
            if notional is not None:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=order_side,
                    time_in_force=tif,
                )
            else:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=tif,
                )

            order = client.submit_order(order_request)
            self.logger.info(f"Market order placed: {order.id} for {symbol}")
            return order.id

        except Exception as e:
            self.logger.error(f"Failed to place market order for {symbol}: {e}")
            raise

    def place_limit_order(
        self,
        symbol: str,
        quantity: float | None = None,
        side: str = "buy",
        limit_price: float = 0.0,
        time_in_force: str = "day",
        notional: float | None = None,
    ) -> str:
        """Place a limit order.

        Args:
            symbol: Symbol to trade
            quantity: Number of shares (mutually exclusive with notional)
            side: Order side ('buy' or 'sell')
            limit_price: Limit price for the order
            time_in_force: Time in force ('day', 'gtc', etc.)
            notional: Dollar amount (mutually exclusive with quantity)

        Returns:
            Order ID

        """
        try:
            client = self.get_trading_client()

            # Convert side to Alpaca enum
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            # Convert time in force
            tif_map = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK,
            }
            tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)

            # Create order request
            if notional is not None:
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    notional=notional,
                    side=order_side,
                    time_in_force=tif,
                    limit_price=limit_price,
                )
            else:
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=tif,
                    limit_price=limit_price,
                )

            order = client.submit_order(order_request)
            self.logger.info(f"Limit order placed: {order.id} for {symbol} at ${limit_price}")
            return order.id

        except Exception as e:
            self.logger.error(f"Failed to place limit order for {symbol}: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful

        """
        try:
            client = self.get_trading_client()
            client.cancel_order_by_id(order_id)
            self.logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders with optional status filter.

        Args:
            status: Optional status filter ('open', 'closed', etc.)

        Returns:
            List of order objects

        """
        try:
            client = self.get_trading_client()

            if status:
                from alpaca.trading.enums import QueryOrderStatus

                status_map = {
                    "open": QueryOrderStatus.OPEN,
                    "closed": QueryOrderStatus.CLOSED,
                    "all": QueryOrderStatus.ALL,
                }
                query_status = status_map.get(status.lower(), QueryOrderStatus.ALL)
                orders = client.get_orders(status=query_status)
            else:
                orders = client.get_orders()

            return list(orders)
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []

    def get_open_orders(self) -> list[Any]:
        """Get all open orders.

        Returns:
            List of open order objects

        """
        return self.get_orders("open")

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders for a symbol or all orders.

        Args:
            symbol: Optional symbol to filter orders

        Returns:
            True if cancellation successful

        """
        try:
            client = self.get_trading_client()

            if symbol:
                open_orders = self.get_open_orders()
                symbol_orders = [order for order in open_orders if order.symbol == symbol]

                for order in symbol_orders:
                    try:
                        client.cancel_order_by_id(order.id)
                    except Exception as e:
                        self.logger.warning(f"Failed to cancel order {order.id}: {e}")

                self.logger.info(f"Cancelled {len(symbol_orders)} orders for {symbol}")
            else:
                client.cancel_orders()
                self.logger.info("Cancelled all open orders")

            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel orders: {e}")
            return False

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate a position.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None otherwise

        """
        try:
            client = self.get_trading_client()

            # Get current position
            try:
                position = client.get_open_position(symbol)
            except Exception:
                self.logger.warning(f"No position found for {symbol}")
                return None

            if not position or float(position.qty) == 0:
                self.logger.warning(f"No position to liquidate for {symbol}")
                return None

            # Place market order to close position
            quantity = abs(float(position.qty))
            side = "sell" if float(position.qty) > 0 else "buy"

            order_id = self.place_market_order(
                symbol=symbol,
                quantity=quantity,
                side=side,
                time_in_force="day",
            )

            self.logger.info(f"Position liquidated for {symbol}: {order_id}")
            return order_id

        except Exception as e:
            self.logger.error(f"Failed to liquidate position for {symbol}: {e}")
            return None

    def get_order_status(self, order_id: str) -> dict[str, Any]:
        """Get status for a specific order.

        Args:
            order_id: Order ID to check

        Returns:
            Dictionary with order status information

        """
        try:
            client = self.get_trading_client()
            order = client.get_order_by_id(order_id)

            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "quantity": float(order.qty),
                "side": order.side.value,
                "order_type": order.order_type.value,
                "status": order.status.value,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price)
                if order.filled_avg_price
                else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            }
        except Exception as e:
            self.logger.error(f"Failed to get order status for {order_id}: {e}")
            return {"error": str(e)}

    # Stubs for TradingRepository interface compatibility (implemented in other adapters)
    def get_account(self) -> Any:
        """Get account information (implemented in portfolio adapter)."""
        raise NotImplementedError("Account operations handled by portfolio adapter")

    def get_positions(self) -> list[Any]:
        """Get positions (implemented in portfolio adapter)."""
        raise NotImplementedError("Position operations handled by portfolio adapter")

    def get_positions_dict(self) -> dict[str, float]:
        """Get positions as dictionary (implemented in portfolio adapter)."""
        raise NotImplementedError("Position operations handled by portfolio adapter")
