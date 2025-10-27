# Natural Language DSL Reasoning Parser Enhancement

## Problem Statement

**Current Output:**
```
Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation
```

**Desired Output:**
```
Bullish sentiment. SPY above its 200-day moving average, RSI below 79, so we buy leveraged tech with TQQQ.
```

### Current Limitations

1. **Technical DSL Syntax Leaking**: Output uses checkmarks (✓), arrows (→), and raw operator syntax instead of natural prose
2. **Missing Context**: Doesn't explain the "why" - what market condition are we in?
3. **Lack of Sentiment**: No indication of bullish/bearish/neutral market interpretation
4. **Robotic Structure**: Reads like debug output, not decision reasoning
5. **Missing Action Rationale**: Doesn't explain WHY we pick TQQQ vs other options
6. **Limited Indicator Description**: Shows "RSI(10)>79" instead of "RSI is overbought at 82.5"
7. **No Strategic Narrative**: Doesn't tell the story of the decision path

## Architecture Analysis

### Current Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DSL Evaluator (dsl_evaluator.py)                                │
│    - Evaluates CLJ file using operators                             │
│    - Captures decision_path: list[DecisionNode]                     │
│      * DecisionNode = {condition: str, result: bool, branch: str,   │
│                        values: dict[str, Any]}                      │
│    - Stores in context.decision_path (shared across all contexts)   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Control Flow Operator (operators/control_flow.py)               │
│    - _capture_decision() appends to decision_path                   │
│    - _build_decision_node() formats condition:                      │
│      Example: "rsi(SPY, {:window 10}) > 79"                        │
│    - _extract_indicator_values() adds actual values                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Strategy Engine (strategy_engine.py)                            │
│    - _build_decision_reasoning() converts decision_path to string:  │
│      * Takes first 3 important decisions (where result=True)        │
│      * Formats as: "✓ condition → ✓ condition → X% allocation"     │
│    - Stored in StrategySignal.reasoning field (max 1000 chars)     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Notification Templates (shared/notifications/templates/         │
│    signals.py)                                                      │
│    - _parse_dsl_reasoning_to_human_readable()                       │
│    - Extracts strategy name, conditions, allocation                 │
│    - Parses individual conditions:                                  │
│      * _parse_rsi_condition() → "SPY RSI(10) above 79"            │
│      * _parse_drawdown_condition() → "drawdown check on X"        │
│    - Builds: "Strategy triggered: conditions, allocation set"       │
└─────────────────────────────────────────────────────────────────────┘
```

## Proposed Solution

### Phase 1: Enhanced Decision Path Capture (strategy_v2/engines/dsl/)

**Goal**: Capture richer context during DSL evaluation to enable natural language generation.

#### 1.1 Extended DecisionNode Schema

**File**: `the_alchemiser/strategy_v2/engines/dsl/context.py`

```python
class DecisionNode(TypedDict):
    """Enhanced decision node with narrative context."""
    
    # Existing fields
    condition: str              # Raw condition: "rsi(SPY, {:window 10}) > 79"
    result: bool               # True/False
    branch: str                # "then" or "else"
    values: dict[str, Any]     # Indicator values: {"SPY_rsi_10": 82.5}
    
    # NEW fields for natural language generation
    condition_type: str        # "rsi_check", "ma_comparison", "price_check", etc.
    symbols_involved: list[str] # ["SPY", "TQQQ"]
    operator_type: str         # "greater_than", "less_than", "and", "or"
    threshold: float | None    # 79.0 for "RSI > 79"
    indicator_name: str | None # "rsi", "moving_average", "current_price"
    indicator_params: dict[str, Any] | None  # {"window": 10}
    market_context: str | None # "bullish", "bearish", "neutral", "volatile"
    strategic_intent: str | None # "risk_off", "risk_on", "defensive", etc.
