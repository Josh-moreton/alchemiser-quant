"""Business Unit: utilities; Status: current.

Typed Nuclear Strategy Engine.

Typed implementation of the Nuclear energy trading strategy that inherits from
StrategyEngine and uses MarketDataPort for data access. Produces StrategySignal
objects with proper confidence values and target allocations.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.domain.market_data.protocols.market_data_port import MarketDataPort
from the_alchemiser.domain.math.indicator_utils import safe_get_indicator
from the_alchemiser.domain.math.indicators import TechnicalIndicators
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.engine import StrategyEngine
from the_alchemiser.domain.strategies.errors.strategy_errors import StrategyExecutionError
from the_alchemiser.domain.strategies.nuclear_logic import evaluate_nuclear_strategy
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.shared.value_objects.symbol import Symbol


class NuclearTypedEngine(StrategyEngine):
    """Typed Nuclear Strategy Engine using MarketDataPort and producing StrategySignal objects."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        super().__init__("Nuclear", market_data_port)
        self.indicators = TechnicalIndicators()
        # pure strategy evaluated via nuclear_logic.evaluate_nuclear_strategy

        # Symbol lists from original Nuclear strategy
        self.market_symbols = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX"]
        self.volatility_symbols = ["UVXY", "BTAL"]
        self.tech_symbols = ["QQQ", "SQQQ", "PSQ", "UPRO"]
        self.bond_symbols = ["TLT", "IEF"]
        self.nuclear_symbols = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]

        # All required symbols
        self._all_symbols = (
            self.market_symbols
            + self.volatility_symbols
            + self.tech_symbols
            + self.bond_symbols
            + self.nuclear_symbols
        )

    def get_required_symbols(self) -> list[str]:
        """Return all symbols required by the Nuclear strategy."""
        return self._all_symbols

    def generate_signals(
        self,
        now_or_port: datetime | MarketDataPort,
        maybe_now: datetime | None = None,
    ) -> list[StrategySignal]:
        """Generate Nuclear strategy signals using MarketDataPort.

        Supports two calling conventions for backward compatibility:
        - generate_signals(now)
        - generate_signals(market_data_port, now)

        Args:
            now_or_port: Either the current timestamp or a MarketDataPort override
            maybe_now: The current timestamp when providing a MarketDataPort override

        Returns:
            List of StrategySignal objects

        Raises:
            StrategyExecutionError: If signal generation fails

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

            # Fetch market data for all symbols
            market_data = self._fetch_market_data(market_data_port_override)
            if not market_data:
                self.logger.warning("No market data available for Nuclear strategy")
                return []

            # Calculate technical indicators
            indicators = self._calculate_indicators(market_data)
            if not indicators:
                self.logger.warning("No indicators calculated for Nuclear strategy")
                return []

            # Evaluate strategy using existing logic
            symbol, action, reason = self._evaluate_nuclear_strategy(indicators, market_data)

            # Expand portfolio recommendations to multiple per-symbol signals
            if symbol == "UVXY_BTAL_PORTFOLIO" and action == "BUY":
                return self._expand_uvxy_btal_portfolio(reason, now)
            if symbol == "NUCLEAR_PORTFOLIO" and action == "BUY":
                return self._expand_nuclear_portfolio(indicators, reason, now)
            if symbol == "BEAR_PORTFOLIO" and action == "BUY":
                return self._expand_bear_portfolio(indicators, market_data, reason, now)

            # Convert to single typed StrategySignal
            signal = self._create_strategy_signal(symbol, action, reason, now)
            return [signal]

        except Exception as e:
            raise StrategyExecutionError(f"Nuclear strategy generation failed: {e}") from e

    def _fetch_market_data(
        self, market_data_port: MarketDataPort | None = None
    ) -> dict[str, pd.DataFrame]:
        """Fetch market data for all required symbols.

        Allows a one-off MarketDataPort override for this call.
        """
        from the_alchemiser.application.mapping.market_data_mapping import (
            bars_to_dataframe,
            symbol_str_to_symbol,
        )

        market_data = {}
        port = market_data_port or self.market_data_port
        for symbol in self._all_symbols:
            try:
                symbol_obj = symbol_str_to_symbol(symbol)
                bars = port.get_bars(symbol_obj, period="1y", timeframe="1day")
                data = bars_to_dataframe(bars)
                if not data.empty:
                    market_data[symbol] = data
                else:
                    self.logger.warning(f"Empty data for {symbol}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch data for {symbol}: {e}")

        return market_data

    def _calculate_indicators(self, market_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Calculate technical indicators for all symbols."""
        indicators = {}
        for symbol, df in market_data.items():
            if df.empty:
                continue

            try:
                close = df["Close"]
                indicators[symbol] = {
                    "rsi_10": safe_get_indicator(close, self.indicators.rsi, 10),
                    "rsi_20": safe_get_indicator(close, self.indicators.rsi, 20),
                    "ma_200": safe_get_indicator(close, self.indicators.moving_average, 200),
                    "ma_20": safe_get_indicator(close, self.indicators.moving_average, 20),
                    "ma_return_90": safe_get_indicator(
                        close, self.indicators.moving_average_return, 90
                    ),
                    "cum_return_60": safe_get_indicator(
                        close, self.indicators.cumulative_return, 60
                    ),
                    "current_price": float(close.iloc[-1]),
                }
            except Exception as e:
                self.logger.warning(f"Failed to calculate indicators for {symbol}: {e}")

        return indicators

    def _evaluate_nuclear_strategy(
        self, indicators: dict[str, Any], market_data: dict[str, Any] | None = None
    ) -> tuple[str, str, str]:
        """Evaluate Nuclear strategy using the shared strategy logic.

        Returns:
            Tuple of (recommended_symbol, action, detailed_reason)

        """
        # Use the new pure evaluation helper
        return evaluate_nuclear_strategy(indicators, market_data)

    def _create_strategy_signal(
        self,
        symbol: str,
        action: str,
        reasoning: str,
        timestamp: datetime,
        target_allocation_override: float | None = None,
    ) -> StrategySignal:
        """Convert legacy signal format to typed StrategySignal."""
        # Normalize symbol - handle portfolio cases and invalid symbol names
        if symbol == "UVXY_BTAL_PORTFOLIO":
            signal_symbol = "UVXY"  # Primary symbol for portfolio signals
        elif symbol == "NUCLEAR_PORTFOLIO":
            signal_symbol = "SMR"  # Primary nuclear stock
        elif "_" in symbol or not symbol.isalpha():
            # Handle other portfolio or invalid symbols - extract first valid symbol
            parts = symbol.replace("_", " ").split()
            valid_symbols = [p for p in parts if p.isalpha() and len(p) <= 5]
            signal_symbol = valid_symbols[0] if valid_symbols else "SPY"
        else:
            signal_symbol = symbol

        # Determine confidence based on signal strength
        confidence_value = self._calculate_confidence(symbol, action, reasoning)

        # Determine target allocation based on signal type, unless overridden
        if target_allocation_override is not None:
            allocation_value = target_allocation_override
        else:
            allocation_value = self._calculate_target_allocation(symbol, action)

        return StrategySignal(
            symbol=Symbol(signal_symbol),
            action=action,  # type: ignore  # Already validated by strategy logic
            confidence=Confidence(Decimal(str(confidence_value))),
            target_allocation=Percentage(Decimal(str(allocation_value))),
            reasoning=reasoning,
            timestamp=timestamp,
        )

    def _calculate_confidence(self, symbol: str, action: str, reasoning: str) -> float:
        """Calculate confidence based on signal characteristics."""
        base_confidence = 0.5

        # High confidence conditions
        if "extremely overbought" in reasoning.lower():
            return 0.9
        if "oversold" in reasoning.lower() and action == "BUY":
            return 0.85
        if "volatility hedge" in reasoning.lower():
            return 0.8
        if "bull market" in reasoning.lower() or "bear market" in reasoning.lower():
            return 0.7
        if action == "HOLD":
            return 0.6

        return base_confidence

    def _calculate_target_allocation(self, symbol: str, action: str) -> float:
        """Calculate target allocation percentage based on signal."""
        if action == "HOLD":
            return 0.0
        if symbol == "UVXY_BTAL_PORTFOLIO" or symbol == "NUCLEAR_PORTFOLIO":
            return 1.0  # 100% allocation for portfolio strategies
        if symbol in ["UVXY", "SQQQ", "PSQ"]:
            return 0.25  # 25% for volatility/hedging positions
        if symbol in ["TQQQ", "UPRO"]:
            return 0.30  # 30% for leveraged growth positions
        if symbol in self.nuclear_symbols:
            return 0.20  # 20% for individual nuclear stocks
        return 0.15  # 15% default allocation

    # --- Portfolio expansion helpers ---

    def _expand_uvxy_btal_portfolio(self, reason: str, now: datetime) -> list[StrategySignal]:
        """Expand UVXY/BTAL defensive portfolio into two signals with fixed weights 75%/25%."""
        return [
            self._create_strategy_signal(
                symbol="UVXY",
                action="BUY",
                reasoning=reason,
                timestamp=now,
                target_allocation_override=0.75,
            ),
            self._create_strategy_signal(
                symbol="BTAL",
                action="BUY",
                reasoning=reason,
                timestamp=now,
                target_allocation_override=0.25,
            ),
        ]

    def _expand_nuclear_portfolio(
        self, indicators: dict[str, Any], reason: str, now: datetime, top_n: int = 3
    ) -> list[StrategySignal]:
        """Build a nuclear equity portfolio and emit per-symbol BUY signals with weights.

        Ranking heuristic: sort available nuclear symbols by 90-day moving-average return (desc)
        and assign equal weights across the top N. Falls back to equal weights across whatever
        nuclear symbols have indicators.
        """
        ranked = self._rank_nuclear_symbols(indicators)
        selected = ranked[:top_n] if ranked else []
        if not selected:
            # Fallback: single primary nuclear symbol if no indicators available
            return [
                self._create_strategy_signal(
                    symbol="SMR",
                    action="BUY",
                    reasoning=reason,
                    timestamp=now,
                    target_allocation_override=1.0,
                )
            ]

        weight = 1.0 / float(len(selected))
        signals: list[StrategySignal] = []
        for sym in selected:
            signals.append(
                self._create_strategy_signal(
                    symbol=sym,
                    action="BUY",
                    reasoning=f"{reason} | Nuclear portfolio constituent",
                    timestamp=now,
                    target_allocation_override=weight,
                )
            )
        return signals

    def _rank_nuclear_symbols(self, indicators: dict[str, Any]) -> list[str]:
        """Return nuclear symbols sorted by ma_return_90 descending (missing treated as very low)."""
        scored: list[tuple[str, float]] = []
        for sym in self.nuclear_symbols:
            if sym in indicators:
                try:
                    score = float(indicators[sym].get("ma_return_90", float("-inf")))
                except Exception:
                    score = float("-inf")
                scored.append((sym, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in scored]

    # --- Bear portfolio helpers (align with Clojure decision tree) ---

    def _expand_bear_portfolio(
        self,
        indicators: dict[str, Any],
        market_data: dict[str, pd.DataFrame] | None,
        reason: str,
        now: datetime,
    ) -> list[StrategySignal]:
        a1 = self._choose_bear1_asset(indicators)
        a2 = self._choose_bear2_asset(indicators)
        assets = [a1, a2]

        # Compute inverse-vol weights from 14-day stdev of daily returns
        vols: list[float] = []
        for sym in assets:
            vol = 1.0
            try:
                if market_data and sym in market_data:
                    df = market_data[sym]
                    if not df.empty and "Close" in df.columns:
                        ret = df["Close"].pct_change().dropna()
                        vol14 = float(ret.tail(14).std())
                        if vol14 and vol14 > 0.0:
                            vol = vol14
            except Exception:
                vol = 1.0
            vols.append(vol)

        inv = [1.0 / v if v > 0.0 else 1.0 for v in vols]
        s = sum(inv) if sum(inv) > 0.0 else 1.0
        weights = [x / s for x in inv]

        signals: list[StrategySignal] = []
        for sym, w in zip(assets, weights, strict=True):
            signals.append(
                self._create_strategy_signal(
                    symbol=sym,
                    action="BUY",
                    reasoning=f"{reason} | Bear portfolio constituent",
                    timestamp=now,
                    target_allocation_override=w,
                )
            )
        return signals

    def _get(self, indicators: dict[str, Any], sym: str, key: str) -> float | None:
        try:
            d = indicators.get(sym)
            if not d:
                return None
            v = d.get(key)
            return float(v) if v is not None else None
        except Exception:
            return None

    def _choose_bear1_asset(self, indicators: dict[str, Any]) -> str:
        psq_rsi10 = self._get(indicators, "PSQ", "rsi_10")
        if psq_rsi10 is not None and psq_rsi10 < 35.0:
            return "SQQQ"
        qqq_cr60 = self._get(indicators, "QQQ", "cum_return_60")
        if qqq_cr60 is not None and qqq_cr60 < -10.0:
            tlt_rsi20 = self._get(indicators, "TLT", "rsi_20")
            psq_rsi20 = self._get(indicators, "PSQ", "rsi_20")
            if tlt_rsi20 is not None and psq_rsi20 is not None and tlt_rsi20 > psq_rsi20:
                return "TQQQ"
            return "PSQ"
        tqqq_price = self._get(indicators, "TQQQ", "current_price")
        tqqq_ma20 = self._get(indicators, "TQQQ", "ma_20")
        if tqqq_price is not None and tqqq_ma20 is not None and tqqq_price > tqqq_ma20:
            tlt_rsi20 = self._get(indicators, "TLT", "rsi_20")
            psq_rsi20 = self._get(indicators, "PSQ", "rsi_20")
            if tlt_rsi20 is not None and psq_rsi20 is not None and tlt_rsi20 > psq_rsi20:
                return "TQQQ"
            return "SQQQ"
        ief_rsi10 = self._get(indicators, "IEF", "rsi_10")
        psq_rsi20 = self._get(indicators, "PSQ", "rsi_20")
        if ief_rsi10 is not None and psq_rsi20 is not None and ief_rsi10 > psq_rsi20:
            return "SQQQ"
        tlt_rsi20 = self._get(indicators, "TLT", "rsi_20")
        if tlt_rsi20 is not None and psq_rsi20 is not None and tlt_rsi20 > psq_rsi20:
            return "QQQ"
        return "SQQQ"

    def _choose_bear2_asset(self, indicators: dict[str, Any]) -> str:
        psq_rsi10 = self._get(indicators, "PSQ", "rsi_10")
        if psq_rsi10 is not None and psq_rsi10 < 35.0:
            return "SQQQ"
        tqqq_price = self._get(indicators, "TQQQ", "current_price")
        tqqq_ma20 = self._get(indicators, "TQQQ", "ma_20")
        if tqqq_price is not None and tqqq_ma20 is not None and tqqq_price > tqqq_ma20:
            tlt_rsi20 = self._get(indicators, "TLT", "rsi_20")
            psq_rsi20 = self._get(indicators, "PSQ", "rsi_20")
            if tlt_rsi20 is not None and psq_rsi20 is not None and tlt_rsi20 > psq_rsi20:
                return "TQQQ"
            return "SQQQ"
        tlt_rsi20 = self._get(indicators, "TLT", "rsi_20")
        psq_rsi20 = self._get(indicators, "PSQ", "rsi_20")
        if tlt_rsi20 is not None and psq_rsi20 is not None and tlt_rsi20 > psq_rsi20:
            return "QQQ"
        return "SQQQ"
