"""Utility functions and classes for generating trading alerts.

This module centralizes alert creation and logging, providing helpers that
convert strategy recommendations into structured data that can be persisted or
displayed to users.
"""

import datetime as dt
import json
import logging
import re
from typing import Any

from the_alchemiser.infrastructure.config import load_settings


class Alert:
    """Container for a single strategy alert."""

    def __init__(
        self, symbol: str, action: str, reason: str, timestamp: dt.datetime, price: float
    ) -> None:
        """Initialize an alert.

        Args:
            symbol: Ticker symbol the alert relates to.
            action: Recommended action such as ``"BUY"`` or ``"SELL"``.
            reason: Human readable explanation for the alert.
            timestamp: Time the alert was generated.
            price: Price associated with the alert.

        """
        self.symbol = symbol
        self.action = action
        self.reason = reason
        self.timestamp = timestamp
        self.price = price

    def to_dict(self) -> dict[str, Any]:
        """Serialize the alert to a dictionary for storage or logging."""
        return {
            "symbol": self.symbol,
            "action": self.action,
            "reason": self.reason,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, dt.datetime)
                else str(self.timestamp)
            ),
            "price": self.price,
        }


# Factory function for alert creation (can be extended for more logic)
def create_alert(
    symbol: str, action: str, reason: str, price: float, timestamp: dt.datetime | None = None
) -> Alert:
    """Create a new :class:`Alert` instance.

    Args:
        symbol: Ticker symbol the alert relates to.
        action: Recommended action such as ``"BUY"`` or ``"SELL"``.
        reason: Human readable explanation for the alert.
        price: Price associated with the alert.
        timestamp: Optional timestamp to associate with the alert. If omitted the
            current time is used.

    Returns:
        Alert: Newly constructed alert object.

    """
    if timestamp is None:
        timestamp = dt.datetime.now()
    return Alert(symbol, action, reason, timestamp, price)


def create_alerts_from_signal(
    symbol: str,
    action: str,
    reason: str,
    indicators: dict[str, Any],
    market_data: dict[str, Any],
    data_provider: Any,
    ensure_scalar_price: Any,
    strategy_engine: Any = None,
) -> list[Alert]:
    """Create Alert objects based on the signal type and portfolio logic.
    data_provider: must have get_current_price(symbol)
    ensure_scalar_price: function to convert price to scalar
    strategy_engine: NuclearStrategyEngine instance to avoid circular imports.
    """
    alerts = []

    if symbol == "NUCLEAR_PORTFOLIO" and action == "BUY":
        nuclear_portfolio = indicators.get("nuclear_portfolio")
        if not nuclear_portfolio and market_data and strategy_engine:
            # Use passed strategy_engine to avoid circular import
            nuclear_portfolio = strategy_engine.get_nuclear_portfolio(indicators, market_data)
        for stock_symbol, allocation in (nuclear_portfolio or {}).items():
            current_price = data_provider.get_current_price(stock_symbol)
            current_price = ensure_scalar_price(current_price)
            portfolio_reason = (
                f"Nuclear portfolio allocation: {allocation['weight']:.1%} ({reason})"
            )
            alerts.append(
                Alert(
                    symbol=stock_symbol,
                    action=action,
                    reason=portfolio_reason,
                    timestamp=dt.datetime.now(),
                    price=current_price,
                )
            )
        return alerts
    if symbol == "UVXY_BTAL_PORTFOLIO" and action == "BUY":
        # UVXY 75%
        uvxy_price = data_provider.get_current_price("UVXY")
        uvxy_price = ensure_scalar_price(uvxy_price)
        alerts.append(
            Alert(
                symbol="UVXY",
                action=action,
                reason=f"Volatility hedge allocation: 75% ({reason})",
                timestamp=dt.datetime.now(),
                price=uvxy_price,
            )
        )
        # BTAL 25%
        btal_price = data_provider.get_current_price("BTAL")
        btal_price = ensure_scalar_price(btal_price)
        alerts.append(
            Alert(
                symbol="BTAL",
                action=action,
                reason=f"Anti-beta hedge allocation: 25% ({reason})",
                timestamp=dt.datetime.now(),
                price=btal_price,
            )
        )
        return alerts
    if symbol == "BEAR_PORTFOLIO" and action == "BUY":
        portfolio_match = re.findall(r"(\w+) \((\d+(?:\.\d+)?)%\)", reason)
        if portfolio_match:
            for stock_symbol, allocation_str in portfolio_match:
                current_price = data_provider.get_current_price(stock_symbol)
                current_price = ensure_scalar_price(current_price)
                bear_reason = (
                    f"Bear market allocation: {allocation_str}% (inverse volatility weighted)"
                )
                alerts.append(
                    Alert(
                        symbol=stock_symbol,
                        action=action,
                        reason=bear_reason,
                        timestamp=dt.datetime.now(),
                        price=current_price,
                    )
                )
            return alerts
        current_price = data_provider.get_current_price(symbol)
        current_price = ensure_scalar_price(current_price)
        alerts.append(
            Alert(
                symbol=symbol,
                action=action,
                reason=reason,
                timestamp=dt.datetime.now(),
                price=current_price,
            )
        )
        return alerts
    current_price = data_provider.get_current_price(symbol)
    current_price = ensure_scalar_price(current_price)
    alerts.append(
        Alert(
            symbol=symbol,
            action=action,
            reason=reason,
            timestamp=dt.datetime.now(),
            price=current_price,
        )
    )
    return alerts


def log_alert_to_file(
    alert: Alert, log_file_path: str | None = None, paper_trading: bool | None = None
) -> None:
    """Log alert to file - centralized logging logic."""
    if log_file_path is None:
        _config = load_settings()  # Configuration loaded but not used directly
        # Determine trading mode for appropriate JSON file
        if paper_trading is None:
            # Try to detect paper trading from environment or default to paper
            import os

            paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

        # Use appropriate JSON file based on trading mode
        if paper_trading:
            log_file_path = "s3://the-alchemiser-s3/dashboard/paper_signals.json"
        else:
            log_file_path = "s3://the-alchemiser-s3/dashboard/signals.json"

    alert_data = {
        "timestamp": alert.timestamp.isoformat(),
        "symbol": alert.symbol,
        "action": alert.action,
        "price": alert.price,
        "reason": alert.reason,
    }

    try:
        from the_alchemiser.infrastructure.s3.s3_utils import get_s3_handler

        s3_handler = get_s3_handler()

        if log_file_path.startswith("s3://"):
            # Append to S3
            s3_handler.append_text(log_file_path, json.dumps(alert_data) + "\n")
        else:
            # Local file
            with open(log_file_path, "a") as f:
                f.write(json.dumps(alert_data) + "\n")
    except Exception as e:
        logging.error(f"Failed to log alert: {e}")


def log_alerts_to_file(
    alerts: list[Alert], log_file_path: str | None = None, paper_trading: bool | None = None
) -> None:
    """Log multiple alerts to file."""
    if log_file_path is None:
        _config = load_settings()  # Configuration loaded but not used directly
        # Determine trading mode for appropriate JSON file
        if paper_trading is None:
            # Try to detect paper trading from environment or default to paper
            import os

            paper_trading = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

        # Use appropriate JSON file based on trading mode
        if paper_trading:
            log_file_path = "s3://the-alchemiser-s3/dashboard/paper_signals.json"
        else:
            log_file_path = "s3://the-alchemiser-s3/dashboard/signals.json"

    for alert in alerts:
        log_alert_to_file(alert, log_file_path, paper_trading)
