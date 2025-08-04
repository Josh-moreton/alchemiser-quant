#!/usr/bin/env python3
"""
KLM Quantitative Trading Engine

This module implements the orchestration and execution layer for the KLM strategy, including:
- Multi-layer RSI overbought detection for volatility protection
- Complex nested if-then logic for sector rotation
- VIX-based hedging and defensive positioning
- Technical indicator calculation, alert generation, and S3 integration
- Both continuous and one-shot execution modes

This file handles data fetching, orchestration, and execution for the KLM strategy,
using the KLM ensemble approach for multi-variant strategy selection.
"""

# Standard library imports
import datetime as dt
import logging
import warnings

# Third-party imports
import pandas as pd

# Local imports
from the_alchemiser.core.indicators.indicators import TechnicalIndicators

# Static strategy import instead of dynamic import - KLM uses ensemble approach
from the_alchemiser.core.trading.klm_ensemble_engine import KLMStrategyEnsemble

warnings.filterwarnings("ignore")

# Import Alert from alert_service

from the_alchemiser.core.alerts.alert_service import Alert

# Import UnifiedDataProvider from the new module
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

# Import ActionType from common module


class KLMStrategyEngine:
    """KLM Strategy Engine - Orchestrates data, indicators, and strategy logic"""

    def __init__(self, data_provider=None):
        if data_provider is None:
            raise ValueError("data_provider is required for KLMStrategyEngine")
        self.data_provider = data_provider
        self.indicators = TechnicalIndicators()

        # Use static import - strategy class imported at module level
        self.strategy = KLMStrategyEnsemble(data_provider=self.data_provider)

        # KLM strategy symbols (comprehensive list from strategy logic)
        self.market_symbols = ["SPY", "QQQE", "VTV", "VOX", "TECL", "VOOG", "VOOV"]
        self.sector_symbols = ["XLP", "TQQQ", "XLY", "FAS", "XLF", "RETL", "XLK"]
        self.tech_symbols = ["SOXL", "SPXL", "SPLV"]
        self.volatility_symbols = ["UVXY", "VIXY", "VXX", "VIXM"]
        self.bond_symbols = ["TLT", "BIL", "BTAL", "BND", "KMLM"]
        self.bear_symbols = ["LABD", "TZA"]

        # All symbols needed for KLM strategy
        self.all_symbols = (
            self.market_symbols
            + self.sector_symbols
            + self.tech_symbols
            + self.volatility_symbols
            + self.bond_symbols
            + self.bear_symbols
        )

    def get_market_data(self):
        """Fetch data for all symbols"""
        market_data = {}
        for symbol in self.all_symbols:
            data = self.data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        return market_data

    def safe_get_indicator(self, data, indicator_func, *args, **kwargs):
        """Safely get indicator value, logging exceptions to surface data problems."""
        try:
            result = indicator_func(data, *args, **kwargs)
            if pd.isna(result) or result is None:
                logging.warning(f"Indicator {indicator_func.__name__} returned NaN/None")
                return 50.0  # Neutral RSI as fallback
            return float(result)
        except ValueError as e:
            logging.error(f"ValueError in safe_get_indicator for {indicator_func.__name__}: {e}")
            return 50.0
        except Exception as e:
            logging.error(f"Exception in safe_get_indicator for {indicator_func.__name__}: {e}")
            return 50.0

    def calculate_indicators(self, market_data):
        """Calculate all technical indicators needed for KLM strategy"""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue
            close = df["Close"]
            indicators[symbol] = {
                "rsi_10": self.safe_get_indicator(close, self.indicators.rsi, 10),
                "rsi_20": self.safe_get_indicator(close, self.indicators.rsi, 20),
                "rsi_21": self.safe_get_indicator(close, self.indicators.rsi, 21),
                "current_price": float(close.iloc[-1]),
            }
        return indicators

    def evaluate_klm_strategy(self, indicators, market_data=None):
        """
        Evaluate the KLM strategy using the ensemble approach.
        Returns: (recommended_symbol, action, reason)
        """
        # The ensemble returns (symbol_or_allocation, action, detailed_reason, variant_name)
        # We need to unwrap this for compatibility
        result = self.strategy.evaluate_ensemble(indicators, market_data)
        return result[0], result[1], result[2]  # Return (symbol, action, reason)


