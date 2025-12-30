"""Business Unit: shared | Status: current.

Templates for natural language reasoning generation.
"""

from typing import Any, ClassVar


class ReasoningTemplates:
    """Templates for generating natural language reasoning."""

    # Sentiment openings
    SENTIMENT_OPENINGS: ClassVar[dict[str, list[str]]] = {
        "bullish": [
            "Bullish sentiment.",
            "Market showing strength.",
            "Upward momentum detected.",
        ],
        "bearish": [
            "Bearish sentiment.",
            "Defensive positioning warranted.",
            "Risk-off conditions.",
        ],
        "neutral": [
            "Neutral market conditions.",
            "Mixed signals across indicators.",
            "Range-bound market.",
        ],
        "volatile": [
            "High volatility detected.",
            "Market uncertainty elevated.",
            "Choppy conditions prevail.",
        ],
    }

    # RSI condition templates
    RSI_TEMPLATES: ClassVar[dict[str, str]] = {
        "overbought_above_threshold": "{symbol} RSI at {value:.1f}, above {threshold} threshold",
        "oversold_below_threshold": "{symbol} RSI at {value:.1f}, below {threshold} (oversold)",
        "rsi_neutral": "{symbol} RSI at {value:.1f} (neutral zone)",
    }

    # Moving average templates
    MA_TEMPLATES: ClassVar[dict[str, str]] = {
        "above_ma": "{symbol} above its {period}-day moving average",
        "below_ma": "{symbol} below its {period}-day moving average",
        "near_ma": "{symbol} near its {period}-day moving average",
    }

    # Allocation rationale templates
    ALLOCATION_RATIONALES: ClassVar[dict[str, str]] = {
        "bullish_tech": "so we buy leveraged tech with {symbol}",
        "bearish_defensive": "shifting to defensive positions with {symbol}",
        "volatility_hedge": "hedging with {symbol} as volatility spikes",
        "profit_taking": "taking profits in {symbol} as momentum fades",
        "risk_off": "moving to cash equivalents for capital preservation",
        "sector_rotation": "rotating into {symbol} for better risk-adjusted returns",
    }

    def get_sentiment_opening(self, sentiment: str) -> str:
        """Get opening sentence for given sentiment.

        Args:
            sentiment: Market sentiment ("bullish", "bearish", "neutral", "volatile")

        Returns:
            Opening sentence for the sentiment

        """
        openings = self.SENTIMENT_OPENINGS.get(sentiment, self.SENTIMENT_OPENINGS["neutral"])
        return openings[0]  # Use first template for consistency

    def get_rsi_description(
        self,
        symbol: str,
        rsi_value: float,
        threshold: float | None,
        operator: str,
    ) -> str:
        """Generate RSI condition description.

        Args:
            symbol: Stock symbol
            rsi_value: Current RSI value
            threshold: Threshold for comparison
            operator: Comparison operator (">", "<", etc.)

        Returns:
            Human-readable RSI description

        """
        if threshold is None:
            return self.RSI_TEMPLATES["rsi_neutral"].format(symbol=symbol, value=rsi_value)

        if operator in (">", "greater_than") and rsi_value > 70:
            return self.RSI_TEMPLATES["overbought_above_threshold"].format(
                symbol=symbol, value=rsi_value, threshold=threshold
            )
        if operator in ("<", "less_than") and rsi_value < 30:
            return self.RSI_TEMPLATES["oversold_below_threshold"].format(
                symbol=symbol, value=rsi_value, threshold=threshold
            )
        return self.RSI_TEMPLATES["rsi_neutral"].format(symbol=symbol, value=rsi_value)

    def get_ma_description(
        self,
        symbol: str,
        current_price: float,
        ma_price: float,
        period: int,
    ) -> str:
        """Generate moving average description.

        Args:
            symbol: Stock symbol
            current_price: Current price
            ma_price: Moving average price
            period: MA period (e.g., 200)

        Returns:
            Human-readable MA description

        """
        import math

        if math.isclose(ma_price, 0, abs_tol=1e-9) or ma_price == 0:
            return f"{symbol} moving average unavailable"

        pct_diff = ((current_price - ma_price) / ma_price) * 100

        if abs(pct_diff) < 1.0:  # Within 1%
            return self.MA_TEMPLATES["near_ma"].format(symbol=symbol, period=period)
        if pct_diff > 0:
            return self.MA_TEMPLATES["above_ma"].format(symbol=symbol, period=period)
        return self.MA_TEMPLATES["below_ma"].format(symbol=symbol, period=period)

    def get_allocation_rationale(
        self,
        allocation: dict[str, float],
        market_context: dict[str, Any],
    ) -> str:
        """Generate allocation rationale based on context.

        Args:
            allocation: Symbol allocation weights
            market_context: Market context dict with sentiment, volatility, etc.

        Returns:
            Human-readable allocation rationale

        """
        if not allocation:
            return ""

        primary_symbol = max(allocation, key=lambda k: allocation[k])
        sentiment = market_context.get("sentiment", "neutral")

        # Common leveraged tech ETFs
        leveraged_tech = {"TQQQ", "FNGU", "TECL", "SOXL", "NVDL"}
        # Common defensive/volatility instruments
        defensive = {"BTAL", "VIXY", "CASH", "BIL", "SHY", "SHV"}
        # Common volatility hedges
        volatility_hedges = {"UVXY", "VXX", "VIXY", "SVIX"}

        # Determine rationale type from symbol and sentiment
        if primary_symbol in leveraged_tech and sentiment == "bullish":
            template = self.ALLOCATION_RATIONALES["bullish_tech"]
        elif primary_symbol in defensive and sentiment == "bearish":
            template = self.ALLOCATION_RATIONALES["bearish_defensive"]
        elif primary_symbol in volatility_hedges:
            template = self.ALLOCATION_RATIONALES["volatility_hedge"]
        else:
            template = self.ALLOCATION_RATIONALES["sector_rotation"]

        return template.format(symbol=primary_symbol)
