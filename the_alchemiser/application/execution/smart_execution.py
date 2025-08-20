#!/usr/bin/env python3
"""
Smart Execution Engine with Professional Order Strategy.

This module provides sophisticated order execution using the Better Orders strategy:
- Aggressive marketable limits (ask+1¢ for buys, bid-1¢ for sells)
- Market timing logic for 9:30-9:35 ET execution
- Fast 2-3 second timeouts with re-pegging
- Designed for leveraged ETFs and high-volume trading
- Market order fallback for execution certainty

Refactored to use composition instead of thin proxy methods.
Focuses on execution strategy logic while delegating order placement to specialized components.
"""

import logging
import time
from typing import Any, Protocol

from alpaca.trading.enums import OrderSide

from the_alchemiser.services.errors.exceptions import (
    DataProviderError,
    OrderExecutionError,
    TradingClientError,
)


class OrderExecutor(Protocol):
    """Protocol for order execution components."""

    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        qty: float | None = None,
        notional: float | None = None,
    ) -> str | None:
        """Place a market order."""
        ...

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order."""
        ...

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate a position."""
        ...

    def get_current_positions(self) -> dict[str, float]:
        """Get current positions."""
        ...

    def place_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> str | None:
        """Place a limit order."""
        ...

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> dict[str, str]:
        """Wait for order completion."""
        ...

    @property
    def trading_client(self) -> Any:  # Backward compatibility
        """Access to trading client for market hours and order queries."""
        ...

    @property
    def data_provider(self) -> "DataProvider":
        """Access to data provider for quotes and prices."""
        ...