class KLMTradingBot:
    """KLM Quantitative Trading Engine"""

    def __init__(self, data_provider=None):
        if data_provider is None:
            data_provider = UnifiedDataProvider(paper_trading=True)

        self.strategy = KLMStrategyEngine(data_provider=data_provider)

    def handle_klm_signal(self, symbol, action, reason, indicators, market_data):
        """Handle KLM strategy signal and convert to Alert objects"""
        alerts = []
        current_time = dt.datetime.now()

        # Handle single symbol signals
        if isinstance(symbol, str):
            if symbol in indicators:
                current_price = indicators[symbol]["current_price"]
            else:
                current_price = 0.0

            alert = Alert(
                symbol=symbol,
                action=action,
                price=current_price,
                timestamp=current_time,
                reason=reason,
            )
            alerts.append(alert)

        # Handle portfolio allocations (dict)
        elif isinstance(symbol, dict):
            for sym, weight in symbol.items():
                if sym in indicators:
                    current_price = indicators[sym]["current_price"]
                else:
                    current_price = 0.0

                alert = Alert(
                    symbol=sym,
                    action=action,
                    price=current_price,
                    timestamp=current_time,
                    reason=f"{reason} (Weight: {weight:.1%})",
                )
                alerts.append(alert)

        return alerts

    def run_analysis(self):
        """Run complete KLM strategy analysis"""
        logging.info("Starting KLM strategy analysis...")

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
        symbol, action, reason = self.strategy.evaluate_klm_strategy(indicators, market_data)

        # Handle KLM signal properly
        alerts = self.handle_klm_signal(symbol, action, reason, indicators, market_data)

        logging.info(f"Analysis complete: {action} {symbol} - {reason}")
        return alerts

    def run_once(self):
        """Run analysis once"""
        try:
            logging.info("🧪 Starting KLM Energy Strategy Analysis")
            alerts = self.run_analysis()

            if not alerts:
                logging.error("No alerts generated")
                return

            # Display results
            if len(alerts) > 1:
                # Portfolio signal
                logging.info(f"KLM PORTFOLIO SIGNAL: {alerts[0].action}")
                logging.info(f"   Reason: {alerts[0].reason}")

                portfolio = {}
                for alert in alerts:
                    portfolio[alert.symbol] = {
                        "weight": getattr(alert, "allocation", 1.0),
                        "price": alert.price,
                    }

                if portfolio:
                    logging.info("PORTFOLIO DETAILS:")
                    for symbol, data in portfolio.items():
                        logging.info(f"   {symbol}: {data['weight']:.1%}")
            else:
                # Single signal
                alert = alerts[0]
                if alert.action != "HOLD":
                    logging.info(
                        f"KLM TRADING SIGNAL: {alert.action} {alert.symbol} at ${alert.price:.2f}"
                    )
                    logging.info(f"   Reason: {alert.reason}")
                else:
                    logging.info(
                        f"KLM Analysis: {alert.action} {alert.symbol} at ${alert.price:.2f}"
                    )
                    logging.info(f"   Reason: {alert.reason}")

            # Print technical indicator values for key symbols
            if alerts and hasattr(self.strategy, "calculate_indicators"):
                market_data = self.strategy.get_market_data()
                indicators = self.strategy.calculate_indicators(market_data)

                key_symbols = ["SPY", "XLK", "KMLM", "UVXY", "QQQE", "TECL"]
                logging.info("📊 Key Technical Indicators:")
                for symbol in key_symbols:
                    if symbol in indicators:
                        rsi_10 = indicators[symbol]["rsi_10"]
                        price = indicators[symbol]["current_price"]
                        logging.info(f"   {symbol}: RSI(10)={rsi_10:.1f}, Price=${price:.2f}")

            return alerts

        except Exception as e:
            logging.error(f"Error in KLM analysis: {e}")
            logging.exception("Detailed error:")
            return None


def main():
    """Test the KLM trading system"""

    print("🧪 KLM Quantitative Trading Engine Test")
    print("=" * 50)

    # Initialize bot
    bot = KLMTradingBot()

    # Run analysis
    print("⚡ Running KLM analysis...")
    alerts = bot.run_once()

    if alerts:
        print(f"\n✅ Analysis complete - {len(alerts)} alert(s) generated")
    else:
        print("\n❌ Analysis failed")


if __name__ == "__main__":
    main()
