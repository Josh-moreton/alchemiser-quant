#!/usr/bin/env python3
"""
Nuclear Signal Generator

This module provides signal generation for the Nuclear Energy trading strategy, including:
- Data fetching and technical indicator calculation
- Strategy evaluation using pure logic from strategy_engine.py
- Alert generation, logging, and S3 integration
- Portfolio allocation reporting and display
- Both continuous and one-shot execution modes

Pure strategy logic (portfolio construction, signal generation) resides in strategy_engine.py.
This file handles the real-world orchestration, data management, and signal generation layers.
"""

# Standard library imports
import logging
import warnings
from enum import Enum
from typing import Any

from the_alchemiser.domain.math.indicator_utils import safe_get_indicator
from the_alchemiser.domain.math.indicators import TechnicalIndicators

# Static strategy import instead of dynamic import
from the_alchemiser.domain.strategies.strategy_engine import (
    NuclearStrategyEngine as PureStrategyEngine,
)

# Third-party imports
# Local imports
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.config.config_utils import load_alert_config
from the_alchemiser.services.errors.exceptions import StrategyExecutionError
from the_alchemiser.services.market_data.price_utils import ensure_scalar_price

# Setup
warnings.filterwarnings("ignore")
config = load_settings()
logging_config = config.logging.model_dump()

# Logging is configured at application entry point


