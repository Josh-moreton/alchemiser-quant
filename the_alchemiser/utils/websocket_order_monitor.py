#!/usr/bin/env python3
"""
WebSocket Order Monitoring Utilities

This module provides WebSocket-based order completion monitoring for faster
order settlement detection compared to polling-based approaches.
"""

import logging
import time
import threading
from typing import Dict, List, Set
from rich.console import Console


class OrderCompletionMonitor:
    """
    Monitor order completion using WebSocket streams for faster detection.
    
    Provides both streaming and polling methods with automatic fallback.
    """
    
    def __init__(self, trading_client):
        """Initialize with trading client."""
        self.trading_client = trading_client
        self.console = Console()
        
        # WebSocket connection state
        self._websocket_stream = None
        self._websocket_thread = None
    
    def wait_for_order_completion(
        self,
        order_ids: List[str],
        max_wait_seconds: int = 60,
    ) -> Dict[str, str]:
        """Wait for orders to reach a final state."""
        if not order_ids:
            return {}

        api_key = getattr(self.trading_client, "_api_key", None)
        secret_key = getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)

        self.console.print(f"[blue]🔑 API keys available: {has_keys}[/blue]")
        
        if has_keys:
            try:
                if logging.getLogger().level <= logging.DEBUG:
                    self.console.print("[blue]🚀 Attempting WebSocket streaming method for order completion[/blue]")
                return self._wait_for_order_completion_stream(order_ids, max_wait_seconds)
            except Exception as e:  # pragma: no cover - streaming errors fallback
                self.console.print(f"[red]❌ Falling back to polling due to streaming error: {e}[/red]")
                logging.warning(f"❌ Falling back to polling due to streaming error: {e}")

        if logging.getLogger().level <= logging.DEBUG:
            self.console.print("[blue]🔄 Using polling method for order completion[/blue]")
        return self._wait_for_order_completion_polling(order_ids, max_wait_seconds)

    def _wait_for_order_completion_polling(self, order_ids: List[str], max_wait_seconds: int) -> Dict[str, str]:
        """Original polling-based settlement check."""
        logging.info(f"⏳ Waiting for {len(order_ids)} orders to complete via polling...")

        start_time = time.time()
        completed: Dict[str, str] = {}

        while time.time() - start_time < max_wait_seconds and len(completed) < len(order_ids):
            logging.info(f"🔍 Checking {len(order_ids)} orders, {len(completed)} completed so far...")
            
            for order_id in order_ids:
                if order_id in completed:
                    continue

                try:
                    order = self.trading_client.get_order_by_id(order_id)
                    status = getattr(order, "status", "unknown")
                    status_str = str(status)
                    logging.info(f"📋 Order {order_id}: status={status_str}")

                    final_states = [
                        "filled", "canceled", "rejected", "expired",
                        "OrderStatus.FILLED", "OrderStatus.CANCELED", 
                        "OrderStatus.REJECTED", "OrderStatus.EXPIRED",
                    ]
                    
                    if status_str in final_states or str(status).lower() in [
                        "filled", "canceled", "rejected", "expired"
                    ]:
                        completed[order_id] = status_str
                        logging.info(f"✅ Order {order_id}: {status_str}")

                except Exception as e:
                    logging.warning(f"❌ Error checking order {order_id}: {e}")
                    completed[order_id] = "error"

            if len(completed) < len(order_ids):
                # Use shorter polling interval for faster detection
                sleep_time = min(1.0, max_wait_seconds / 10)
                logging.info(f"⏳ {len(order_ids) - len(completed)} orders still pending, waiting {sleep_time}s...")
                time.sleep(sleep_time)

        # Handle timeouts
        if len(completed) < len(order_ids):
            elapsed_time = time.time() - start_time
            logging.warning(f"⏰ Timeout after {elapsed_time:.1f}s: {len(order_ids) - len(completed)} orders did not complete")

        for order_id in order_ids:
            if order_id not in completed:
                completed[order_id] = "timeout"
                logging.warning(f"⏰ Order {order_id}: timeout")

        logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
        return completed

    def _wait_for_order_completion_stream(self, order_ids: List[str], max_wait_seconds: int) -> Dict[str, str]:
        """Use Alpaca's TradingStream to monitor order status."""
        logging.info(f"⏳ Waiting for {len(order_ids)} orders to complete via websocket...")
        logging.debug(f"🔍 Order IDs to monitor: {order_ids}")

        # First, check if any orders are already completed
        completed: Dict[str, str] = {}
        remaining = set(order_ids)
        
        # Quick API check for already completed orders
        for order_id in list(remaining):
            try:
                order = self.trading_client.get_order_by_id(order_id)
                status = str(getattr(order, "status", "")).lower()
                if 'orderstatus.' in status:
                    actual_status = status.split('.')[-1]
                else:
                    actual_status = status
                    
                final_states = {"filled", "canceled", "rejected", "expired"}
                if actual_status in final_states:
                    logging.info(f"✅ Order {order_id} already completed with status: {actual_status}")
                    completed[order_id] = actual_status
                    remaining.remove(order_id)
            except Exception as e:
                logging.warning(f"❌ Error checking initial order status for {order_id}: {e}")
        
        # If all orders are already completed, return immediately
        if not remaining:
            logging.info(f"🎯 All {len(order_ids)} orders already completed, no websocket monitoring needed")
            return completed

        # Set up WebSocket monitoring for remaining orders
        final_states = {"filled", "canceled", "rejected", "expired"}
        stream_stopped = False

        async def on_update(data) -> None:
            nonlocal stream_stopped
            if stream_stopped:
                return
                
            logging.debug(f"📡 WebSocket trade update received: {data}")
            
            order = getattr(data, "order", None)
            if not order:
                return
                
            oid = str(getattr(order, "id", ""))
            status = str(getattr(order, "status", ""))
            
            if oid in remaining:
                logging.debug(f"📋 WebSocket order update: ID={oid}, status={status}")
                
                # Handle both string status and enum status
                status_str = str(status).lower()
                if 'orderstatus.' in status_str:
                    actual_status = status_str.split('.')[-1]
                else:
                    actual_status = status_str
                
                if actual_status in final_states:
                    logging.info(f"✅ Order {oid} reached final state: {status} -> {actual_status}")
                    completed[oid] = actual_status
                    remaining.remove(oid)
                    logging.debug(f"📊 Completed orders: {completed}, remaining: {remaining}")
                    
                    if not remaining:
                        logging.info("🏁 All orders completed, stopping stream")
                        stream_stopped = True

        # Try to use existing WebSocket connection first
        if (hasattr(self, '_websocket_stream') and hasattr(self, '_websocket_thread') and 
            self._websocket_stream is not None and self._websocket_thread is not None):
            return self._use_existing_websocket(on_update, remaining, completed, max_wait_seconds)
        
        # Create new WebSocket connection
        return self._create_new_websocket(on_update, remaining, completed, max_wait_seconds, order_ids)

    def _use_existing_websocket(self, on_update, remaining, completed, max_wait_seconds):
        """Use pre-connected WebSocket stream."""
        logging.info("🎯 Using pre-connected WebSocket stream")
        
        try:
            if self._websocket_stream is not None:
                self._websocket_stream.subscribe_trade_updates(on_update)
                logging.info("✅ Subscribed to trade updates on pre-connected stream")
            
            # Wait for orders to complete
            start_time = time.time()
            stream_stopped = False
            
            while remaining and time.time() - start_time < max_wait_seconds and not stream_stopped:
                time.sleep(0.1)

            # Handle timeouts
            if remaining and not stream_stopped:
                logging.warning(f"⏰ Timeout reached! Remaining orders: {remaining}")
                for oid in remaining:
                    completed[oid] = "timeout"
            else:
                logging.info("✅ All orders completed before timeout")

            logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
            return completed
                
        except Exception as e:
            logging.error(f"❌ Error using pre-connected WebSocket: {e}")
            # Fall back to polling
            return self._wait_for_order_completion_polling(list(remaining) + list(completed.keys()), max_wait_seconds)

    def _create_new_websocket(self, on_update, remaining, completed, max_wait_seconds, order_ids):
        """Create new WebSocket connection."""
        api_key = getattr(self.trading_client, "_api_key")
        secret_key = getattr(self.trading_client, "_secret_key")
        paper = getattr(self.trading_client, "_sandbox", True)
        
        logging.info("Creating new WebSocket connection")

        try:
            from alpaca.trading.stream import TradingStream
            
            logging.info("🚀 Starting new WebSocket stream...")
            stream = TradingStream(api_key, secret_key, paper=paper)
            stream.subscribe_trade_updates(on_update)
            
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()
            
            # Give WebSocket time to connect
            time.sleep(3)
                
        except Exception as e:
            logging.error(f"❌ Failed to initialize new WebSocket stream: {e}")
            return self._wait_for_order_completion_polling(order_ids, max_wait_seconds)
        
        # Wait for completion
        start_time = time.time()
        while remaining and time.time() - start_time < max_wait_seconds:
            time.sleep(0.5)

        # Handle results and cleanup
        if remaining:
            logging.warning(f"⏰ Timeout reached! Remaining orders: {remaining}")
            stream.stop()
            thread.join(timeout=2)
            for oid in remaining:
                completed[oid] = "timeout"
        else:
            logging.info("✅ All orders completed before timeout")

        logging.info(f"🏁 Order settlement complete: {len(completed)} orders processed")
        return completed

    def prepare_websocket_connection(self) -> bool:
        """Pre-initialize WebSocket connection for faster order monitoring."""
        api_key = getattr(self.trading_client, "_api_key", None)
        secret_key = getattr(self.trading_client, "_secret_key", None)
        has_keys = isinstance(api_key, str) and isinstance(secret_key, str)
        
        if not has_keys:
            self.console.print("[yellow]⚠️ No API keys available for WebSocket[/yellow]")
            return False
        
        paper = getattr(self.trading_client, "_sandbox", True)
        
        try:
            from alpaca.trading.stream import TradingStream
            
            # Clean up any existing connection first
            self.cleanup_websocket_connection()
            
            self.console.print("[blue]🔌 Initializing WebSocket for trade monitoring...[/blue]")
            
            # Create the stream
            stream = TradingStream(str(api_key), str(secret_key), paper=paper)
            
            # Dummy handler for trade updates
            async def dummy_handler(data):
                if logging.getLogger().level <= logging.DEBUG:
                    self.console.print(f"[dim]📡 Pre-connection WebSocket message: {data}[/dim]")
            
            stream.subscribe_trade_updates(dummy_handler)
            
            # Start the stream
            thread = threading.Thread(target=stream.run, daemon=True)
            thread.start()
            time.sleep(2.0)
            
            # Store for later use
            self._websocket_stream = stream
            self._websocket_thread = thread
            
            self.console.print("[green]🎯 WebSocket connection established![/green]")
            logging.info("🎯 WebSocket pre-connection established!")
            return True
                
        except Exception as e:
            self.console.print(f"[red]❌ Failed to pre-initialize WebSocket: {e}[/red]")
            logging.error(f"❌ Failed to pre-initialize WebSocket: {e}")
            return False

    def cleanup_websocket_connection(self) -> None:
        """Clean up any existing WebSocket connection."""
        if hasattr(self, '_websocket_stream') and self._websocket_stream is not None:
            try:
                self._websocket_stream.stop()
            except:
                pass
            delattr(self, '_websocket_stream')
        
        if hasattr(self, '_websocket_thread') and self._websocket_thread is not None:
            try:
                if self._websocket_thread.is_alive():
                    self._websocket_thread.join(timeout=1.0)
            except:
                pass
            delattr(self, '_websocket_thread')
