"""Business Unit: strategy | Status: current.

KLM Strategy Engine.

Simplified KLM strategy implementing the StrategyEngine protocol.
Directly implements the original CLJ specification without variant abstractions.

This implements the exact "Simons KMLM switcher (single pops)" logic
with exact parity to the original Clojure specification.
"""

from __future__ import annotations

import decimal
import logging
import math
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd

from the_alchemiser.shared.config.confidence_config import ConfidenceConfig
from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.math.math_utils import (
    calculate_moving_average_return,
    calculate_stdev_returns,
)
from the_alchemiser.shared.types import Confidence, StrategyEngine, StrategySignal
from the_alchemiser.shared.types.exceptions import StrategyExecutionError
from the_alchemiser.shared.types.market_data import bars_to_dataframe
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy_v2.indicators.indicator_utils import safe_get_indicator
from the_alchemiser.strategy_v2.indicators.indicators import TechnicalIndicators


class KLMEngine(StrategyEngine):
    """KLM Strategy Engine implementing StrategyEngine protocol.

    Directly implements the Original CLJ strategy specification:
    "Simons KMLM switcher (single pops) | BT 4/13/22 = A.R. 466% / D.D. 22% V2"

    Implements exact nested if-else structure:
    1. UVXY guard-rail path (11-step overbought detection)
    2. Combined Pop Bot (oversold rotations)
    3. KMLM switcher (XLK vs KMLM comparison)
    """

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize KLM strategy engine."""
        self.market_data_port = market_data_port
        self.strategy_name = "KLM_Original"
        self.logger = logging.getLogger(f"Strategy.{self.strategy_name}")
        self.indicators = TechnicalIndicators()
        self.confidence_config = ConfidenceConfig.default()

        # Required symbols from CLJ specification
        self.required_symbols = [
            # Overbought detection
            "QQQE",
            "VTV",
            "VOX",
            "TECL",
            "VOOG",
            "VOOV",
            "XLP",
            "TQQQ",
            "XLY",
            "FAS",
            "SPY",
            # Hedge symbol
            "UVXY",
            # Combined Pop Bot
            "SOXL",
            "SPXL",
            "LABU",
            # KMLM Switcher
            "XLK",
            "KMLM",
            "SVIX",
            "SQQQ",
            "TLT",
        ]

        self.logger.info("KLM Engine initialized for Original CLJ strategy")

    def get_required_symbols(self) -> list[str]:
        """Return all symbols required by the KLM strategy."""
        return self.required_symbols

    def generate_signals(
        self,
        now_or_port: datetime | MarketDataPort,
        maybe_now: datetime | None = None,
    ) -> list[StrategySignal]:
        """Generate typed trading signals from KLM strategy evaluation.

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

            # Evaluate CLJ strategy directly
            decision = self._evaluate_klm_strategy(indicators)

            # Convert to typed StrategySignal
            return self._convert_to_strategy_signals(decision, now)

        except Exception as e:
            self.logger.error(f"Error generating KLM signals: {e}")
            raise StrategyExecutionError(
                f"KLM strategy signal generation failed: {e}",
                strategy_name=self.strategy_name,
            ) from e

    def _evaluate_klm_strategy(self, indicators: dict[str, TechnicalIndicatorDTO]) -> KLMDecision:
        """Evaluate KLM strategy - EXACT match to CLJ specification.

        Implements the exact nested if-else structure from 'klm original.clj':
        1. UVXY guard-rail path (11-step overbought detection)
        2. Combined Pop Bot (oversold rotations including LABU)
        3. KMLM switcher (XLK vs KMLM comparison)
        """
        # Step 1: UVXY Guard-rail Path (11-step overbought detection)
        overbought_result = self._check_overbought_conditions(indicators)
        if overbought_result is not None:
            return overbought_result

        # Step 2: Combined Pop Bot (exact CLJ sequence including LABU)
        pop_bot_result = self._evaluate_combined_pop_bot(indicators)
        if pop_bot_result is not None:
            return pop_bot_result

        # Step 3: KMLM Switcher (XLK vs KMLM RSI comparison)
        return self._evaluate_kmlm_switcher(indicators)

    def _check_overbought_conditions(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision | None:
        """Complete 11-step overbought detection chain from CLJ.

        Sequence: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY
        Returns KLMDecision if overbought condition met, None otherwise.
        """
        # Step 1: QQQE RSI(10) > 79
        if "QQQE" in indicators and (indicators["QQQE"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "QQQE RSI(10) > 79 → UVXY")

        # Step 2: VTV RSI(10) > 79
        if "VTV" in indicators and (indicators["VTV"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "VTV RSI(10) > 79 → UVXY")

        # Step 3: VOX RSI(10) > 79
        if "VOX" in indicators and (indicators["VOX"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "VOX RSI(10) > 79 → UVXY")

        # Step 4: TECL RSI(10) > 79
        if "TECL" in indicators and (indicators["TECL"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "TECL RSI(10) > 79 → UVXY")

        # Step 5: VOOG RSI(10) > 79
        if "VOOG" in indicators and (indicators["VOOG"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "VOOG RSI(10) > 79 → UVXY")

        # Step 6: VOOV RSI(10) > 79
        if "VOOV" in indicators and (indicators["VOOV"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "VOOV RSI(10) > 79 → UVXY")

        # Step 7: XLP RSI(10) > 75 (different threshold!)
        if "XLP" in indicators and (indicators["XLP"].rsi_10 or 0) > 75:
            return self._create_klm_decision("UVXY", "BUY", "XLP RSI(10) > 75 → UVXY")

        # Step 8: TQQQ RSI(10) > 79
        if "TQQQ" in indicators and (indicators["TQQQ"].rsi_10 or 0) > 79:
            return self._create_klm_decision("UVXY", "BUY", "TQQQ RSI(10) > 79 → UVXY")

        # Step 9: XLY RSI(10) > 80 (different threshold!)
        if "XLY" in indicators and (indicators["XLY"].rsi_10 or 0) > 80:
            return self._create_klm_decision("UVXY", "BUY", "XLY RSI(10) > 80 → UVXY")

        # Step 10: FAS RSI(10) > 80
        if "FAS" in indicators and (indicators["FAS"].rsi_10 or 0) > 80:
            return self._create_klm_decision("UVXY", "BUY", "FAS RSI(10) > 80 → UVXY")

        # Step 11: SPY RSI(10) > 80
        if "SPY" in indicators and (indicators["SPY"].rsi_10 or 0) > 80:
            return self._create_klm_decision("UVXY", "BUY", "SPY RSI(10) > 80 → UVXY")

        # No overbought conditions met
        return None

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision | None:
        """Evaluate Combined Pop Bot with EXACT CLJ sequence including LABU.

        CLJ sequence:
        1. TQQQ RSI(10) < 30 → TECL
        2. SOXL RSI(10) < 30 → SOXL
        3. SPXL RSI(10) < 30 → SPXL
        4. LABU RSI(10) < 25 → LABU (different threshold!)
        """
        # Priority 1: TQQQ oversold check
        if "TQQQ" in indicators:
            tqqq_rsi = indicators["TQQQ"].rsi_10 or 50
            if tqqq_rsi < 30:
                return self._create_klm_decision(
                    "TECL",
                    ActionType.BUY.value,
                    f"Pop Bot: TQQQ RSI(10) {tqqq_rsi:.1f} < 30 → TECL",
                )

        # Priority 2: SOXL oversold check
        if "SOXL" in indicators:
            soxl_rsi = indicators["SOXL"].rsi_10 or 50
            if soxl_rsi < 30:
                return self._create_klm_decision(
                    "SOXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SOXL RSI(10) {soxl_rsi:.1f} < 30 → SOXL",
                )

        # Priority 3: SPXL oversold check
        if "SPXL" in indicators:
            spxl_rsi = indicators["SPXL"].rsi_10 or 50
            if spxl_rsi < 30:
                return self._create_klm_decision(
                    "SPXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SPXL RSI(10) {spxl_rsi:.1f} < 30 → SPXL",
                )

        # Priority 4: LABU oversold check (threshold 25, not 30!)
        if "LABU" in indicators:
            labu_rsi = indicators["LABU"].rsi_10 or 50
            if labu_rsi < 25:
                return self._create_klm_decision(
                    "LABU",
                    ActionType.BUY.value,
                    f"Pop Bot: LABU RSI(10) {labu_rsi:.1f} < 25 → LABU",
                )

        # No oversold conditions met
        return None

    def _evaluate_kmlm_switcher(self, indicators: dict[str, TechnicalIndicatorDTO]) -> KLMDecision:
        """KMLM Switcher - exact CLJ implementation.

        Logic from CLJ:
        - Compare RSI(XLK) vs RSI(KMLM) (both window 10)
        - If XLK RSI > KMLM RSI:
          - filter by RSI, select-bottom 2 from [TECL, SOXL, SVIX]
          - weight-equal across selected two
        - Else (L/S Rotator):
          - filter by RSI, select-top 1 from [SQQQ, TLT]
          - 100% weight to selected one
        """
        # Get RSI values for comparison (coalesce None to float defaults)
        xlk_ti = indicators.get("XLK")
        kmlm_ti = indicators.get("KMLM")
        xlk_rsi: float = (
            float(xlk_ti.rsi_10) if (xlk_ti is not None and xlk_ti.rsi_10 is not None) else 50.0
        )
        kmlm_rsi: float = (
            float(kmlm_ti.rsi_10) if (kmlm_ti is not None and kmlm_ti.rsi_10 is not None) else 50.0
        )

        if xlk_rsi > kmlm_rsi:
            # Tech branch: select-bottom 2 from [TECL, SOXL, SVIX]
            tech_symbols = ["TECL", "SOXL", "SVIX"]
            selected_symbols = self._filter_and_select_by_rsi(tech_symbols, indicators, "bottom", 2)

            if selected_symbols:
                # weight-equal across selected symbols
                equal_weight = 1.0 / len(selected_symbols)
                allocation = dict.fromkeys(selected_symbols, equal_weight)
                reasoning = (
                    f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) > KMLM RSI({kmlm_rsi:.1f}) "
                    f"→ Tech branch, selected {selected_symbols}"
                )
                return self._create_klm_decision(allocation, ActionType.BUY.value, reasoning)
            # Fallback if no tech symbols available
            return self._create_klm_decision(
                "TECL",
                ActionType.BUY.value,
                f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) > KMLM RSI({kmlm_rsi:.1f}) → TECL (fallback)",
            )
        # L/S Rotator: select-top 1 from [SQQQ, TLT]
        ls_symbols = ["SQQQ", "TLT"]
        selected_symbols = self._filter_and_select_by_rsi(ls_symbols, indicators, "top", 1)

        if selected_symbols:
            # 100% weight to selected symbol
            selected_symbol = selected_symbols[0]
            reasoning = (
                f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) ≤ KMLM RSI({kmlm_rsi:.1f}) "
                f"→ L/S Rotator, selected {selected_symbol}"
            )
            return self._create_klm_decision(selected_symbol, ActionType.BUY.value, reasoning)
        # Fallback if no L/S symbols available
        return self._create_klm_decision(
            "TLT",
            ActionType.BUY.value,
            f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) ≤ KMLM RSI({kmlm_rsi:.1f}) → TLT (fallback)",
        )

    def _filter_and_select_by_rsi(
        self,
        candidates: list[str],
        indicators: dict[str, TechnicalIndicatorDTO],
        selection_type: str,
        count: int,
    ) -> list[str]:
        """Filter candidates by RSI and select top/bottom N.

        Implements the exact filter/select logic from CLJ:
        - filter by RSI (window 10) - only include symbols with valid RSI
        - select-bottom N or select-top N based on RSI values
        - Deterministic tie-breaking using symbol name (alphabetical)
        """
        # Filter to only symbols with valid RSI data
        valid_candidates = []
        for symbol in candidates:
            if symbol in indicators:
                rsi_value = indicators[symbol].rsi_10
                if rsi_value is not None and 0 <= rsi_value <= 100:
                    valid_candidates.append((symbol, rsi_value))

        if not valid_candidates:
            return []

        # Sort by RSI value, then by symbol name for deterministic tie-breaking
        if selection_type == "bottom":
            # Sort ascending (lowest RSI first), then alphabetically
            sorted_candidates = sorted(valid_candidates, key=lambda x: (x[1], x[0]))
        else:  # "top"
            # Sort descending (highest RSI first), then alphabetically
            sorted_candidates = sorted(valid_candidates, key=lambda x: (-x[1], x[0]))

        # Select top N
        selected = sorted_candidates[:count]
        return [symbol for symbol, _ in selected]

    def _create_klm_decision(
        self, symbol_or_allocation: str | dict[str, float], action: str, reasoning: str
    ) -> KLMDecision:
        """Create a KLMDecision object."""
        return {
            "symbol": symbol_or_allocation,
            "action": action,  # type: ignore[typeddict-item]
            "reasoning": reasoning,
        }

    def _get_market_data(
        self, market_data_port: MarketDataPort | None = None
    ) -> dict[str, pd.DataFrame]:
        """Fetch market data for all required symbols using typed port."""

        def symbol_str_to_symbol(symbol_str: str) -> Symbol:
            from the_alchemiser.shared.value_objects.symbol import Symbol

            return Symbol(symbol_str)

        market_data = {}
        port = market_data_port or self.market_data_port
        for symbol in self.required_symbols:
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
    ) -> dict[str, TechnicalIndicatorDTO]:
        """Calculate technical indicators for all symbols with data."""
        indicators: dict[str, TechnicalIndicatorDTO] = {}
        for symbol, data in market_data.items():
            try:
                # Always operate on the Close price series
                if data.empty or "Close" not in data.columns:
                    continue
                close = data["Close"]

                # Calculate RSI indicators
                rsi_10 = safe_get_indicator(close, self.indicators.rsi, window=10)
                rsi_14 = safe_get_indicator(close, self.indicators.rsi, window=14)
                rsi_21 = safe_get_indicator(close, self.indicators.rsi, window=21)

                # Calculate moving averages
                ma_200 = safe_get_indicator(close, self.indicators.moving_average, window=200)

                # Calculate returns
                ma_return_90 = calculate_moving_average_return(close, 90)
                stdev_return_6 = calculate_stdev_returns(close, 6)

                # Create TechnicalIndicatorDTO
                indicators[symbol] = TechnicalIndicatorDTO(
                    symbol=symbol,
                    timestamp=datetime.now(UTC),
                    current_price=Decimal(str(close.iloc[-1])),
                    rsi_10=rsi_10,
                    rsi_14=rsi_14,
                    rsi_21=rsi_21,
                    ma_200=ma_200,
                    ma_return_90=ma_return_90,
                    stdev_return_6=stdev_return_6,
                    metadata={},
                    data_source="klm_engine",
                )

            except Exception as e:
                self.logger.debug(f"Error calculating indicators for {symbol}: {e}")

        return indicators

    def _convert_to_strategy_signals(
        self, decision: KLMDecision, now: datetime
    ) -> list[StrategySignal]:
        """Convert KLM decision to typed StrategySignal objects."""
        signals = []
        symbol_or_allocation = decision["symbol"]
        action = decision["action"]
        reasoning = decision["reasoning"]

        if isinstance(symbol_or_allocation, dict):
            # Multi-asset allocation - create signal for each asset
            for symbol_str, weight in symbol_or_allocation.items():
                try:
                    # Validate weight is a valid number
                    if weight is None or not isinstance(weight, int | float) or math.isnan(weight):
                        self.logger.warning(f"Invalid weight for {symbol_str}: {weight}, skipping")
                        continue

                    symbol = Symbol(symbol_str)
                    target_allocation = Percentage(Decimal(str(weight)))
                    confidence = self._calculate_confidence(action, weight)

                    signal = StrategySignal(
                        symbol=symbol,
                        action=action,
                        confidence=confidence,
                        target_allocation=target_allocation,
                        reasoning=f"{reasoning} (Weight: {weight:.1%})",
                        timestamp=now,
                    )
                    signals.append(signal)

                except (ValueError, TypeError, decimal.InvalidOperation) as e:
                    self.logger.warning(
                        f"Skipping invalid symbol {symbol_str} with weight {weight}: {e}"
                    )
                    continue

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
                    action=action,
                    confidence=confidence,
                    target_allocation=target_allocation,
                    reasoning=reasoning,
                    timestamp=now,
                )
                signals.append(signal)

            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                self.logger.error(
                    f"Error creating signal for {symbol_or_allocation} with action {action}: {e}"
                )
                # Return hold signal as fallback
                return self._create_hold_signal(f"Invalid symbol: {symbol_or_allocation}", now)

        return signals if signals else self._create_hold_signal("No valid signals generated", now)

    def _calculate_confidence(self, action: str, weight: float) -> Confidence:
        """Calculate confidence based on action and allocation weight."""
        config = self.confidence_config.klm

        # Validate weight is a valid number
        if weight is None or not isinstance(weight, int | float) or math.isnan(weight):
            self.logger.warning(
                f"Invalid weight for confidence calculation: {weight}, using default"
            )
            weight = 0.0

        if action == "BUY":
            # Start with base confidence and apply weight adjustment
            confidence_value = float(config.base_confidence)

            # Apply weight adjustment
            weight_adjustment = weight * float(config.weight_adjustment_factor)
            confidence_value += weight_adjustment

            # Boost for high-weight positions
            if weight >= float(config.high_weight_threshold):
                confidence_value += float(config.high_weight_boost)

            # Clamp to valid range
            confidence_value = max(
                float(config.min_confidence),
                min(float(config.max_confidence), confidence_value),
            )

        elif action == "SELL":
            # Sell signals have moderate confidence
            confidence_value = float(config.sell_confidence)
        else:  # HOLD
            # Hold signals have moderate confidence
            confidence_value = float(config.hold_confidence)

        # Ensure confidence_value is valid before Decimal conversion
        if (
            confidence_value is None
            or not isinstance(confidence_value, int | float)
            or math.isnan(confidence_value)
        ):
            self.logger.warning(f"Invalid confidence value: {confidence_value}, using default 0.5")
            confidence_value = 0.5

        try:
            return Confidence(Decimal(str(confidence_value)))
        except (decimal.InvalidOperation, ValueError) as e:
            self.logger.warning(
                f"Failed to convert confidence value {confidence_value} to Decimal: {e}, using default"
            )
            return Confidence(Decimal("0.5"))

    def _create_hold_signal(self, reason: str, now: datetime) -> list[StrategySignal]:
        """Create a default hold signal for BIL."""
        config = self.confidence_config.klm
        signal = StrategySignal(
            symbol=Symbol("BIL"),
            action="HOLD",
            confidence=Confidence(config.hold_confidence),
            target_allocation=Percentage(Decimal("1.0")),
            reasoning=f"KLM Strategy: {reason}",
            timestamp=now,
        )
        return [signal]

    def validate_signals(self, signals: list[StrategySignal]) -> None:
        """Validate generated signals.

        Args:
            signals: List of signals to validate

        Raises:
            ValueError: If signals are invalid

        """
        for signal in signals:
            if not isinstance(signal, StrategySignal):
                raise ValueError(f"Invalid signal type: {type(signal)}")
            if signal.confidence.value < 0 or signal.confidence.value > 1:
                raise ValueError(f"Invalid confidence value: {signal.confidence.value}")
