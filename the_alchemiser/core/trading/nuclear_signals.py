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

# Third-party imports
# Local imports
from the_alchemiser.core.config import load_settings
from the_alchemiser.core.indicators.indicators import TechnicalIndicators

# Static strategy import instead of dynamic import
from the_alchemiser.core.trading.strategy_engine import NuclearStrategyEngine as PureStrategyEngine
from the_alchemiser.utils.config_utils import load_alert_config
from the_alchemiser.utils.indicator_utils import safe_get_indicator
from the_alchemiser.utils.price_utils import ensure_scalar_price

from ..exceptions import StrategyExecutionError

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
        Evaluate the Nuclear Energy strategy using the canonical hierarchical logic from Clojure implementation.
        Returns: (recommended_symbol, action, detailed_reason)
        """
        from the_alchemiser.core.trading.strategy_engine import (
            BearMarketStrategy,
            BullMarketStrategy,
            VoxOverboughtStrategy,
        )

        if "SPY" not in indicators:
            return (
                "SPY",
                ActionType.HOLD.value,
                "Missing SPY data - cannot evaluate market conditions",
            )

        # Get key market indicators for detailed reasoning
        spy_rsi_10 = indicators["SPY"]["rsi_10"]
        spy_price = indicators["SPY"]["current_price"]
        spy_ma_200 = indicators["SPY"]["ma_200"]
        market_trend = "Bull Market" if spy_price > spy_ma_200 else "Bear Market"

        # PRIMARY BRANCH: SPY RSI > 79 (ALL nested overbought checks happen HERE)
        if spy_rsi_10 > 79:
            base_explanation = f"Market Analysis: {market_trend} (SPY ${spy_price:.2f} vs 200MA ${spy_ma_200:.2f})\nSPY RSI(10): {spy_rsi_10:.1f} - Primary overbought condition triggered (>79)"

            # First: SPY extremely overbought (> 81)
            if spy_rsi_10 > 81:
                explanation = f"{base_explanation}\n\nSignal: SPY extremely overbought (RSI {spy_rsi_10:.1f} > 81)\nAction: Buy UVXY volatility hedge - expect major market correction"
                return "UVXY", ActionType.BUY.value, explanation

            # Then: Nested checks for IOO, TQQQ, VTV, XLF (RSI > 81) - IN ORDER
            for symbol in ["IOO", "TQQQ", "VTV", "XLF"]:
                if symbol in indicators and indicators[symbol]["rsi_10"] > 81:
                    symbol_rsi = indicators[symbol]["rsi_10"]
                    explanation = f"{base_explanation}\n\nSecondary Check: {symbol} RSI(10): {symbol_rsi:.1f} - Extremely overbought (>81)\nAction: Buy UVXY volatility hedge - sector rotation imminent"
                    return "UVXY", ActionType.BUY.value, explanation

            # Finally: SPY moderately overbought (79-81) - hedge portfolio
            explanation = f"{base_explanation}\n\nSignal: SPY moderately overbought (79 < RSI {spy_rsi_10:.1f} < 81)\nAction: Defensive hedged position - UVXY 75% + BTAL 25%\nRationale: Partial volatility hedge while maintaining some upside exposure"
            return "UVXY_BTAL_PORTFOLIO", ActionType.BUY.value, explanation

        # PRIMARY BRANCH: SPY RSI <= 79 - Continue with VOX, oversold checks, bull/bear logic
        base_explanation = f"Market Analysis: {market_trend} (SPY ${spy_price:.2f} vs 200MA ${spy_ma_200:.2f})\nSPY RSI(10): {spy_rsi_10:.1f} - Not overbought, checking secondary conditions"

        # VOX overbought check
        if "VOX" in indicators and indicators["VOX"]["rsi_10"] > 79:
            vox_rsi = indicators["VOX"]["rsi_10"]
            result = VoxOverboughtStrategy().recommend(indicators)
            if result:
                symbol, action, basic_reason = result
                explanation = f"{base_explanation}\n\nVOX Telecom Analysis: RSI(10) {vox_rsi:.1f} > 79 (overbought)\n{basic_reason}"
                return symbol, action, explanation

        # Oversold conditions (TQQQ first, then SPY)
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            tqqq_rsi = indicators["TQQQ"]["rsi_10"]
            explanation = f"{base_explanation}\n\nOversold Opportunity: TQQQ RSI(10) {tqqq_rsi:.1f} < 30\nAction: Buy the dip in leveraged tech - oversold bounce expected"
            return "TQQQ", ActionType.BUY.value, explanation

        if indicators["SPY"]["rsi_10"] < 30:
            explanation = f"{base_explanation}\n\nOversold Opportunity: SPY RSI(10) {spy_rsi_10:.1f} < 30\nAction: Buy UPRO (3x leveraged SPY) - market oversold, strong bounce expected"
            return "UPRO", ActionType.BUY.value, explanation

        # Bull vs Bear market determination (SPY above/below 200 MA)
        if "SPY" in indicators and spy_price > spy_ma_200:
            result = BullMarketStrategy(self.strategy).recommend(indicators, market_data)
            if result:
                symbol, action, basic_reason = result
                explanation = f"{base_explanation}\n\nBull Market Strategy: SPY above 200MA (${spy_price:.2f} > ${spy_ma_200:.2f})\n{basic_reason}"
                return symbol, action, explanation
        else:
            result = BearMarketStrategy(self.strategy).recommend(indicators)
            if result:
                symbol, action, basic_reason = result
                explanation = f"{base_explanation}\n\nBear Market Strategy: SPY below 200MA (${spy_price:.2f} < ${spy_ma_200:.2f})\n{basic_reason}"
                return symbol, action, explanation

        # Fallback - no clear signal
        explanation = f"{base_explanation}\n\nNo Clear Signal: Market conditions neutral\nRSI not overbought/oversold, no strong trend signals\nAction: Hold current positions, wait for clearer market direction"
        return "SPY", ActionType.HOLD.value, explanation


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
        from the_alchemiser.core.alerts.alert_service import create_alerts_from_signal

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
        from the_alchemiser.core.alerts.alert_service import log_alert_to_file

        log_alert_to_file(alert)

    def run_once(self) -> Any:
        """Run analysis once"""
        alerts = self.run_analysis()

        # Use the consolidated display utility
        from the_alchemiser.utils.signal_display_utils import (
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
                from ..logging.logging_utils import get_logger, log_error_with_context

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
                from ..logging.logging_utils import get_logger, log_error_with_context

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
