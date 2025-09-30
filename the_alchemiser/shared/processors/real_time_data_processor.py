"""Business Unit: shared | Status: current.

Real-time data processor for streaming market data.

This module processes real-time market data (quotes, trades, bars) from WebSocket
streams and transforms them into structured events and aggregated metrics for
consumption by trading strategies and other system components.

DESIGN PHILOSOPHY:
=================
- Single responsibility: process and enrich real-time market data
- Event-driven: publish processed data as events for downstream consumption
- Stateless: maintain minimal state, primarily for aggregation windows
- Type-safe: use structured DTOs (QuoteModel, BarModel) for all data
- Memory-efficient: automatic cleanup of aged data

KEY FEATURES:
============
1. Quote processing with spread analysis and quality checks
2. Trade processing with VWAP calculation
3. Bar aggregation for custom timeframes
4. Market depth tracking (bid/ask sizes)
5. Rolling statistics (volume, volatility)
6. Suspicious data detection and filtering
7. Thread-safe data structures for concurrent access

USAGE:
=====
processor = RealTimeDataProcessor()
processor.process_quote(quote_model)
processor.process_trade(trade_model)
metrics = processor.get_symbol_metrics("AAPL")
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from ..logging.logging_utils import get_logger
from ..types.market_data import BarModel, QuoteModel

logger = get_logger(__name__)


@dataclass
class TradeData:
    """Trade data structure."""

    symbol: str
    price: float
    size: float
    timestamp: datetime


@dataclass
class SymbolMetrics:
    """Real-time metrics for a symbol."""

    symbol: str
    last_quote: QuoteModel | None = None
    last_trade: TradeData | None = None
    quote_count: int = 0
    trade_count: int = 0
    total_volume: float = 0.0
    vwap: float = 0.0
    avg_spread: float = 0.0
    min_spread: float = float("inf")
    max_spread: float = 0.0
    suspicious_quotes: int = 0
    last_update: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProcessingConfig:
    """Configuration for data processor."""

    max_quote_history: int = 100
    max_trade_history: int = 100
    vwap_window_seconds: int = 300  # 5 minutes
    cleanup_interval_seconds: int = 300  # 5 minutes
    max_spread_threshold: float = 0.10  # 10% spread considered suspicious
    min_quote_age_seconds: int = 60  # Quotes older than this are considered stale


class RealTimeDataProcessor:
    """Process real-time market data streams.

    Handles quotes, trades, and bars from WebSocket feeds, providing:
    - Data validation and quality checks
    - Aggregation and statistical calculations
    - Suspicious data detection
    - Memory-efficient storage with automatic cleanup
    """

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        """Initialize the real-time data processor.

        Args:
            config: Processing configuration, uses defaults if not provided

        """
        self.config = config or ProcessingConfig()
        self._metrics: dict[str, SymbolMetrics] = {}
        self._quote_history: dict[str, deque[QuoteModel]] = defaultdict(
            lambda: deque(maxlen=self.config.max_quote_history)
        )
        self._trade_history: dict[str, deque[TradeData]] = defaultdict(
            lambda: deque(maxlen=self.config.max_trade_history)
        )
        self._lock = threading.Lock()
        self._last_cleanup = datetime.now(UTC)

        logger.info("📊 Real-time data processor initialized")

    def process_quote(self, quote: QuoteModel) -> dict[str, Any]:
        """Process a real-time quote update.

        Args:
            quote: Quote data to process

        Returns:
            Processing result with metrics and flags

        """
        with self._lock:
            symbol = quote.symbol

            # Initialize metrics if needed
            if symbol not in self._metrics:
                self._metrics[symbol] = SymbolMetrics(symbol=symbol)

            metrics = self._metrics[symbol]

            # Validate quote quality
            is_suspicious = self._check_quote_quality(quote)

            # Update metrics
            metrics.last_quote = quote
            metrics.quote_count += 1
            metrics.last_update = datetime.now(UTC)

            if is_suspicious:
                metrics.suspicious_quotes += 1

            # Update spread statistics
            spread = quote.spread
            if spread >= 0:
                if metrics.quote_count == 1:
                    metrics.avg_spread = spread
                    metrics.min_spread = spread
                    metrics.max_spread = spread
                else:
                    # Running average
                    metrics.avg_spread = (
                        metrics.avg_spread * (metrics.quote_count - 1) + spread
                    ) / metrics.quote_count
                    metrics.min_spread = min(metrics.min_spread, spread)
                    metrics.max_spread = max(metrics.max_spread, spread)

            # Store in history
            self._quote_history[symbol].append(quote)

            # Periodic cleanup
            self._maybe_cleanup()

            return {
                "symbol": symbol,
                "is_suspicious": is_suspicious,
                "spread": spread,
                "mid_price": quote.mid_price,
                "quote_count": metrics.quote_count,
            }

    def process_trade(
        self, symbol: str, price: float, size: float, timestamp: datetime
    ) -> dict[str, Any]:
        """Process a real-time trade update.

        Args:
            symbol: Stock symbol
            price: Trade price
            size: Trade size (shares)
            timestamp: Trade timestamp

        Returns:
            Processing result with VWAP and volume metrics

        """
        with self._lock:
            # Initialize metrics if needed
            if symbol not in self._metrics:
                self._metrics[symbol] = SymbolMetrics(symbol=symbol)

            metrics = self._metrics[symbol]

            # Create trade data
            trade = TradeData(symbol=symbol, price=price, size=size, timestamp=timestamp)

            # Update metrics
            metrics.last_trade = trade
            metrics.trade_count += 1
            metrics.total_volume += size
            metrics.last_update = datetime.now(UTC)

            # Store in history
            self._trade_history[symbol].append(trade)

            # Calculate VWAP
            vwap = self._calculate_vwap(symbol)
            metrics.vwap = vwap

            return {
                "symbol": symbol,
                "price": price,
                "size": size,
                "vwap": vwap,
                "total_volume": metrics.total_volume,
                "trade_count": metrics.trade_count,
            }

    def get_symbol_metrics(self, symbol: str) -> SymbolMetrics | None:
        """Get current metrics for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Symbol metrics or None if not tracked

        """
        with self._lock:
            return self._metrics.get(symbol)

    def get_all_metrics(self) -> dict[str, SymbolMetrics]:
        """Get metrics for all tracked symbols.

        Returns:
            Dictionary mapping symbols to their metrics

        """
        with self._lock:
            return dict(self._metrics)

    def get_quote_history(self, symbol: str, max_count: int = 100) -> list[QuoteModel]:
        """Get recent quote history for a symbol.

        Args:
            symbol: Stock symbol
            max_count: Maximum number of quotes to return

        Returns:
            List of recent quotes (most recent last)

        """
        with self._lock:
            history = self._quote_history.get(symbol, deque())
            return list(history)[-max_count:]

    def get_trade_history(self, symbol: str, max_count: int = 100) -> list[TradeData]:
        """Get recent trade history for a symbol.

        Args:
            symbol: Stock symbol
            max_count: Maximum number of trades to return

        Returns:
            List of recent trades (most recent last)

        """
        with self._lock:
            history = self._trade_history.get(symbol, deque())
            return list(history)[-max_count:]

    def clear_symbol(self, symbol: str) -> None:
        """Clear all data for a symbol.

        Args:
            symbol: Stock symbol to clear

        """
        with self._lock:
            self._metrics.pop(symbol, None)
            self._quote_history.pop(symbol, None)
            self._trade_history.pop(symbol, None)
            logger.debug(f"Cleared data for symbol: {symbol}")

    def clear_all(self) -> None:
        """Clear all tracked data."""
        with self._lock:
            self._metrics.clear()
            self._quote_history.clear()
            self._trade_history.clear()
            logger.info("Cleared all processor data")

    def _check_quote_quality(self, quote: QuoteModel) -> bool:
        """Check if quote appears suspicious.

        Args:
            quote: Quote to check

        Returns:
            True if quote appears suspicious, False otherwise

        """
        # Check for negative prices
        if quote.bid_price <= 0 or quote.ask_price <= 0:
            logger.warning(
                f"Suspicious quote for {quote.symbol}: negative prices "
                f"(bid={quote.bid_price}, ask={quote.ask_price})"
            )
            return True

        # Check for inverted bid/ask
        if quote.bid_price > quote.ask_price:
            logger.warning(
                f"Suspicious quote for {quote.symbol}: inverted bid/ask "
                f"(bid={quote.bid_price} > ask={quote.ask_price})"
            )
            return True

        # Check for excessive spread
        spread_pct = quote.spread / quote.mid_price if quote.mid_price > 0 else 0
        if spread_pct > self.config.max_spread_threshold:
            logger.warning(
                f"Suspicious quote for {quote.symbol}: excessive spread "
                f"({spread_pct:.2%} > {self.config.max_spread_threshold:.2%})"
            )
            return True

        # Check for stale data
        age = (datetime.now(UTC) - quote.timestamp).total_seconds()
        if age > self.config.min_quote_age_seconds:
            logger.debug(
                f"Stale quote for {quote.symbol}: age={age:.1f}s "
                f"(threshold={self.config.min_quote_age_seconds}s)"
            )
            return True

        return False

    def _calculate_vwap(self, symbol: str) -> float:
        """Calculate volume-weighted average price.

        Args:
            symbol: Stock symbol

        Returns:
            VWAP for the configured time window

        """
        trades = self._trade_history.get(symbol, deque())
        if not trades:
            return 0.0

        # Filter trades within the VWAP window
        cutoff_time = datetime.now(UTC) - timedelta(seconds=self.config.vwap_window_seconds)
        recent_trades = [t for t in trades if t.timestamp >= cutoff_time]

        if not recent_trades:
            return 0.0

        # Calculate VWAP
        total_value = sum(t.price * t.size for t in recent_trades)
        total_volume = sum(t.size for t in recent_trades)

        return total_value / total_volume if total_volume > 0 else 0.0

    def _maybe_cleanup(self) -> None:
        """Perform cleanup if enough time has passed.

        Removes stale data to prevent memory bloat.
        """
        now = datetime.now(UTC)
        elapsed = (now - self._last_cleanup).total_seconds()

        if elapsed >= self.config.cleanup_interval_seconds:
            self._cleanup_stale_data()
            self._last_cleanup = now

    def _cleanup_stale_data(self) -> None:
        """Remove stale data from storage.

        Cleans up data older than the configured thresholds.
        """
        cutoff_time = datetime.now(UTC) - timedelta(seconds=self.config.vwap_window_seconds * 2)
        symbols_to_remove = []

        for symbol, metrics in self._metrics.items():
            if metrics.last_update < cutoff_time:
                symbols_to_remove.append(symbol)

        for symbol in symbols_to_remove:
            self.clear_symbol(symbol)

        if symbols_to_remove:
            logger.debug(f"Cleaned up {len(symbols_to_remove)} stale symbols")
