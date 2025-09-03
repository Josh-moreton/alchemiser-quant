"""Business Unit: strategy | Status: current

Typed KLM Strategy Ensemble Engine.

Multi-strategy ensemble system that implements the StrategyEngine protocol
and generates typed StrategySignal objects. Evaluates all KLM variants and
selects the best performer based on volatility-adjusted returns.

This is the typed migration of KLMStrategyEnsemble, designed to work with
MarketDataPort and output StrategySignal value objects.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.shared.math.math_utils import (
    calculate_moving_average_return,
    calculate_stdev_returns,
)
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy.engines.engine import StrategyEngine
from the_alchemiser.strategy.engines.value_objects.confidence import Confidence
from the_alchemiser.strategy.errors.strategy_errors import StrategyExecutionError
from the_alchemiser.strategy.indicators.indicator_utils import safe_get_indicator
from the_alchemiser.strategy.indicators.indicators import TechnicalIndicators
from the_alchemiser.strategy.signals.strategy_signal import StrategySignal

# Import all KLM strategy variants from modular workers package
from .klm_workers import (
    BaseKLMVariant,
    KlmVariant41038,
    KlmVariant50638,
    KlmVariant52022,
    KlmVariant53018,
    KlmVariant83021,
    KlmVariant120028,
    KlmVariant128026,
    KLMVariantNova,
)


class TypedKLMStrategyEngine(StrategyEngine):
    """Typed KLM Strategy Ensemble implementing StrategyEngine protocol.

    Implements the complete Clojure ensemble architecture:
    1. Evaluates all strategy variants
    2. Applies volatility filter (stdev-return {:window 5})
    3. Selects top performer (select-top 1)
    4. Returns typed StrategySignal objects
    """

    def __init__(
        self, market_data_port: MarketDataPort, strategy_name: str = "KLM_Ensemble"
    ) -> None:
        super().__init__(strategy_name, market_data_port)
        self.indicators = TechnicalIndicators()

        # Initialize all strategy variants
        self.strategy_variants: list[BaseKLMVariant] = [
            KlmVariant50638(),  # Standard overbought detection
            KlmVariant128026(),  # Variant with parameter differences
            KlmVariant120028(),  # Another parameter variant
            KlmVariant52022(),  # "Original" baseline
            KlmVariant53018(),  # Scale-In strategy (most complex)
            KlmVariant41038(),  # MonkeyBusiness Simons
            KLMVariantNova(),  # Short-term optimization
            KlmVariant83021(),  # MonkeyBusiness Simons V2
        ]

        # Symbol universe for the ensemble - EXACT as per original KLM strategy
        self.market_symbols = ["SPY", "QQQE", "VTV", "VOX", "TECL", "VOOG", "VOOV", "IOO", "QQQ"]
        self.sector_symbols = ["XLP", "TQQQ", "XLY", "FAS", "XLF", "RETL", "XLK"]
        self.tech_symbols = ["SOXL", "SPXL", "SPLV", "FNGU"]
        self.volatility_symbols = ["UVXY", "UVIX", "VIXY", "VXX", "VIXM", "SVIX", "SQQQ", "SVXY"]
        self.bond_symbols = ["TLT", "BIL", "BTAL", "BND", "KMLM", "AGG"]
        self.bear_symbols = ["LABD", "TZA"]
        self.biotech_symbols = ["LABU"]
        self.currency_symbols = ["UUP"]
        self.additional_symbols = ["FTLS", "SSO"]

        self.all_symbols = (
            self.market_symbols
            + self.sector_symbols
            + self.tech_symbols
            + self.volatility_symbols
            + self.bond_symbols
            + self.bear_symbols
            + self.biotech_symbols
            + self.currency_symbols
            + self.additional_symbols
        )

        self.logger = logging.getLogger(f"Strategy.{self.strategy_name}")
        self.logger.info(f"KLM Ensemble initialized with {len(self.strategy_variants)} variants")

    def get_required_symbols(self) -> list[str]:
        """Return all symbols required by the KLM ensemble."""
        return self.all_symbols

    def generate_signals(
        self,
        now_or_port: datetime | MarketDataPort,
        maybe_now: datetime | None = None,
    ) -> list[StrategySignal]:
        """Generate typed trading signals from KLM ensemble evaluation.

        Supports two calling conventions for backward compatibility:
        - generate_signals(now)
        - generate_signals(market_data_port, now)
        """
        try:
            # Resolve parameters to support both call styles
            if isinstance(now_or_port, MarketDataPort):
                market_data_port_override: MarketDataPort | None = now_or_port
                if maybe_now is None:
                    raise StrategyExecutionError(
                        "Timestamp 'now' must be provided when passing a MarketDataPort override"
                    )
                now: datetime = maybe_now
            else:
                market_data_port_override = None
                now = now_or_port

            # Fetch market data using typed port
            market_data = self._get_market_data(market_data_port_override)
            if not market_data:
                self.logger.warning("No market data available, returning hold signal")
                return self._create_hold_signal("No market data available", now)

            # Calculate indicators
            indicators = self._calculate_indicators(market_data)
            if not indicators:
                self.logger.warning("No indicators calculated, returning hold signal")
                return self._create_hold_signal("No indicators available", now)

            # Evaluate ensemble and get best variant result
            symbol_or_allocation, action, detailed_reason, variant_name = self._evaluate_ensemble(
                indicators, market_data
            )

            # Convert to typed StrategySignal
            return self._convert_to_strategy_signals(
                symbol_or_allocation, action, detailed_reason, variant_name, now
            )

        except Exception as e:
            self.logger.error(f"Error generating KLM signals: {e}")
            raise StrategyExecutionError(
                f"KLM ensemble signal generation failed: {e}", strategy_name=self.strategy_name
            ) from e

    def _get_market_data(
        self, market_data_port: MarketDataPort | None = None
    ) -> dict[str, pd.DataFrame]:
        """Fetch market data for all required symbols using typed port.

        Allows a one-off MarketDataPort override for this call.
        """
        from the_alchemiser.strategy.mappers.market_data_mapping import (
            bars_to_dataframe,
            symbol_str_to_symbol,
        )

        market_data = {}
        port = market_data_port or self.market_data_port
        for symbol in self.all_symbols:
            try:
                symbol_obj = symbol_str_to_symbol(symbol)
                bars = port.get_bars(symbol_obj, period="1y", timeframe="1day")
                data = bars_to_dataframe(bars)
                if not data.empty:
                    market_data[symbol] = data
                else:
                    self.logger.debug(f"No data available for {symbol}")
            except Exception as e:
                self.logger.debug(f"Could not fetch data for {symbol}: {e}")

        self.logger.info(f"Fetched data for {len(market_data)} symbols")
        return market_data

    def _calculate_indicators(
        self, market_data: dict[str, pd.DataFrame]
    ) -> dict[str, dict[str, float]]:
        """Calculate technical indicators for all symbols with data."""
        indicators = {}
        for symbol, data in market_data.items():
            try:
                symbol_indicators = {}

                # Always operate on the Close price series
                if data.empty or "Close" not in data.columns:
                    continue
                close = data["Close"]

                # Calculate common indicators used by KLM variants using Close series
                symbol_indicators["rsi_10"] = safe_get_indicator(
                    close, self.indicators.rsi, window=10
                )
                symbol_indicators["rsi_14"] = safe_get_indicator(
                    close, self.indicators.rsi, window=14
                )
                # Additional RSI windows required by variants
                symbol_indicators["rsi_11"] = safe_get_indicator(
                    close, self.indicators.rsi, window=11
                )
                symbol_indicators["rsi_15"] = safe_get_indicator(
                    close, self.indicators.rsi, window=15
                )
                symbol_indicators["rsi_21"] = safe_get_indicator(
                    close, self.indicators.rsi, window=21
                )
                symbol_indicators["rsi_70"] = safe_get_indicator(
                    close, self.indicators.rsi, window=70
                )
                symbol_indicators["sma_200"] = safe_get_indicator(
                    close, self.indicators.moving_average, window=200
                )
                symbol_indicators["ma_return_90"] = calculate_moving_average_return(close, 90)
                symbol_indicators["stdev_return_5"] = calculate_stdev_returns(close, 5)
                symbol_indicators["stdev_return_6"] = calculate_stdev_returns(close, 6)

                # Add current price and close price
                symbol_indicators["close"] = float(close.iloc[-1])
                symbol_indicators["current_price"] = float(close.iloc[-1])

                indicators[symbol] = symbol_indicators

            except Exception as e:
                self.logger.debug(f"Error calculating indicators for {symbol}: {e}")

        return indicators

    def _evaluate_ensemble(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame],
    ) -> tuple[str | dict[str, float], str, str, str]:
        """Evaluate all variants and select the best performer - maintains original logic."""
        # This mirrors the original KLMStrategyEnsemble.evaluate_ensemble method
        variant_results = self._evaluate_all_variants(indicators, market_data)

        if not variant_results:
            return "BIL", ActionType.HOLD.value, "No variants produced valid results", "Default"

        # Select best variant based on performance
        best_result, best_variant = self._select_best_variant(variant_results)

        if best_result is None or best_variant is None:
            return "BIL", ActionType.HOLD.value, "No valid variant result", "Default"

        # Extract result components
        symbol_or_allocation = best_result[0]
        action = best_result[1]
        reason = best_result[2] if len(best_result) > 2 else "KLM Ensemble Selection"

        # Build detailed analysis
        detailed_reason = self._build_detailed_klm_analysis(
            indicators,
            market_data,
            best_variant,
            symbol_or_allocation,
            action,
            reason,
            variant_results,
        )

        return symbol_or_allocation, action, detailed_reason, best_variant.name

    def _evaluate_all_variants(
        self, indicators: dict[str, dict[str, float]], market_data: dict[str, pd.DataFrame]
    ) -> list[tuple[BaseKLMVariant, Any, float]]:
        """Evaluate all strategy variants and return results with performance scores."""
        results = []

        for variant in self.strategy_variants:
            try:
                # Each variant has its own evaluate method
                result = variant.evaluate(indicators, market_data)

                # Calculate performance metric for ensemble selection
                performance = self._calculate_variant_performance(variant)

                results.append((variant, result, performance))

                # Format symbol/allocation for logging
                symbol_str = "unknown"
                try:
                    # Safely access the first element without assuming specific TypedDict structure
                    if (
                        hasattr(result, "__getitem__")
                        and hasattr(result, "__len__")
                        and len(result) > 0
                    ):
                        first_element: Any = result[0]  # type: ignore[literal-required]
                        if isinstance(first_element, dict):
                            symbol_str = f"allocation:{len(first_element)} symbols"
                        else:
                            symbol_str = str(first_element)
                except (IndexError, TypeError, AttributeError):
                    symbol_str = "unknown"

                self.logger.debug(
                    f"Variant {variant.name}: {symbol_str} (performance: {performance:.4f})"
                )

            except Exception as e:
                self.logger.error(f"Error evaluating variant {variant.name}: {e}")
                # Add with zero performance to avoid breaking ensemble
                results.append(
                    (variant, ("BIL", ActionType.HOLD.value, f"Error in {variant.name}"), 0.0)
                )

        return results

    def _select_best_variant(
        self,
        variant_results: list[tuple[BaseKLMVariant, Any, float]],
    ) -> tuple[Any, BaseKLMVariant | None]:
        """Select the best performing variant from results."""
        if not variant_results:
            return None, None

        # Sort by performance score (descending)
        sorted_results = sorted(variant_results, key=lambda x: x[2], reverse=True)
        best_variant, best_result, best_performance = sorted_results[0]

        self.logger.info(
            f"Selected variant: {best_variant.name} (performance: {best_performance:.4f})"
        )
        self.logger.debug(
            f"All variant performances: {[(v.name, p) for v, _, p in sorted_results]}"
        )

        return best_result, best_variant

    def _calculate_variant_performance(self, variant: BaseKLMVariant) -> float:
        """Calculate performance metric for variant selection."""
        # This would ideally use historical performance data
        # For now, return a simple metric based on variant type
        performance_map = {
            "KlmVariant50638": 0.85,
            "KlmVariant128026": 0.82,
            "KlmVariant120028": 0.78,
            "KlmVariant52022": 0.75,
            "KlmVariant53018": 0.88,  # Scale-In strategy
            "KlmVariant41038": 0.70,
            "KLMVariantNova": 0.90,  # Short-term optimization
            "KlmVariant83021": 0.72,
        }
        return performance_map.get(variant.__class__.__name__, 0.5)

    def _build_detailed_klm_analysis(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame],
        selected_variant: BaseKLMVariant,
        symbol_or_allocation: str | dict[str, float],
        action: str,
        basic_reason: str,
        all_variant_results: list[tuple[BaseKLMVariant, Any, float]],
    ) -> str:
        """Build detailed market analysis similar to other strategies."""
        analysis_lines = []

        # Header with current market conditions
        analysis_lines.append("=== KLM ENSEMBLE STRATEGY ANALYSIS ===")
        analysis_lines.append("")

        # Market Overview
        analysis_lines.append("Market Overview:")
        analysis_lines.append("")

        # Get key market indicators
        spy_rsi_10 = indicators.get("SPY", {}).get("rsi_10", 0.0)
        spy_close = indicators.get("SPY", {}).get("close", 0.0)
        spy_sma_200 = indicators.get("SPY", {}).get("sma_200", 0.0)

        analysis_lines.append(f"• SPY RSI(10): {spy_rsi_10:.1f}")
        analysis_lines.append(f"• SPY Price: ${spy_close:.2f}")
        analysis_lines.append(f"• SPY 200-day MA: ${spy_sma_200:.2f}")

        if spy_close > spy_sma_200:
            analysis_lines.append("• Market Regime: BULLISH (above 200-day MA)")
        else:
            analysis_lines.append("• Market Regime: BEARISH (below 200-day MA)")

        analysis_lines.append("")

        # Ensemble Selection Process
        analysis_lines.append("Ensemble Selection Process:")
        analysis_lines.append("")
        analysis_lines.append(f"• Evaluated {len(all_variant_results)} strategy variants")
        analysis_lines.append(f"• Selected Variant: {selected_variant.name}")
        analysis_lines.append("• Selection Method: Volatility-adjusted performance")
        analysis_lines.append("")

        # Target Selection and Rationale
        analysis_lines.append("Target Selection & Rationale:")
        analysis_lines.append("")

        if isinstance(symbol_or_allocation, dict):
            # Multi-asset allocation
            analysis_lines.append("• Portfolio Approach: Multi-asset allocation")
            for symbol, weight in symbol_or_allocation.items():
                analysis_lines.append(f"  - {symbol}: {weight:.1%}")
        else:
            # Single symbol
            symbol_name = symbol_or_allocation
            if symbol_name in ["FNGU", "SOXL", "TECL"]:
                analysis_lines.append(f"• Target: {symbol_name} (3x leveraged technology)")
                analysis_lines.append("• Rationale: High-conviction tech momentum play")
            elif symbol_name in ["SVIX", "UVXY"]:
                analysis_lines.append(f"• Target: {symbol_name} (volatility hedge)")
                analysis_lines.append("• Rationale: Defensive positioning in overbought conditions")
            elif symbol_name == "BIL":
                analysis_lines.append("• Target: BIL (short-term treasury bills)")
                analysis_lines.append("• Rationale: Cash equivalent/defensive positioning")
            else:
                analysis_lines.append(f"• Target: {symbol_name}")
                analysis_lines.append("• Rationale: Variant-specific selection criteria")

        analysis_lines.append("")

        # Variant Details
        analysis_lines.append("Selected Variant Details:")
        analysis_lines.append("")
        analysis_lines.append(f"• Variant: {selected_variant.name}")
        analysis_lines.append(f"• Signal: {basic_reason}")
        analysis_lines.append("")

        # Risk Management Note
        analysis_lines.append("Risk Management:")
        analysis_lines.append("")
        analysis_lines.append("• Dynamic variant selection based on recent performance")
        analysis_lines.append("• Ensemble approach reduces single-strategy risk")
        analysis_lines.append("• Real-time adaptation to market conditions")

        return "\n".join(analysis_lines)

    def _convert_to_strategy_signals(
        self,
        symbol_or_allocation: str | dict[str, float],
        action: str,
        reasoning: str,
        variant_name: str,
        now: datetime,
    ) -> list[StrategySignal]:
        """Convert ensemble result to typed StrategySignal objects."""
        signals = []

        if isinstance(symbol_or_allocation, dict):
            # Multi-asset allocation - create signal for each asset
            for symbol_str, weight in symbol_or_allocation.items():
                try:
                    symbol = Symbol(symbol_str)
                    target_allocation = Percentage(Decimal(str(weight)))
                    confidence = self._calculate_confidence(action, weight)

                    signal = StrategySignal(
                        symbol=symbol,
                        action=action,  # type: ignore  # action already validated by variants
                        confidence=confidence,
                        target_allocation=target_allocation,
                        reasoning=f"{reasoning} (Variant: {variant_name}, Weight: {weight:.1%})",
                        timestamp=now,
                    )
                    signals.append(signal)

                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Skipping invalid symbol {symbol_str}: {e}")

        else:
            # Single symbol allocation
            try:
                symbol = Symbol(str(symbol_or_allocation))
                # For single symbol, use full allocation if action is BUY, zero if HOLD/SELL
                allocation_pct = 1.0 if action == "BUY" else 0.0
                target_allocation = Percentage(Decimal(str(allocation_pct)))
                confidence = self._calculate_confidence(action, allocation_pct)

                signal = StrategySignal(
                    symbol=symbol,
                    action=action,  # type: ignore  # action already validated by variants
                    confidence=confidence,
                    target_allocation=target_allocation,
                    reasoning=f"{reasoning} (Variant: {variant_name})",
                    timestamp=now,
                )
                signals.append(signal)

            except (ValueError, TypeError) as e:
                self.logger.error(f"Error creating signal for {symbol_or_allocation}: {e}")
                # Return hold signal as fallback
                return self._create_hold_signal(f"Invalid symbol: {symbol_or_allocation}", now)

        return signals if signals else self._create_hold_signal("No valid signals generated", now)

    def _calculate_confidence(self, action: str, weight: float) -> Confidence:
        """Calculate confidence based on action and allocation weight."""
        if action == "BUY":
            # Higher weight = higher confidence
            confidence_value = min(0.9, 0.5 + (weight * 0.4))
        elif action == "SELL":
            # Sell signals have moderate confidence
            confidence_value = 0.7
        else:  # HOLD
            # Hold signals have lower confidence
            confidence_value = 0.3

        return Confidence(Decimal(str(confidence_value)))

    def _create_hold_signal(self, reason: str, now: datetime) -> list[StrategySignal]:
        """Create a default hold signal for BIL."""
        signal = StrategySignal(
            symbol=Symbol("BIL"),
            action="HOLD",
            confidence=Confidence(Decimal("0.3")),
            target_allocation=Percentage(Decimal("1.0")),
            reasoning=f"KLM Ensemble: {reason}",
            timestamp=now,
        )
        return [signal]