```

**Implementation Steps**:

1. Add new fields to `DecisionNode` TypedDict
2. Update `_build_decision_node()` in `operators/control_flow.py` to populate:
   - Parse condition AST to extract `condition_type`
   - Identify `symbols_involved` from AST traversal
   - Determine `operator_type` from comparison operator node
   - Extract `threshold` from right-hand side of comparisons
   - Capture `indicator_name` and `indicator_params` from function calls

#### 1.2 Market Context Detection

**File**: `the_alchemiser/strategy_v2/engines/dsl/operators/indicators.py` (new module)

```python
class MarketContextAnalyzer:
    """Analyzes indicator values to determine market context."""
    
    def analyze_market_regime(
        self, 
        decisions: list[DecisionNode],
        indicator_service: IndicatorService
    ) -> str:
        """
        Determine overall market regime from decision path.
        
        Returns: "bullish", "bearish", "neutral", "volatile", "defensive"
        
        Logic:
        - If SPY > MA(200) → bullish
        - If SPY < MA(200) → bearish  
        - If VIX > 30 or UVXY allocated → volatile
        - If RSI > 70 on major indices → overbought (still bullish but cautious)
        - If RSI < 30 on major indices → oversold (bearish but potential reversal)
        """
        
    def extract_sentiment_indicators(
        self, 
        decisions: list[DecisionNode]
    ) -> dict[str, Any]:
        """
        Extract key sentiment signals from decisions.
        
        Returns:
        {
            "spy_trend": "above_ma200" | "below_ma200",
            "rsi_state": "overbought" | "oversold" | "neutral",
            "volatility": "high" | "normal" | "low",
            "sector_rotation": "tech" | "defensive" | "mixed"
        }
        """
```

**Integration Point**: 
- Call `MarketContextAnalyzer.analyze_market_regime()` in `_build_decision_node()`
- Store result in `DecisionNode.market_context`
- Use decisions list to determine strategic_intent (risk on/off)

### Phase 2: Natural Language Reasoner (shared/reasoning/)

**Goal**: Transform decision paths into narrative sentences using templates and rules.

#### 2.1 New Module Structure

```
the_alchemiser/shared/reasoning/
├── __init__.py
├── nl_generator.py          # Main natural language generator
├── templates.py             # Sentence templates
├── sentiment_mapper.py      # Maps indicators → sentiment
└── strategic_narrator.py    # Builds strategic narrative
```

#### 2.2 Natural Language Generator

**File**: `the_alchemiser/shared/reasoning/nl_generator.py`

```python
"""Business Unit: shared | Status: current.

Natural language generator for DSL reasoning.
Converts technical decision paths into human-readable narratives.
"""

from typing import Any
from the_alchemiser.strategy_v2.engines.dsl.context import DecisionNode

class NaturalLanguageGenerator:
    """Generates natural language explanations from decision paths."""
    
    def __init__(self):
        self.templates = ReasoningTemplates()
        self.sentiment_mapper = SentimentMapper()
        self.narrator = StrategicNarrator()
    
    def generate_reasoning(
        self,
        decision_path: list[DecisionNode],
        allocation: dict[str, float],
        strategy_name: str,
    ) -> str:
        """
        Generate natural language reasoning from decision path.
        
        Args:
            decision_path: List of decision nodes from DSL evaluation
            allocation: Final allocation dict {symbol: weight}
            strategy_name: Name of strategy (e.g., "Nuclear")
        
        Returns:
            Natural language explanation like:
            "Bullish sentiment. SPY above its 200-day moving average, 
            RSI below 79, so we buy leveraged tech with TQQQ."
        """
        
        # Step 1: Determine market context
        market_context = self._extract_market_context(decision_path)
        
        # Step 2: Build condition narrative
        conditions_narrative = self._build_conditions_narrative(decision_path)
        
        # Step 3: Explain allocation rationale
        allocation_rationale = self._explain_allocation(
            allocation, 
            market_context,
            decision_path
        )
        
        # Step 4: Combine into natural sentence
        return self._compose_narrative(
            market_context,
            conditions_narrative,
            allocation_rationale,
        )
    
    def _extract_market_context(
        self, 
        decision_path: list[DecisionNode]
    ) -> dict[str, Any]:
        """
        Extract market context from decisions.
        
        Returns:
        {
            "sentiment": "bullish" | "bearish" | "neutral",
            "volatility": "high" | "normal" | "low",
            "trend": "above_ma200" | "below_ma200" | "range_bound",
            "rsi_state": "overbought" | "oversold" | "neutral"
        }
        """
        
    def _build_conditions_narrative(
        self, 
        decision_path: list[DecisionNode]
    ) -> str:
        """
        Build narrative from condition checks.
        
        Examples:
        - "SPY above its 200-day moving average, RSI below 79"
        - "TQQQ showing oversold RSI at 28, price above 20-day MA"
        - "Multiple overbought signals, defensive posture warranted"
        """
        
    def _explain_allocation(
        self,
        allocation: dict[str, float],
        market_context: dict[str, Any],
        decision_path: list[DecisionNode],
    ) -> str:
        """
        Explain allocation decision based on context.
        
        Examples:
        - "so we buy leveraged tech with TQQQ"
        - "shifting to defensive positions with BTAL"
        - "taking profits in UVXY as volatility peaks"
        """
        
    def _compose_narrative(
        self,
        market_context: dict[str, Any],
        conditions_narrative: str,
        allocation_rationale: str,
    ) -> str:
        """Compose final natural language narrative."""
        sentiment = market_context["sentiment"]
        
        # Build opening with sentiment
        if sentiment == "bullish":
            opening = "Bullish sentiment."
        elif sentiment == "bearish":
            opening = "Bearish sentiment."
        elif sentiment == "neutral":
            opening = "Neutral market conditions."
        else:  # volatile
            opening = "High volatility detected."
        
        # Combine parts
        parts = [opening, conditions_narrative, allocation_rationale]
        return " ".join(p for p in parts if p)