# ActionType enum for clarity and safety
class ActionType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class NuclearStrategyEngine:
    def get_best_nuclear_stocks(self, indicators: dict[str, Any], top_n: int = 3) -> list[str]:
        """Get top performing nuclear stocks based on 90-day moving average return."""
        portfolio = self.strategy.get_nuclear_portfolio(indicators, top_n=top_n)
        return list(portfolio.keys())[:top_n]

    """Nuclear Strategy Engine - Orchestrates data, indicators, and strategy logic"""

    def __init__(self, data_provider: Any = None) -> None:
        if data_provider is None:
            raise ValueError("data_provider is required for NuclearStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()

        # Use static import - strategy class imported at module level
        self.strategy = PureStrategyEngine()

        # Core symbols from the Nuclear strategy
        self.market_symbols = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX"]
        self.volatility_symbols = ["UVXY", "BTAL"]
        self.tech_symbols = ["QQQ", "SQQQ", "PSQ", "UPRO"]
        self.bond_symbols = ["TLT", "IEF"]

        # Nuclear energy stocks (the core of this strategy)
        self.nuclear_symbols = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]

        # All symbols
        self.all_symbols = (
            self.market_symbols
            + self.volatility_symbols
            + self.tech_symbols
            + self.bond_symbols
            + self.nuclear_symbols
        )

    def get_market_data(self) -> dict[str, Any]:
        """Fetch data for all symbols"""
        market_data = {}
        for symbol in self.all_symbols:
            data = self.data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        return market_data

    def calculate_indicators(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate all technical indicators"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df["Close"]
            indicators[symbol] = {
                "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                "rsi_20": safe_get_indicator(close, self.indicators.rsi, 20),
                "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                "ma_20": safe_get_indicator(close, self.indicators.moving_average, 20),
                "ma_return_90": safe_get_indicator(
                    close, self.indicators.moving_average_return, 90
                ),
                "cum_return_60": safe_get_indicator(close, self.indicators.cumulative_return, 60),
                "current_price": float(close.iloc[-1]),
            }
        return indicators

    def evaluate_nuclear_strategy(
        self, indicators: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> tuple[str, str, str]:
        """
        Evaluate the Nuclear Energy strategy using the shared logic.
        Returns: (recommended_symbol, action, detailed_reason)
        """
        from the_alchemiser.domain.strategies.nuclear_strategy_logic import (
            evaluate_nuclear_strategy_logic,
        )

        symbol, action, reason = evaluate_nuclear_strategy_logic(indicators, market_data, self.strategy)

        # Convert action to ActionType enum value for legacy compatibility
        if action == "BUY":
            action = ActionType.BUY.value
        elif action == "SELL":
            action = ActionType.SELL.value
        else:
            action = ActionType.HOLD.value

        return symbol, action, reason


class NuclearSignalGenerator:
    """Nuclear Energy Signal Generator"""

    def __init__(self) -> None:
        self.strategy = NuclearStrategyEngine()
        self.load_config()

    def load_config(self) -> None:
        """Load configuration"""
        self.config = load_alert_config()

    def handle_nuclear_portfolio_signal(
        self,
        symbol: str,
        action: str,
        reason: str,
        indicators: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Delegate alert creation to alert_service.create_alerts_from_signal"""
        from the_alchemiser.infrastructure.alerts.alert_service import create_alerts_from_signal

        return create_alerts_from_signal(
            symbol,
            action,
            reason,
            indicators,
            market_data or {},
            self.strategy.data_provider,
            ensure_scalar_price,
            self.strategy,
        )

    def run_analysis(self) -> list[Any] | None:
        """Run complete strategy analysis"""
        logging.debug("Starting Nuclear Energy strategy analysis...")

        # Get market data
        market_data = self.strategy.get_market_data()
        if not market_data:
            logging.error("No market data available")
            return None

        # Calculate indicators
        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            logging.error("No indicators calculated")
            return None

        # Evaluate strategy
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)

        # Handle nuclear portfolio signal properly
        alerts = self.handle_nuclear_portfolio_signal(
            symbol, action, reason, indicators, market_data
        )

        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alerts

    def log_alert(self, alert: Any) -> None:
        """Log alert to file - delegates to alert service"""
        from the_alchemiser.infrastructure.alerts.alert_service import log_alert_to_file

        log_alert_to_file(alert)

    def run_once(self) -> Any:
        """Run analysis once"""
        alerts = self.run_analysis()

        # Use the consolidated display utility
        from the_alchemiser.interface.cli.signal_display_utils import (
            display_portfolio_details,
            display_signal_results,
            display_technical_indicators,
        )

        result = display_signal_results(
            alerts or [], "NUCLEAR", ["IOO", "SPY", "TQQQ", "VTV", "XLF"]
        )

        # Display technical indicators for key symbols
        if alerts:
            display_technical_indicators(self.strategy, ["IOO", "SPY", "TQQQ", "VTV", "XLF"])

            # Show portfolio allocation details for multi-asset signals
            if len(alerts) > 1:
                display_portfolio_details(self, "NUCLEAR")

        return result

    def run_continuous(self, interval_minutes: int = 15, max_errors: int = 10) -> None:
        """Run analysis continuously with error limits"""
        import time

        logging.info(
            f"Starting continuous Nuclear Energy analysis (every {interval_minutes} minutes)"
        )
        error_count = 0

        while True:
            try:
                self.run_once()
                error_count = 0  # Reset error count on success
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logging.info("Stopping Nuclear Energy bot...")
                break
            except StrategyExecutionError as e:
                from the_alchemiser.infrastructure.logging.logging_utils import (
                    get_logger,
                    log_error_with_context,
                )

                error_count += 1
                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "nuclear_strategy_continuous_run",
                    function="run_continuous",
                    error_count=error_count,
                    max_errors=max_errors,
                    error_type=type(e).__name__,
                )
                logging.error(
                    f"Strategy execution error in continuous run ({error_count}/{max_errors}): {e}"
                )

                if error_count >= max_errors:
                    logging.error(
                        f"Too many consecutive strategy errors ({max_errors}), stopping..."
                    )
                    break
            except Exception as e:
                from the_alchemiser.infrastructure.logging.logging_utils import (
                    get_logger,
                    log_error_with_context,
                )

                error_count += 1
                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "nuclear_strategy_continuous_run",
                    function="run_continuous",
                    error_count=error_count,
                    max_errors=max_errors,
                    error_type="unexpected_error",
                    original_error=type(e).__name__,
                )
                logging.error(
                    f"Unexpected error in continuous run ({error_count}/{max_errors}): {e}"
                )

                if error_count >= max_errors:
                    logging.error(f"Too many consecutive errors ({max_errors}), stopping...")
                    break

                # Exponential backoff for errors
                backoff_time = min(60 * (2 ** min(error_count, 5)), 300)  # Max 5 minutes
                logging.info(f"Backing off for {backoff_time} seconds...")
                time.sleep(backoff_time)

    def get_current_portfolio_allocation(self) -> dict[str, Any] | None:
        """Get current portfolio allocation for display purposes"""
        # Get market data and indicators
        market_data = self.strategy.get_market_data()
        if not market_data:
            return None

        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            return None

        # Get strategy recommendation
        symbol, action, reason = self.strategy.evaluate_nuclear_strategy(indicators, market_data)

        # If we're in a bull market, show the nuclear portfolio
        if "SPY" in indicators:
            spy_price = indicators["SPY"]["current_price"]
            spy_ma_200 = indicators["SPY"]["ma_200"]

            if spy_price > spy_ma_200 and action == "BUY":
                nuclear_portfolio = self.strategy.strategy.get_nuclear_portfolio(
                    indicators, market_data
                )
                if nuclear_portfolio:
                    # Add current prices and market values
                    portfolio_with_prices = {}
                    for symbol, data in nuclear_portfolio.items():
                        if symbol in indicators:
                            current_price = indicators[symbol]["current_price"]
                            portfolio_with_prices[symbol] = {
                                "weight": data["weight"],
                                "performance": data["performance"],
                                "current_price": current_price,
                                "market_value": 10000 * data["weight"],  # Assuming $10k portfolio
                                "shares": (10000 * data["weight"]) / current_price,
                            }
                    return portfolio_with_prices

        return None
