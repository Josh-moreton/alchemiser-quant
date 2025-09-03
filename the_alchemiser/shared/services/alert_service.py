"""Business Unit: shared | Status: current..

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
        timestamp = dt.datetime.now(dt.UTC)
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
                    timestamp=dt.datetime.now(dt.UTC),
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
                timestamp=dt.datetime.now(dt.UTC),
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
                timestamp=dt.datetime.now(dt.UTC),
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
                        timestamp=dt.datetime.now(dt.UTC),
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
                timestamp=dt.datetime.now(dt.UTC),
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
            timestamp=dt.datetime.now(dt.UTC),
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
        from the_alchemiser.shared.utils.s3_utils import get_s3_handler

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