```

#### 2.3 Reasoning Templates

**File**: `the_alchemiser/shared/reasoning/templates.py`

```python
"""Business Unit: shared | Status: current.

Templates for natural language reasoning generation.
"""

from typing import Any

class ReasoningTemplates:
    """Templates for generating natural language reasoning."""
    
    # Sentiment openings
    SENTIMENT_OPENINGS = {
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
    RSI_TEMPLATES = {
        "overbought_above_threshold": (
            "{symbol} RSI at {value:.1f}, above {threshold} threshold"
        ),
        "oversold_below_threshold": (
            "{symbol} RSI at {value:.1f}, below {threshold} (oversold)"
        ),
        "rsi_neutral": (
            "{symbol} RSI at {value:.1f} (neutral zone)"
        ),
    }
    
    # Moving average templates
    MA_TEMPLATES = {
        "above_ma": "{symbol} above its {period}-day moving average",
        "below_ma": "{symbol} below its {period}-day moving average",
        "near_ma": "{symbol} near its {period}-day moving average",
    }
    
    # Allocation rationale templates
    ALLOCATION_RATIONALES = {
        "bullish_tech": "so we buy leveraged tech with {symbol}",
        "bearish_defensive": "shifting to defensive positions with {symbol}",
        "volatility_hedge": "hedging with {symbol} as volatility spikes",
        "profit_taking": "taking profits in {symbol} as momentum fades",
        "risk_off": "moving to cash equivalents for capital preservation",
        "sector_rotation": "rotating into {symbol} for better risk-adjusted returns",
    }
    
    def get_rsi_description(
        self,
        symbol: str,
        rsi_value: float,
        threshold: float | None,
        operator: str,
    ) -> str:
        """Generate RSI condition description."""
        if threshold is None:
            return self.RSI_TEMPLATES["rsi_neutral"].format(
                symbol=symbol, value=rsi_value
            )
        
        if operator == ">" and rsi_value > 70:
            return self.RSI_TEMPLATES["overbought_above_threshold"].format(
                symbol=symbol, value=rsi_value, threshold=threshold
            )
        elif operator == "<" and rsi_value < 30:
            return self.RSI_TEMPLATES["oversold_below_threshold"].format(
                symbol=symbol, value=rsi_value, threshold=threshold
            )
        else:
            return self.RSI_TEMPLATES["rsi_neutral"].format(
                symbol=symbol, value=rsi_value
            )
    
    def get_ma_description(
        self,
        symbol: str,
        current_price: float,
        ma_price: float,
        period: int,
    ) -> str:
        """Generate moving average description."""
        pct_diff = ((current_price - ma_price) / ma_price) * 100
        
        if abs(pct_diff) < 1.0:  # Within 1%
            return self.MA_TEMPLATES["near_ma"].format(
                symbol=symbol, period=period
            )
        elif pct_diff > 0:
            return self.MA_TEMPLATES["above_ma"].format(
                symbol=symbol, period=period
            )
        else:
            return self.MA_TEMPLATES["below_ma"].format(
                symbol=symbol, period=period
            )
    
    def get_allocation_rationale(
        self,
        allocation: dict[str, float],
        market_context: dict[str, Any],
    ) -> str:
        """Generate allocation rationale based on context."""
        primary_symbol = max(allocation, key=allocation.get)
        sentiment = market_context.get("sentiment", "neutral")
        
        # Determine rationale type from symbol and sentiment
        if primary_symbol in ("TQQQ", "FNGU", "TECL") and sentiment == "bullish":
            template = self.ALLOCATION_RATIONALES["bullish_tech"]
        elif primary_symbol in ("BTAL", "VIXY", "CASH") and sentiment == "bearish":
            template = self.ALLOCATION_RATIONALES["bearish_defensive"]
        elif primary_symbol in ("UVXY", "VXX", "VIXY"):
            template = self.ALLOCATION_RATIONALES["volatility_hedge"]
        else:
            template = self.ALLOCATION_RATIONALES["sector_rotation"]
        
        return template.format(symbol=primary_symbol)
```

### Phase 3: Integration & Migration

#### 3.1 Update Strategy Engine

**File**: `the_alchemiser/strategy_v2/engines/dsl/strategy_engine.py`

**Changes to `_build_decision_reasoning()`**:

```python
def _build_decision_reasoning(
    self,
    decision_path: list[dict[str, Any]] | None,
    weight: float,
    allocation: dict[str, float],  # NEW parameter
    strategy_name: str,             # NEW parameter
) -> str:
    """Build human-readable reasoning from decision path.
    
    NEW: Uses NaturalLanguageGenerator for narrative explanations.
    """
    if not decision_path:
        return f"{weight:.1%} allocation"
    
    # NEW: Use natural language generator
    nl_generator = NaturalLanguageGenerator()
    narrative = nl_generator.generate_reasoning(
        decision_path=decision_path,
        allocation=allocation,
        strategy_name=strategy_name,
    )
    
    # Fallback to old format if NL generation fails
    if not narrative:
        return self._build_legacy_reasoning(decision_path, weight)
    
    return narrative
```

#### 3.2 Update Notification Templates

**File**: `the_alchemiser/shared/notifications/templates/signals.py`

**Changes**:

1. **Remove** current DSL parsing logic (lines 790-1200)
2. **Add** single call to `NaturalLanguageGenerator` if not already generated
3. **Preserve** technical indicator display for gauge tables

```python
@staticmethod
def _parse_dsl_reasoning_to_human_readable(
    reasoning: str,
    technical_indicators: dict[str, TechnicalIndicators] | None = None,
) -> str:
    """Parse DSL reasoning into human-readable text.
    
    NEW: If reasoning is already natural language (from Phase 2),
    return as-is. Otherwise, attempt legacy parsing.
    """
    if not reasoning:
        return ""
    
    # Check if already natural language (no technical symbols)
    if "✓" not in reasoning and "→" not in reasoning:
        # Already natural language from strategy engine
        return reasoning
    
    # Legacy parsing for backwards compatibility
    return SignalsBuilder._parse_dsl_reasoning_legacy(
        reasoning, technical_indicators
    )
```

### Phase 4: Testing & Validation

#### 4.1 Unit Tests

**File**: `tests/shared/reasoning/test_nl_generator.py`

```python
"""Tests for natural language reasoning generator."""

import pytest
from the_alchemiser.shared.reasoning.nl_generator import NaturalLanguageGenerator
from the_alchemiser.strategy_v2.engines.dsl.context import DecisionNode

class TestNaturalLanguageGenerator:
    """Test suite for NL reasoning generation."""
    
    def test_bullish_tech_allocation(self) -> None:
        """Test bullish tech allocation generates correct narrative."""
        decision_path = [
            DecisionNode(
                condition="current_price(SPY) > moving_average(SPY, 200)",
                result=True,
                branch="then",
                values={"SPY_price": 450.0, "SPY_ma_200": 430.0},
                condition_type="ma_comparison",
                symbols_involved=["SPY"],
                market_context="bullish",
            ),
            DecisionNode(
                condition="rsi(SPY, 10) < 79",
                result=True,
                branch="then",
                values={"SPY_rsi_10": 72.0},
                condition_type="rsi_check",
                symbols_involved=["SPY"],
                threshold=79.0,
                operator_type="less_than",
            ),
        ]
        
        allocation = {"TQQQ": 0.75, "BTAL": 0.25}
        
        generator = NaturalLanguageGenerator()
        result = generator.generate_reasoning(
            decision_path=decision_path,
            allocation=allocation,
            strategy_name="Nuclear",
        )
        
        # Assert narrative structure
        assert "bullish" in result.lower() or "strength" in result.lower()
        assert "SPY" in result
        assert "200" in result or "moving average" in result
        assert "TQQQ" in result
        assert len(result) < 500  # Keep concise
    
    def test_bearish_defensive_allocation(self) -> None:
        """Test bearish market generates defensive narrative."""
        # Test implementation...
    
    def test_volatile_hedge_allocation(self) -> None:
        """Test high volatility generates hedge narrative."""
        # Test implementation...
```

#### 4.2 Integration Tests

**File**: `tests/integration/test_end_to_end_reasoning.py`

```python
"""End-to-end tests for DSL evaluation → natural language reasoning."""

def test_nuclear_strategy_natural_language() -> None:
    """Test Nuclear strategy produces natural language reasoning."""
    # 1. Evaluate nuclear.clj strategy
    # 2. Check StrategySignal.reasoning contains natural language
    # 3. Verify no technical symbols (✓, →) in output
    # 4. Confirm sentiment word present (bullish/bearish/neutral/volatile)
    # 5. Validate symbol names and rationale present
```

#### 4.3 Comparison Tests

**File**: `tests/shared/reasoning/test_format_comparison.py`

```python
"""Compare old vs new reasoning formats."""

def test_old_format_vs_new_format() -> None:
    """Compare technical DSL output with natural language output."""
    old_format = "Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"
    
    # Expected new format
    expected_patterns = [
        r"(bullish|bearish|neutral|volatile)",  # Sentiment
        r"SPY",                                  # Symbol mentioned
        r"(moving average|MA|trend|above|below)", # Context
        r"RSI",                                  # Indicator
        r"TQQQ",                                 # Allocation symbol
    ]
    
    new_format = generate_natural_language(old_format)
    
    for pattern in expected_patterns:
        assert re.search(pattern, new_format, re.IGNORECASE)
```

## Implementation Roadmap

### Sprint 1: Foundation (2-3 days)

- [ ] **Task 1.1**: Extend `DecisionNode` schema with new fields
- [ ] **Task 1.2**: Update `_build_decision_node()` to populate new fields
- [ ] **Task 1.3**: Add `MarketContextAnalyzer` module
- [ ] **Task 1.4**: Write unit tests for decision node capture

### Sprint 2: Natural Language Core (3-4 days)

- [ ] **Task 2.1**: Create `shared/reasoning/` module structure
- [ ] **Task 2.2**: Implement `ReasoningTemplates` class
- [ ] **Task 2.3**: Implement `NaturalLanguageGenerator` class
- [ ] **Task 2.4**: Write comprehensive unit tests for NL generation

### Sprint 3: Integration (2-3 days)

- [ ] **Task 3.1**: Update `_build_decision_reasoning()` in strategy engine
- [ ] **Task 3.2**: Update notification template parsing
- [ ] **Task 3.3**: Add backwards compatibility for legacy format
- [ ] **Task 3.4**: Write integration tests

### Sprint 4: Testing & Refinement (2 days)

- [ ] **Task 4.1**: End-to-end testing with all strategies
- [ ] **Task 4.2**: Comparison testing old vs new format
- [ ] **Task 4.3**: Performance benchmarking
- [ ] **Task 4.4**: Documentation updates

## Success Metrics

### Qualitative

1. **Readability**: Non-technical users can understand reasoning
2. **Context**: Explains market conditions and strategic rationale
3. **Conciseness**: Stays under 300 characters for email display
4. **Accuracy**: Correctly interprets indicator values and conditions

### Quantitative

1. **Format Compliance**: 100% of outputs contain sentiment word
2. **Symbol Mention**: 100% of outputs mention allocated symbols
3. **Context Inclusion**: 90%+ include market context (MA, trend, etc.)
4. **Length**: Average length 150-300 characters
5. **Performance**: < 50ms additional latency per signal

## Example Transformations

### Example 1: Bullish Tech

**Before:**
```
Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation
```

**After:**
```
Bullish sentiment. SPY above its 200-day moving average, RSI below 79, so we buy leveraged tech with TQQQ.
```

### Example 2: Bearish Defensive

**Before:**
```
Nuclear: ✓ SPY RSI(10)<30 → ✓ TQQQ drawdown>10% → 100.0% allocation
```

**After:**
```
Bearish sentiment. SPY below its 200-day moving average, TQQQ showing excessive drawdown, shifting to defensive positions with BTAL.
```

### Example 3: Volatile Hedge

**Before:**
```
Nuclear: ✓ SPY RSI(10)>81 → ✓ VIX>30 → 75.0% allocation
```

**After:**
```
High volatility detected. SPY critically overbought at RSI 82, VIX spiking, hedging with UVXY as markets destabilize.
```

### Example 4: Neutral Positioning

**Before:**
```
Quantum: ✓ conditions satisfied → 50.0% allocation
```

**After:**
```
Neutral market conditions. Mixed signals across indicators, maintaining balanced exposure with 50% RGTI allocation.
```

## Rollout Strategy

### Phase 1: Opt-in (Week 1-2)

- Deploy new NL generator
- Add feature flag: `ENABLE_NATURAL_LANGUAGE_REASONING`
- Default to `False` (legacy format)
- Test with development/staging environments

### Phase 2: A/B Testing (Week 3-4)

- Enable for 50% of production signals
- Collect feedback on email reports
- Monitor for parsing errors or regressions
- Compare user comprehension metrics

### Phase 3: Full Rollout (Week 5)

- Enable for 100% of signals
- Keep legacy parser as fallback
- Remove technical DSL symbols from output
- Update all documentation

### Phase 4: Cleanup (Week 6)

- Remove feature flag
- Archive legacy parsing code
- Optimize NL generator performance
- Add more template variations

## Risk Mitigation

### Risk 1: Inaccurate Narratives

**Mitigation:**
- Comprehensive unit test coverage (>90%)
- Manual review of generated narratives
- Fallback to legacy format on generation failure
- Logging of all NL generation attempts

### Risk 2: Performance Degradation

**Mitigation:**
- Profile NL generator (target <50ms)
- Cache common narrative patterns
- Pre-compute market context where possible
- Async generation if needed

### Risk 3: Lost Technical Detail

**Mitigation:**
- Preserve detailed decision path in StrategySignal metadata
- Add "View Technical Details" link in emails
- Keep gauge tables with exact indicator values
- Log full decision path for debugging

### Risk 4: Backwards Compatibility

**Mitigation:**
- Keep legacy parser for 2 release cycles
- Detect format type automatically (✓ and → presence)
- Feature flag for gradual rollout
- Version StrategySignal schema if needed

## Open Questions

1. **Language Localization**: Should we support multiple languages? (Future)
2. **Customization**: Allow users to configure verbosity level? (Future)
3. **Explanation Depth**: Offer "simple" vs "detailed" narrative modes? (Phase 5)
4. **AI Enhancement**: Use LLM for more sophisticated narratives? (Research)

## Conclusion

This enhancement transforms DSL reasoning from technical debug output into user-friendly strategic narratives. By capturing richer context during evaluation and applying template-based natural language generation, we can explain trading decisions in terms traders actually use: sentiment, trends, indicators, and rationale.

The phased approach with feature flags and fallbacks ensures safe rollout while preserving all technical detail for debugging and auditing.

**Estimated Total Effort**: 9-12 days
**Priority**: High (directly improves user experience)
**Complexity**: Medium (well-defined templates, clear structure)
**Risk**: Low (fallback to legacy format, feature flagged)