class DataProvider(Protocol):
    """Protocol for data provider components."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        ...

    def get_latest_quote(
        self, symbol: str
    ) -> tuple[float, float] | None:  # Phase 5: precise tuple typing for bid/ask
        """Get latest quote for a symbol."""
        ...


def is_market_open(trading_client: Any) -> bool:
    """Check if the market is currently open."""
    try:
        clock = trading_client.get_clock()
        return getattr(clock, "is_open", False)
    except TradingClientError:
        # If we can't get market status, assume closed for safety
        return False
    except Exception:
        # For any unexpected errors, assume market is closed for safety
        return False


class SmartExecution:
    """
    Professional execution engine using Better Orders strategy.

    Focuses on sophisticated execution logic while delegating actual order placement
    to injected order executor. Uses composition over inheritance for better testability
    and separation of concerns.
    """

    def __init__(
        self,
        order_executor: "OrderExecutor",
        data_provider: "DataProvider",
        ignore_market_hours: bool = False,
        config: Any = None,
    ) -> None:
        """Initialize with dependency injection for execution and data access."""

        self.config = config or {}
        # Store dependencies for composition
        self._order_executor = order_executor
        self._data_provider = data_provider
        # Backward compatibility accessor used by is_market_open()
        self._trading_client = getattr(order_executor, "trading_client", None)
        self.ignore_market_hours = ignore_market_hours

    def execute_safe_sell(self, symbol: str, target_qty: float) -> str | None:
        """
        Execute a safe sell using the configured order executor.

        Focuses on safe selling logic while delegating actual order placement.
        """
        return self._order_executor.place_smart_sell_order(symbol, target_qty)

    def execute_liquidation(self, symbol: str) -> str | None:
        """Execute full position liquidation using the configured order executor."""
        return self._order_executor.liquidate_position(symbol)

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
        notional: float | None = None,
        max_slippage_bps: float | None = None,
    ) -> str | None:
        """
        Place order using professional Better Orders execution strategy.

        Implements the 5-step execution ladder:
        1. Market timing assessment (9:30-9:35 ET logic)
        2. Aggressive marketable limit (ask+1¢ for buys, bid-1¢ for sells)
        3. Re-peg sequence (max 2 attempts, 2-3s timeouts)
        4. Market order fallback for execution certainty

        Args:
            symbol: Stock symbol
            qty: Quantity to trade (shares)
            side: OrderSide.BUY or OrderSide.SELL
            notional: For BUY orders, dollar amount instead of shares
            max_slippage_bps: Maximum slippage tolerance in basis points

        Returns:
            Order ID if successful, None otherwise
        """
        from rich.console import Console

        from the_alchemiser.application.execution.spread_assessment import SpreadAssessment
        from the_alchemiser.domain.math.market_timing_utils import MarketOpenTimingEngine

        console = Console()
        timing_engine = MarketOpenTimingEngine()
        spread_assessor = SpreadAssessment(self._data_provider)

        # Handle notional orders for BUY by converting to quantity
        if side == OrderSide.BUY and notional is not None:
            try:
                current_price = self._data_provider.get_current_price(symbol)
                if current_price and current_price > 0:
                    # Calculate max quantity we can afford, round down, scale to 99%
                    raw_qty = notional / current_price
                    rounded_qty = int(raw_qty * 1e6) / 1e6  # Round down to 6 decimals
                    qty = rounded_qty * 0.99  # Scale to 99% to avoid buying power issues
                else:
                    console.print(
                        f"[yellow]Invalid price for {symbol}, using market order[/yellow]"
                    )
                    return self._order_executor.place_market_order(symbol, side, notional=notional)

                if qty <= 0:
                    console.print(
                        f"[yellow]Calculated quantity too small for {symbol}, using market order[/yellow]"
                    )
                    return self._order_executor.place_market_order(symbol, side, notional=notional)

            except DataProviderError:
                console.print(
                    f"[yellow]Price unavailable for {symbol}, using market order[/yellow]"
                )
                return self._order_executor.place_market_order(symbol, side, notional=notional)

        # Step 1: Market timing and spread assessment
        strategy = timing_engine.get_execution_strategy()
        console.print(f"[cyan]Execution strategy: {strategy.value}[/cyan]")

        # Get current bid/ask
        try:
            quote = self._order_executor.data_provider.get_latest_quote(symbol)
            if not quote or len(quote) < 2:
                console.print("[yellow]No valid quote data, using market order[/yellow]")
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            bid, ask = float(quote[0]), float(quote[1])

            # Check if quote is invalid (fallback zeros)
            if bid <= 0 or ask <= 0:
                console.print("[yellow]Invalid quote data, using market order[/yellow]")
                return self._order_executor.place_market_order(symbol, side, qty=qty)
            spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)

            console.print(
                f"[dim]Current spread: {spread_analysis.spread_cents:.1f}¢ ({spread_analysis.spread_quality.value})[/dim]"
            )

            # Check if we should wait for spreads to normalize
            if not timing_engine.should_execute_immediately(spread_analysis.spread_cents, strategy):
                wait_time = timing_engine.get_wait_time_seconds(
                    strategy, spread_analysis.spread_cents
                )
                console.print(
                    f"[yellow]Wide spread detected, waiting {wait_time}s for normalization[/yellow]"
                )
                time.sleep(wait_time)

                # Re-get quote after waiting
                quote = self._order_executor.data_provider.get_latest_quote(symbol)
                if not quote or len(quote) < 2:
                    console.print("[yellow]No valid quote after wait, using market order[/yellow]")
                    return self._order_executor.place_market_order(symbol, side, qty=qty)
                bid, ask = float(quote[0]), float(quote[1])
                spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
                console.print(f"[dim]Updated spread: {spread_analysis.spread_cents:.1f}¢[/dim]")

            # Step 2 & 3: Aggressive Marketable Limit with Re-pegging
            return self._execute_aggressive_limit_sequence(
                symbol, qty, side, bid, ask, strategy, console
            )

        except OrderExecutionError as e:
            logging.error(f"Order execution error in Better Orders execution for {symbol}: {e}")
            # Step 4: Market order fallback
            console.print("[yellow]Order execution failed, falling back to market order[/yellow]")
            return self._order_executor.place_market_order(symbol, side, qty=qty)
        except DataProviderError as e:
            logging.error(f"Data provider error in Better Orders execution for {symbol}: {e}")
            # Step 4: Market order fallback
            console.print("[yellow]Data provider error, falling back to market order[/yellow]")
            return self._order_executor.place_market_order(symbol, side, qty=qty)
        except Exception as e:
            logging.error(f"Unexpected error in Better Orders execution for {symbol}: {e}")
            # Step 4: Market order fallback
            console.print("[yellow]Unexpected error, falling back to market order[/yellow]")
            return self._order_executor.place_market_order(symbol, side, qty=qty)

    def wait_for_settlement(
        self,
        sell_orders: list[dict[str, Any]],
        max_wait_time: int = 60,
        poll_interval: float = 2.0,
    ) -> bool:
        """
        Wait for order settlement using polling-based tracking.
        
        This is a temporary implementation using legacy polling logic.
        TODO: Implement proper OrderSettlementTracker with type-safe tracking
        and WebSocket-based monitoring for real-time settlement detection.
        
        Args:
            sell_orders: List of order dictionaries to monitor
            max_wait_time: Maximum time to wait in seconds
            poll_interval: Polling interval (currently unused in polling implementation)
            
        Returns:
            bool: True if all orders settle successfully, False if any fail or timeout
            
        Note: This method can return False when settlement fails, preventing
        masking of real settlement failures.
        """
        if not sell_orders:
            return True

        # TODO: Replace with proper OrderSettlementTracker implementation
        # Current implementation uses polling-based settlement detection

        # Extract only valid string order IDs
        order_ids: list[str] = []
        for order in sell_orders:
            # Try both 'id' and 'order_id' keys for compatibility
            order_id = order.get("id") or order.get("order_id")
            if order_id is not None and isinstance(order_id, str):
                order_ids.append(order_id)

        # If we had orders but no valid order IDs, that's a failure
        if not order_ids:
            logging.warning("No valid order IDs found in settlement data")
            return False

        # Quick pre-check: see if orders are already filled before starting websocket monitoring
        already_completed = {}
        remaining_order_ids = []

        for order_id in order_ids:
            try:
                order_obj: Any = self._order_executor.trading_client.get_order_by_id(
                    order_id
                )  # TODO: Phase 5 - Migrate to AlpacaOrderObject
                status = str(getattr(order_obj, "status", "unknown")).lower()
                if "orderstatus." in status:
                    actual_status = status.split(".")[-1]
                else:
                    actual_status = status

                if actual_status in ["filled", "canceled", "rejected", "expired"]:
                    logging.info(
                        f"✅ Order {order_id} already settled with status: {actual_status}"
                    )
                    already_completed[order_id] = actual_status
                else:
                    remaining_order_ids.append(order_id)
            except (AttributeError, ValueError) as e:
                logging.warning(f"❌ Error parsing order {order_id} status data: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check
            except TradingClientError as e:
                logging.warning(f"❌ Trading client error checking order {order_id} status: {e}")
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check
            except Exception as e:
                logging.warning(
                    f"❌ Unexpected error checking order {order_id} pre-settlement status: {e}"
                )
                remaining_order_ids.append(order_id)  # Include it in monitoring if we can't check

        # If all orders are already completed, no need to wait
        if not remaining_order_ids:
            logging.info(
                f"🎯 All {len(order_ids)} orders already settled, skipping settlement monitoring"
            )
            return True

        # Only monitor orders that aren't already completed
        logging.info(
            f"📊 Settlement check: {len(already_completed)} already completed, {len(remaining_order_ids)} need monitoring"
        )

        # Wait for order settlement
        completion_statuses = self._order_executor.wait_for_order_completion(
            remaining_order_ids, max_wait_time
        )

        # Combine pre-completed orders with newly completed ones
        all_completion_statuses = {**already_completed, **completion_statuses}

        # Log the completion statuses for debugging
        logging.info(f"Order completion statuses: {all_completion_statuses}")

        # Consider orders settled if they're filled, canceled, or rejected
        # Handle both enum values and string representations
        settled_count = sum(
            1
            for status in all_completion_statuses.values()
            if status in ["filled", "canceled", "rejected", "expired"]
            or str(status).lower() in ["filled", "canceled", "rejected", "expired"]
            or status
            in [
                "OrderStatus.FILLED",
                "OrderStatus.CANCELED",
                "OrderStatus.REJECTED",
                "OrderStatus.EXPIRED",
            ]
        )

        success = settled_count == len(order_ids)
        if success:
            pass  # All orders settled successfully
        else:
            logging.warning(f"Only {settled_count}/{len(order_ids)} orders settled")

        return success

    def calculate_dynamic_limit_price(
        self,
        side: OrderSide,
        bid: float,
        ask: float,
        step: int = 1,
        tick_size: float = 0.01,
        max_steps: int = 5,
    ) -> float:
        """
        Calculate a dynamic limit price based on the bid-ask spread and step.

        Test expects:
        - BUY: bid=99.0, ask=101.0, step=1, tick_size=0.2, max_steps=3 -> 100.2
        - SELL: bid=99.0, ask=101.0, step=2, tick_size=0.5, max_steps=3 -> 99.0

        Args:
            side: OrderSide.BUY or OrderSide.SELL
            bid: Current bid price
            ask: Current ask price
            step: Step number (1-based)
            tick_size: Minimum price increment
            max_steps: Maximum number of steps

        Returns:
            Calculated limit price
        """
        mid_price = (bid + ask) / 2.0

        if side == OrderSide.BUY:
            # For buy orders, step toward ask from mid
            price = mid_price + (step * tick_size)
        else:
            # For sell orders, step toward bid from mid
            price = mid_price - (step * tick_size)

        # Round to nearest tick
        return round(price / tick_size) * tick_size

    def _execute_aggressive_limit_sequence(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,
        bid: float,
        ask: float,
        strategy: Any,
        console: Any,
    ) -> str | None:
        """
        Execute the aggressive marketable limit sequence with re-pegging.

        Step 2: Aggressive marketable limit (ask+1 tick / bid-1 tick)
        Step 3: Re-peg 1-2 times (2-3 second timeouts)
        Step 4: Market order fallback
        """
        from the_alchemiser.domain.math.market_timing_utils import ExecutionStrategy

        # Determine timeout based on strategy and ETF speed
        if strategy == ExecutionStrategy.WAIT_FOR_SPREADS:
            timeout_seconds = 2.0  # Fast execution at market open
        else:
            timeout_seconds = 3.0  # Slightly longer for normal times

        max_repegs = 2  # Maximum 2 re-peg attempts

        for attempt in range(max_repegs + 1):
            # Calculate aggressive marketable limit price
            if side == OrderSide.BUY:
                # Buy: ask + 1 tick (ask + 1¢)
                limit_price = ask + 0.01
                direction = "above ask"
            else:
                # Sell: bid - 1 tick (bid - 1¢)
                limit_price = bid - 0.01
                direction = "below bid"

            attempt_label = "Initial order" if attempt == 0 else f"Re-peg #{attempt}"
            console.print(
                f"[cyan]{attempt_label}: {side.value} {symbol} @ ${limit_price:.2f} ({direction})[/cyan]"
            )

            # Place aggressive marketable limit
            order_id = self._order_executor.place_limit_order(symbol, qty, side, limit_price)
            if not order_id:
                console.print("[red]Failed to place limit order[/red]")
                continue

            # Wait for fill with fast timeout (2-3 seconds max)
            order_results = self._order_executor.wait_for_order_completion(
                [order_id], max_wait_seconds=int(timeout_seconds)
            )

            final_status = order_results.get(order_id, "").lower()
            if "filled" in final_status:
                console.print(
                    f"[green]✅ {side.value} {symbol} filled @ ${limit_price:.2f} ({attempt_label})[/green]"
                )
                return order_id

            # Order not filled - prepare for re-peg if attempts remain
            if attempt < max_repegs:
                console.print(f"[yellow]{attempt_label} not filled, re-pegging...[/yellow]")

                # Get fresh quote for re-peg pricing
                fresh_quote = self._order_executor.data_provider.get_latest_quote(symbol)
                if not fresh_quote or len(fresh_quote) < 2:
                    console.print("[yellow]Invalid fresh quote, using market order[/yellow]")
                    break
                bid, ask = float(fresh_quote[0]), float(fresh_quote[1])

                # Check if fresh quote is invalid (fallback zeros)
                if bid <= 0 or ask <= 0:
                    console.print("[yellow]Invalid fresh quote, using market order[/yellow]")
                    break
            else:
                console.print(f"[yellow]Maximum re-pegs ({max_repegs}) reached[/yellow]")

        # Step 4: Market order fallback
        console.print("[yellow]All limit attempts failed, using market order[/yellow]")
        return self._order_executor.place_market_order(symbol, side, qty=qty)

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order details by order ID from the trading client."""
        try:
            return self._order_executor.trading_client.get_order_by_id(order_id)
        except Exception as e:
            logging.warning(f"Could not retrieve order {order_id}: {e}")
            return None
