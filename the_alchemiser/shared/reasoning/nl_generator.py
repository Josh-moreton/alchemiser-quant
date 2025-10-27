"""Business Unit: shared | Status: current.

Natural language generator for DSL reasoning.
Converts technical decision paths into human-readable narratives.
"""

from typing import Any

from .templates import ReasoningTemplates


class NaturalLanguageGenerator:
    """Generates natural language explanations from decision paths."""

    def __init__(self) -> None:
        """Initialize natural language generator."""
        self.templates = ReasoningTemplates()

    def generate_reasoning(
        self,
        decision_path: list[dict[str, Any]],
        allocation: dict[str, float],
        strategy_name: str,
    ) -> str:
        """Generate natural language reasoning from decision path.

        Args:
            decision_path: List of decision nodes from DSL evaluation
            allocation: Final allocation dict {symbol: weight}
            strategy_name: Name of strategy (e.g., "Nuclear")

        Returns:
            Natural language explanation like:
            "Bullish sentiment. SPY above its 200-day moving average,
            RSI below 79, so we buy leveraged tech with TQQQ."

        """
        if not decision_path:
            return self._generate_simple_allocation(allocation)

        # Step 1: Determine market context
        market_context = self._extract_market_context(decision_path)

        # Step 2: Build condition narrative
        conditions_narrative = self._build_conditions_narrative(decision_path)

        # Step 3: Explain allocation rationale
        allocation_rationale = self._explain_allocation(allocation, market_context, decision_path)

        # Step 4: Combine into natural sentence
        return self._compose_narrative(
            market_context,
            conditions_narrative,
            allocation_rationale,
        )

    def _extract_market_context(self, decision_path: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract market context from decisions.

        Args:
            decision_path: List of decision nodes

        Returns:
            Dictionary with sentiment, volatility, trend, rsi_state

        """
        context = {
            "sentiment": "neutral",
            "volatility": "normal",
            "trend": "range_bound",
            "rsi_state": "neutral",
        }

        # Look for market context in decision nodes
        for decision in decision_path:
            if decision.get("market_context"):
                context["sentiment"] = decision["market_context"]
                break

        # Infer sentiment from conditions if not explicitly set
        if context["sentiment"] == "neutral":
            context["sentiment"] = self._infer_sentiment_from_decisions(decision_path)

        return context

    def _infer_sentiment_from_decisions(self, decision_path: list[dict[str, Any]]) -> str:
        """Infer market sentiment from decision conditions.

        Args:
            decision_path: List of decision nodes

        Returns:
            Inferred sentiment: "bullish", "bearish", "neutral", or "volatile"

        """
        bullish_signals = 0
        bearish_signals = 0

        for decision in decision_path:
            condition = decision.get("condition", "").lower()
            result = decision.get("result", False)

            # Check for bullish indicators
            if result and ("above" in condition or ">" in condition):
                if "moving" in condition or "ma" in condition:
                    bullish_signals += 1
                elif "rsi" in condition and any(str(th) in condition for th in ["70", "79", "80"]):
                    # RSI > threshold is overbought but still bullish context
                    bullish_signals += 1

            # Check for bearish indicators
            if result and ("below" in condition or "<" in condition):
                if "moving" in condition or "ma" in condition:
                    bearish_signals += 1

            # Check for volatility signals
            if "vix" in condition or "uvxy" in condition or "vixy" in condition:
                return "volatile"

        # Determine overall sentiment
        if bullish_signals > bearish_signals:
            return "bullish"
        elif bearish_signals > bullish_signals:
            return "bearish"
        else:
            return "neutral"

    def _build_conditions_narrative(self, decision_path: list[dict[str, Any]]) -> str:
        """Build narrative from condition checks.

        Args:
            decision_path: List of decision nodes

        Returns:
            Human-readable conditions narrative

        """
        narratives = []

        # Process important decisions (where result=True)
        important_decisions = [d for d in decision_path if d.get("result", False)][:3]

        for decision in important_decisions:
            narrative = self._describe_condition(decision)
            if narrative:
                narratives.append(narrative)

        return ", ".join(narratives) if narratives else ""

    def _describe_condition(self, decision: dict[str, Any]) -> str:
        """Describe a single condition in natural language.

        Args:
            decision: Decision node dict

        Returns:
            Human-readable condition description

        """
        condition = decision.get("condition", "")
        condition_type = decision.get("condition_type", "")

        # Handle RSI conditions
        if "rsi" in condition.lower() or condition_type == "rsi_check":
            return self._describe_rsi_condition(decision)

        # Handle moving average conditions
        if "moving" in condition.lower() or "ma" in condition.lower():
            return self._describe_ma_condition(decision)

        # Generic fallback: simplify the condition string
        return self._simplify_condition_string(condition)

    def _describe_rsi_condition(self, decision: dict[str, Any]) -> str:
        """Describe RSI condition in natural language.

        Args:
            decision: Decision node dict

        Returns:
            Human-readable RSI description

        """
        condition = decision.get("condition", "")
        symbols = decision.get("symbols_involved", [])
        threshold = decision.get("threshold")
        operator = decision.get("operator_type", "")

        # Extract symbol from condition or symbols_involved
        symbol = symbols[0] if symbols else self._extract_symbol_from_string(condition)

        # Try to extract RSI value from values dict
        values = decision.get("values", {})
        rsi_value = None
        for key, val in values.items():
            if "rsi" in key.lower() and isinstance(val, (int, float)):
                rsi_value = float(val)
                break

        if symbol and threshold is not None:
            # Use template-based description
            if rsi_value is not None:
                return self.templates.get_rsi_description(symbol, rsi_value, threshold, operator)
            else:
                # Fallback without value
                if ">" in condition or "greater" in operator:
                    return f"{symbol} RSI above {threshold}"
                else:
                    return f"{symbol} RSI below {threshold}"

        return self._simplify_condition_string(condition)

    def _describe_ma_condition(self, decision: dict[str, Any]) -> str:
        """Describe moving average condition in natural language.

        Args:
            decision: Decision node dict

        Returns:
            Human-readable MA description

        """
        condition = decision.get("condition", "")
        symbols = decision.get("symbols_involved", [])

        # Extract symbol from condition or symbols_involved
        symbol = symbols[0] if symbols else self._extract_symbol_from_string(condition)

        # Extract period from indicator_params or condition string
        indicator_params = decision.get("indicator_params", {})
        period = indicator_params.get("window", 200)  # Default to 200

        # Try to extract from condition string if not in params
        if period == 200 and "200" in condition:
            period = 200
        elif "50" in condition:
            period = 50
        elif "20" in condition:
            period = 20

        # Determine if above or below
        if ">" in condition or "above" in condition.lower():
            return self.templates.MA_TEMPLATES["above_ma"].format(symbol=symbol, period=period)
        elif "<" in condition or "below" in condition.lower():
            return self.templates.MA_TEMPLATES["below_ma"].format(symbol=symbol, period=period)
        else:
            return f"{symbol} near its {period}-day moving average"

    def _simplify_condition_string(self, condition: str) -> str:
        """Simplify a condition string for readability.

        Args:
            condition: Raw condition string

        Returns:
            Simplified condition string

        """
        # Remove excess whitespace
        simplified = " ".join(condition.split())

        # Remove common technical artifacts
        simplified = simplified.replace("{:window", "")
        simplified = simplified.replace("}", "")
        simplified = simplified.replace("(", " ")
        simplified = simplified.replace(")", "")
        simplified = simplified.replace(",", "")

        return simplified.strip()

    def _extract_symbol_from_string(self, text: str) -> str:
        """Extract symbol from text string.

        Args:
            text: Text containing symbol

        Returns:
            Extracted symbol or empty string

        """
        # Common symbols to look for
        common_symbols = ["SPY", "TQQQ", "FNGU", "TECL", "BTAL", "UVXY", "VIXY", "VXX", "RGTI"]

        text_upper = text.upper()
        for symbol in common_symbols:
            if symbol in text_upper:
                return symbol

        return ""

    def _explain_allocation(
        self,
        allocation: dict[str, float],
        market_context: dict[str, Any],
        decision_path: list[dict[str, Any]],
    ) -> str:
        """Explain allocation decision based on context.

        Args:
            allocation: Symbol allocation weights
            market_context: Market context dict
            decision_path: Decision path for additional context

        Returns:
            Human-readable allocation explanation

        """
        return self.templates.get_allocation_rationale(allocation, market_context)

    def _compose_narrative(
        self,
        market_context: dict[str, Any],
        conditions_narrative: str,
        allocation_rationale: str,
    ) -> str:
        """Compose final natural language narrative.

        Args:
            market_context: Market context dict
            conditions_narrative: Conditions description
            allocation_rationale: Allocation explanation

        Returns:
            Complete natural language narrative

        """
        sentiment = market_context.get("sentiment", "neutral")

        # Get sentiment opening
        opening = self.templates.get_sentiment_opening(sentiment)

        # Combine parts
        parts = []
        if opening:
            parts.append(opening)
        if conditions_narrative:
            parts.append(conditions_narrative)
        if allocation_rationale:
            parts.append(allocation_rationale)

        # Join with appropriate punctuation
        if len(parts) == 0:
            return "Market conditions evaluated"
        elif len(parts) == 1:
            return parts[0]
        else:
            # Join first parts with ", " and add final part with ", "
            return " ".join(parts)

    def _generate_simple_allocation(self, allocation: dict[str, float]) -> str:
        """Generate simple allocation description without decision path.

        Args:
            allocation: Symbol allocation weights

        Returns:
            Simple allocation description

        """
        if not allocation:
            return "No allocation"

        primary_symbol = max(allocation, key=lambda k: allocation[k])
        primary_weight = allocation[primary_symbol]

        return f"{primary_weight:.1%} allocation to {primary_symbol}"
