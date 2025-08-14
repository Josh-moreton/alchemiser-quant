#!/usr/bin/env python3
"""
TECL Signal Generator

This module implements the signal generation layer for the TECL strategy, including:
- Market regime detection using SPY vs 200-day MA
- RSI-based timing signals and sector rotation (XLK vs KMLM)
- Dynamic allocation between TECL, BIL, UVXY, SQQQ, and BSV
- Volatility protection and defensive positioning
- Technical indicator calculation, alert generation, and S3 integration
- Both continuous and one-shot execution modes

This file handles data fetching, orchestration, and signal generation for the TECL strategy,
while pure strategy logic resides in tecl_strategy_engine.py.
"""

# Standard library imports
import logging
import warnings
from typing import Any

from the_alchemiser.domain.math.indicator_utils import safe_get_indicator

# Third-party imports
# Local imports
from the_alchemiser.domain.math.indicators import TechnicalIndicators

# Static strategy import instead of dynamic import
from the_alchemiser.domain.strategies.tecl_strategy_engine import (
    TECLStrategyEngine as PureStrategyEngine,
)
from the_alchemiser.infrastructure.config.config_utils import load_alert_config
from the_alchemiser.services.market_data.price_utils import ensure_scalar_price

warnings.filterwarnings("ignore")


# Import Alert from alert_service

# Import UnifiedDataProvider from the new module


# Import ActionType from common module


class TECLStrategyEngine:
    """TECL Strategy Engine - Orchestrates data, indicators, and strategy logic"""

    def __init__(self, data_provider: Any = None) -> None:
        if data_provider is None:
            raise ValueError("data_provider is required for TECLStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()

        # Use static import - strategy class imported at module level
        self.strategy = PureStrategyEngine(data_provider=self.data_provider)

        # TECL strategy symbols
        self.market_symbols = ["SPY", "XLK", "KMLM"]
        self.tecl_symbols = ["TECL", "BIL", "UVXY", "SQQQ", "BSV"]
        self.tech_symbols = ["TQQQ", "SPXL"]  # For oversold signals

        # All symbols needed for TECL strategy
        self.all_symbols = self.market_symbols + self.tecl_symbols + self.tech_symbols

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
        """Calculate all technical indicators needed for TECL strategy"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df["Close"]
            indicators[symbol] = {
                "rsi_9": safe_get_indicator(close, self.indicators.rsi, 9),
                "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                "rsi_20": safe_get_indicator(close, self.indicators.rsi, 20),
                "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                "ma_20": safe_get_indicator(close, self.indicators.moving_average, 20),
                "current_price": float(close.iloc[-1]),
            }
        return indicators

    def evaluate_tecl_strategy(
        self, indicators: dict[str, Any], market_data: Any | None = None
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Evaluate the TECL strategy using the pure strategy logic.
        Returns: (recommended_symbol, action, reason)
        """
        return self.strategy.evaluate_tecl_strategy(indicators, market_data)


class TECLSignalGenerator:
    """TECL Signal Generator"""

    def __init__(self) -> None:
        self.strategy = TECLStrategyEngine()
        self.load_config()

    def load_config(self) -> None:
        """Load configuration"""
        self.config = load_alert_config()

    def handle_tecl_portfolio_signal(
        self,
        symbol: str | dict[str, float],
        action: str,
        reason: str,
        indicators: dict[str, Any],
        market_data: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Delegate alert creation to alert_service.create_alerts_from_signal"""
        from the_alchemiser.infrastructure.alerts.alert_service import create_alerts_from_signal

        # Convert dict symbol to string representation for alert service
        symbol_str = str(symbol) if isinstance(symbol, dict) else symbol

        return create_alerts_from_signal(
            symbol_str,
            action,
            reason,
            indicators,
            market_data or {},
            self.strategy.data_provider,
            ensure_scalar_price,
            self.strategy,
        )

    def run_analysis(self) -> list[Any] | None:
        """Run complete TECL strategy analysis"""
        logging.info("Starting TECL strategy analysis...")

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
        symbol, action, reason = self.strategy.evaluate_tecl_strategy(indicators, market_data)

        # Handle TECL portfolio signal properly
        alerts = self.handle_tecl_portfolio_signal(symbol, action, reason, indicators, market_data)

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
            display_signal_results,
            display_technical_indicators,
        )

        result = display_signal_results(alerts or [], "TECL", ["SPY", "XLK", "KMLM", "TECL"])

        # Display technical indicators for key symbols
        if alerts:
            display_technical_indicators(self.strategy, ["SPY", "XLK", "KMLM", "TECL"])

        return result

    def run_continuous(self, interval_minutes: int = 15, max_errors: int = 10) -> None:
        """Run analysis continuously with error limits"""
        import time

        logging.info(
            f"Starting continuous TECL strategy analysis (every {interval_minutes} minutes)"
        )
        error_count = 0

        while True:
            try:
                self.run_once()
                error_count = 0  # Reset error count on success
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                logging.info("Stopping TECL bot...")
                break
            except Exception as e:
                error_count += 1
                logging.error(f"Error in continuous run ({error_count}/{max_errors}): {e}")

                if error_count >= max_errors:
                    logging.error(f"Too many consecutive errors ({max_errors}), stopping...")
                    break

                # Exponential backoff for errors
                backoff_time = min(60 * (2 ** min(error_count, 5)), 300)  # Max 5 minutes
                logging.info(f"Backing off for {backoff_time} seconds...")
                time.sleep(backoff_time)

    def get_current_portfolio_allocation(self) -> dict[str, Any] | None:
        """Get current TECL portfolio allocation for display purposes"""
        # Get market data and indicators
        market_data = self.strategy.get_market_data()
        if not market_data:
            return None

        indicators = self.strategy.calculate_indicators(market_data)
        if not indicators:
            return None

        # Get strategy recommendation
        symbol, action, reason = self.strategy.evaluate_tecl_strategy(indicators, market_data)

        # Return current allocation with prices
        if isinstance(symbol, dict):
            # Multi-asset allocation
            portfolio_with_prices = {}
            for asset_symbol, weight in symbol.items():
                if asset_symbol in indicators:
                    current_price = indicators[asset_symbol]["current_price"]
                    portfolio_with_prices[asset_symbol] = {
                        "weight": weight,
                        "current_price": current_price,
                        "market_value": 10000 * weight,  # Assuming $10k portfolio
                        "shares": (10000 * weight) / current_price if current_price > 0 else 0,
                    }
            return portfolio_with_prices
        elif symbol in indicators:
            # Single asset allocation
            current_price = indicators[symbol]["current_price"]
            return {
                symbol: {
                    "weight": 1.0,
                    "current_price": current_price,
                    "market_value": 10000,
                    "shares": 10000 / current_price if current_price > 0 else 0,
                }
            }

        return None
