# Better Orders Implementation Plan

## Executive Summary

This plan outlines how to implement the **retail-optimized execution ladder** from `better orders.md` into The Alchemiser trading system. The proposed improvements align perfectly with our existing infrastructure and will significantly enhance order execution quality for 3x leveraged ETFs.

## Current System Analysis

### Strengths (Already in Place)

- ✅ **WebSocket order monitoring** via `OrderCompletionMonitor`
- ✅ **Real-time bid/ask data** via `RealTimePricingService`
- ✅ **Progressive limit orders** in `SmartExecution.place_limit_or_market()`
- ✅ **Market order fallback** logic
- ✅ **Aggressive sell pricing** (85% toward bid)
- ✅ **Market hours detection** via `is_market_open()`
- ✅ **Spread-aware execution** with validation

### Gaps to Address

- ❌ **Market open timing logic** (9:30-9:35 ET specific behavior)
- ❌ **Spread-based execution decisions** (≤3¢ vs >5¢ thresholds)
- ❌ **2-3 second timeouts** (currently using 10+ seconds)
- ❌ **Aggressive marketable limits** (ask+1 tick, bid-1 tick)
- ❌ **Pre-market spread assessment**
- ❌ **Maximum 2-3 re-pegs** before market order

## Implementation Strategy

### Phase 1: Market Open Timing Engine

**Files to Modify:**

- `the_alchemiser/execution/smart_execution.py`
- `the_alchemiser/utils/market_timing_utils.py` (new)

**Implementation:**

```python
class MarketOpenTimingEngine:
    """Handles market open timing decisions per better orders spec."""
    
    def get_execution_strategy(self, current_time: datetime) -> ExecutionStrategy:
        """
        Determine execution strategy based on market open timing.
        
        Returns:
        - WAIT_FOR_SPREADS: 9:30:00-9:32:00 with wide spreads
        - NORMAL_EXECUTION: 9:32:00-9:35:00 
        - STANDARD_EXECUTION: After 9:35:00
        """
        
    def should_execute_immediately(self, spread_cents: float, time_strategy: ExecutionStrategy) -> bool:
        """
        Apply the spread decision logic:
        - Spread ≤ 2-3¢ → execute immediately
        - Spread > 5¢ → wait 1-2 mins (unless after 9:35)
        """
```

### Phase 2: Fast Execution Parameters

**Files to Modify:**

- `the_alchemiser/utils/progressive_order_utils.py`
- `the_alchemiser/execution/smart_execution.py`

**Changes:**

1. **Reduce timeouts to 2-3 seconds** for leveraged ETFs
2. **Implement aggressive marketable limits** (ask+1 tick, bid-1 tick)
3. **Maximum 2-3 re-peg attempts** before market order

```python
class FastExecutionParams:
    """Execution parameters optimized for leveraged ETFs."""
    
    # Market open specific timeouts
    MARKET_OPEN_TIMEOUT = 2.0  # seconds
    NORMAL_TIMEOUT = 3.0       # seconds
    
    # Re-peg limits
    MAX_REPEGS = 2
    
    # Aggressive pricing
    TICK_AGGRESSION = 1.0  # +1 tick beyond bid/ask
```

### Phase 3: Spread Assessment Module

**Files to Create:**

- `the_alchemiser/utils/spread_assessment.py`

**Features:**

```python
class SpreadAssessment:
    """Pre-market and real-time spread analysis."""
    
    def assess_premarket_conditions(self, symbol: str) -> PreMarketConditions:
        """
        Step 0: Pre-market spread assessment
        - Check bid/ask width
        - Determine max acceptable slippage
        - Plan timing strategy
        """
        
    def get_spread_quality(self, bid: float, ask: float, symbol: str) -> SpreadQuality:
        """
        Classify spread quality:
        - TIGHT: ≤ 2-3¢
        - NORMAL: 3-5¢  
        - WIDE: > 5¢
        """
```

### Phase 4: Aggressive Marketable Limits

**Files to Modify:**

- `the_alchemiser/utils/smart_pricing_handler.py`

**Enhancement:**

```python
def get_aggressive_marketable_limit(self, symbol: str, side: OrderSide, bid: float, ask: float) -> float:
    """
    Calculate aggressive marketable limit prices:
    - BUY: ask + 1 tick (ask + 0.01)
    - SELL: bid - 1 tick (bid - 0.01)
    
    This is the "pro equivalent of hitting the market but with a seatbelt"
    """
```

### Phase 5: Enhanced Order Flow

**Files to Modify:**

- `the_alchemiser/execution/smart_execution.py`

**New Flow:**

```python
def place_better_order(self, symbol: str, qty: float, side: OrderSide) -> Optional[str]:
    """
    Implement the 5-step execution ladder:
    
    Step 0: Pre-check (if before market open)
    Step 1: Open assessment (9:30-9:35 timing)
    Step 2: Aggressive marketable limit (ask+1 tick / bid-1 tick)
    Step 3: Re-peg 1-2 times (2-3 second timeouts)
    Step 4: Market order fallback
    Step 5: Post-fill logging vs NBBO/VWAP
    """
```

## File-by-File Implementation Details

### 1. `the_alchemiser/utils/market_timing_utils.py` (NEW)

```python
#!/usr/bin/env python3
"""
Market Open Timing Utilities

Implements the timing logic from better orders spec for optimal execution
during market open hours (9:30-9:35 ET).
"""

from datetime import datetime, time
from enum import Enum
from typing import Tuple
import pytz

class ExecutionStrategy(Enum):
    WAIT_FOR_SPREADS = "wait_for_spreads"    # 9:30-9:32 with wide spreads
    NORMAL_EXECUTION = "normal_execution"     # 9:32-9:35
    STANDARD_EXECUTION = "standard_execution" # After 9:35

class MarketOpenTimingEngine:
    """Market open timing decisions per better orders specification."""
    
    def __init__(self):
        self.et_tz = pytz.timezone('US/Eastern')
        
    def get_execution_strategy(self, current_time: datetime = None) -> ExecutionStrategy:
        """Determine execution strategy based on market timing."""
        if current_time is None:
            current_time = datetime.now(self.et_tz)
        
        # Convert to ET time
        et_time = current_time.astimezone(self.et_tz).time()
        
        market_open = time(9, 30)   # 9:30 ET
        spreads_normalize = time(9, 32)  # 9:32 ET  
        market_stable = time(9, 35)     # 9:35 ET
        
        if market_open <= et_time < spreads_normalize:
            return ExecutionStrategy.WAIT_FOR_SPREADS
        elif spreads_normalize <= et_time < market_stable:
            return ExecutionStrategy.NORMAL_EXECUTION
        else:
            return ExecutionStrategy.STANDARD_EXECUTION
    
    def should_execute_immediately(self, spread_cents: float, strategy: ExecutionStrategy) -> bool:
        """Apply spread-based execution decisions."""
        if strategy == ExecutionStrategy.STANDARD_EXECUTION:
            return True  # Always execute after 9:35
        
        # Market open logic
        if spread_cents <= 3.0:  # Tight spread
            return True
        elif spread_cents > 5.0:  # Wide spread
            return strategy != ExecutionStrategy.WAIT_FOR_SPREADS
        else:  # Normal spread
            return True
            
    def get_wait_time_seconds(self, strategy: ExecutionStrategy, spread_cents: float) -> int:
        """Get recommended wait time before execution."""
        if strategy == ExecutionStrategy.WAIT_FOR_SPREADS and spread_cents > 5.0:
            return 90  # Wait 1.5 minutes for spreads to normalize
        return 0
```

### 2. `the_alchemiser/utils/spread_assessment.py` (NEW)

```python
#!/usr/bin/env python3
"""
Spread Assessment for Better Order Execution

Implements pre-market and real-time spread analysis to optimize
order timing and pricing decisions.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum
import logging

class SpreadQuality(Enum):
    TIGHT = "tight"      # ≤ 3¢
    NORMAL = "normal"    # 3-5¢
    WIDE = "wide"        # > 5¢

@dataclass
class PreMarketConditions:
    spread_cents: float
    spread_quality: SpreadQuality
    recommended_wait_minutes: int
    max_slippage_bps: float
    
@dataclass  
class SpreadAnalysis:
    spread_cents: float
    spread_quality: SpreadQuality
    spread_bps: float
    midpoint: float

class SpreadAssessment:
    """Pre-market and real-time spread analysis."""
    
    def __init__(self, data_provider):
        self.data_provider = data_provider
    
    def assess_premarket_conditions(self, symbol: str) -> Optional[PreMarketConditions]:
        """
        Step 0: Pre-market spread assessment
        
        Returns recommendations for:
        - Whether to wait for market open
        - Maximum acceptable slippage
        - Timing strategy
        """
        try:
            # Get pre-market bid/ask
            bid, ask = self.data_provider.get_latest_quote(symbol)
            if bid <= 0 or ask <= 0:
                return None
                
            spread_cents = (ask - bid) * 100  # Convert to cents
            spread_quality = self._classify_spread(spread_cents)
            
            # Determine wait time and slippage tolerance
            if spread_quality == SpreadQuality.WIDE:
                wait_minutes = 2  # Wait 1-2 minutes post-open
                max_slippage_bps = 15  # Allow higher slippage for wide spreads
            elif spread_quality == SpreadQuality.NORMAL:
                wait_minutes = 1
                max_slippage_bps = 10
            else:  # TIGHT
                wait_minutes = 0  # Execute immediately
                max_slippage_bps = 5
                
            return PreMarketConditions(
                spread_cents=spread_cents,
                spread_quality=spread_quality,
                recommended_wait_minutes=wait_minutes,
                max_slippage_bps=max_slippage_bps
            )
            
        except Exception as e:
            logging.warning(f"Error assessing pre-market conditions for {symbol}: {e}")
            return None
    
    def analyze_current_spread(self, symbol: str, bid: float, ask: float) -> SpreadAnalysis:
        """Analyze current spread quality for execution decisions."""
        spread_cents = (ask - bid) * 100
        spread_quality = self._classify_spread(spread_cents)
        midpoint = (bid + ask) / 2
        spread_bps = ((ask - bid) / midpoint) * 10000 if midpoint > 0 else 0
        
        return SpreadAnalysis(
            spread_cents=spread_cents,
            spread_quality=spread_quality,
            spread_bps=spread_bps,
            midpoint=midpoint
        )
    
    def _classify_spread(self, spread_cents: float) -> SpreadQuality:
        """Classify spread quality based on cents."""
        if spread_cents <= 3.0:
            return SpreadQuality.TIGHT
        elif spread_cents <= 5.0:
            return SpreadQuality.NORMAL
        else:
            return SpreadQuality.WIDE
```

### 3. `the_alchemiser/execution/smart_execution.py` (MAJOR ENHANCEMENT)

**Add new method:**

```python
def place_better_order(
    self, 
    symbol: str, 
    qty: float, 
    side: OrderSide,
    max_slippage_bps: Optional[float] = None
) -> Optional[str]:
    """
    Implement the 5-step better orders execution ladder.
    
    This is the new primary order placement method that implements
    the professional swing trading execution strategy.
    """
    from the_alchemiser.utils.market_timing_utils import MarketOpenTimingEngine
    from the_alchemiser.utils.spread_assessment import SpreadAssessment
    from rich.console import Console
    
    console = Console()
    timing_engine = MarketOpenTimingEngine()
    spread_assessor = SpreadAssessment(self.alpaca_client.data_provider)
    
    # Step 0: Pre-Check (if before market open)
    if not is_market_open(self.alpaca_client.trading_client):
        console.print(f"[yellow]Market closed - assessing pre-market conditions for {symbol}[/yellow]")
        
        premarket = spread_assessor.assess_premarket_conditions(symbol)
        if premarket:
            console.print(f"[dim]Pre-market spread: {premarket.spread_cents:.1f}¢ ({premarket.spread_quality.value})[/dim]")
            console.print(f"[dim]Recommended wait: {premarket.recommended_wait_minutes} min after open[/dim]")
            
            # Use premarket slippage tolerance if not specified
            if max_slippage_bps is None:
                max_slippage_bps = premarket.max_slippage_bps
    
    # Step 1: Open Assessment 
    strategy = timing_engine.get_execution_strategy()
    console.print(f"[cyan]Execution strategy: {strategy.value}[/cyan]")
    
    # Get current bid/ask
    try:
        quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
        if not quote or len(quote) < 2:
            console.print(f"[yellow]No quote available, using market order[/yellow]")
            return self.alpaca_client.place_market_order(symbol, side, qty=qty)
            
        bid, ask = float(quote[0]), float(quote[1])
        spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
        
        console.print(f"[dim]Current spread: {spread_analysis.spread_cents:.1f}¢ ({spread_analysis.spread_quality.value})[/dim]")
        
        # Check if we should wait for spreads to normalize
        if not timing_engine.should_execute_immediately(spread_analysis.spread_cents, strategy):
            wait_time = timing_engine.get_wait_time_seconds(strategy, spread_analysis.spread_cents)
            console.print(f"[yellow]Wide spread detected, waiting {wait_time}s for normalization[/yellow]")
            import time
            time.sleep(wait_time)
            
            # Re-get quote after waiting
            quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
            if quote and len(quote) >= 2:
                bid, ask = float(quote[0]), float(quote[1])
                spread_analysis = spread_assessor.analyze_current_spread(symbol, bid, ask)
                console.print(f"[dim]Updated spread: {spread_analysis.spread_cents:.1f}¢[/dim]")
        
        # Step 2 & 3: Aggressive Marketable Limit with Re-pegging
        return self._execute_aggressive_limit_sequence(
            symbol, qty, side, bid, ask, strategy, console
        )
        
    except Exception as e:
        logging.error(f"Error in better order execution for {symbol}: {e}")
        # Step 4: Market order fallback
        console.print(f"[yellow]Falling back to market order[/yellow]")
        return self.alpaca_client.place_market_order(symbol, side, qty=qty)

def _execute_aggressive_limit_sequence(
    self, symbol: str, qty: float, side: OrderSide, 
    bid: float, ask: float, strategy: ExecutionStrategy, console
) -> Optional[str]:
    """
    Execute the aggressive marketable limit sequence with re-pegging.
    
    Step 2: Aggressive marketable limit (ask+1 tick / bid-1 tick)
    Step 3: Re-peg 1-2 times (2-3 second timeouts)  
    Step 4: Market order fallback
    """
    from the_alchemiser.utils.market_timing_utils import ExecutionStrategy
    
    # Determine timeout based on strategy and ETF speed
    if strategy == ExecutionStrategy.WAIT_FOR_SPREADS:
        timeout_seconds = 2.0  # Fast execution at market open
    else:
        timeout_seconds = 3.0  # Slightly longer for normal times
        
    max_repegs = 2  # Maximum 2 re-peg attempts
    
    for attempt in range(max_repegs + 1):
        # Calculate aggressive marketable limit price
        if side == OrderSide.BUY:
            # Buy: ask + 1 tick (ask + 1¢)
            limit_price = ask + 0.01
            direction = "above ask"
        else:
            # Sell: bid - 1 tick (bid - 1¢)  
            limit_price = bid - 0.01
            direction = "below bid"
        
        attempt_label = f"Initial order" if attempt == 0 else f"Re-peg #{attempt}"
        console.print(f"[cyan]{attempt_label}: {side.value} {symbol} @ ${limit_price:.2f} ({direction})[/cyan]")
        
        # Place aggressive marketable limit
        order_id = self.alpaca_client.place_limit_order(symbol, qty, side, limit_price)
        if not order_id:
            console.print(f"[red]Failed to place limit order[/red]")
            continue
            
        # Wait for fill with fast timeout (2-3 seconds max)
        order_results = self.alpaca_client.wait_for_order_completion(
            [order_id], max_wait_seconds=timeout_seconds
        )
        
        final_status = order_results.get(order_id, '').lower()
        if 'filled' in final_status:
            console.print(f"[green]✅ {side.value} {symbol} filled @ ${limit_price:.2f} ({attempt_label})[/green]")
            return order_id
        
        # Order not filled - prepare for re-peg if attempts remain
        if attempt < max_repegs:
            console.print(f"[yellow]{attempt_label} not filled, re-pegging...[/yellow]")
            
            # Get fresh quote for re-peg pricing
            fresh_quote = self.alpaca_client.data_provider.get_latest_quote(symbol)
            if fresh_quote and len(fresh_quote) >= 2:
                bid, ask = float(fresh_quote[0]), float(fresh_quote[1])
            else:
                console.print(f"[yellow]No fresh quote, using market order[/yellow]")
                break
        else:
            console.print(f"[yellow]Maximum re-pegs ({max_repegs}) reached[/yellow]")
    
    # Step 4: Market order fallback
    console.print(f"[yellow]All limit attempts failed, using market order[/yellow]")
    return self.alpaca_client.place_market_order(symbol, side, qty=qty)
```

### 4. `the_alchemiser/utils/smart_pricing_handler.py` (ENHANCEMENT)

**Add aggressive marketable limit pricing:**

```python
def get_aggressive_marketable_limit(self, symbol: str, side: OrderSide, bid: float, ask: float) -> float:
    """
    Calculate aggressive marketable limit prices per better orders spec.
    
    This is the "pro equivalent of hitting the market but with a seatbelt":
    - BUY: ask + 1 tick (ask + 0.01)
    - SELL: bid - 1 tick (bid - 0.01)
    
    Args:
        symbol: Stock symbol
        side: BUY or SELL
        bid: Current bid price
        ask: Current ask price
        
    Returns:
        Aggressive limit price that should execute quickly
    """
    if side == OrderSide.BUY:
        # Buy at ask + 1 cent (aggressive but protected)
        return round(ask + 0.01, 2)
    else:
        # Sell at bid - 1 cent (aggressive but protected)
        return round(max(bid - 0.01, 0.01), 2)  # Ensure positive price

def validate_aggressive_limit(self, limit_price: float, market_price: float, 
                            side: OrderSide, max_slippage_bps: float = 20) -> bool:
    """
    Validate that aggressive limit price is within acceptable slippage bounds.
    
    For leveraged ETFs, opportunity cost often outweighs small slippage costs.
    Default 20 bps tolerance is reasonable for 3x ETFs.
    """
    if market_price <= 0:
        return True  # Can't validate without market price
        
    slippage = abs(limit_price - market_price) / market_price * 10000  # bps
    
    if slippage > max_slippage_bps:
        logging.warning(f"Aggressive limit slippage {slippage:.1f}bps exceeds {max_slippage_bps}bps limit")
        return False
        
    return True
```

### 5. `the_alchemiser/execution/portfolio_rebalancer.py` (INTEGRATION)

**Update to use better orders:**

```python
# Replace existing order placement with better orders
def place_order_with_better_execution(self, symbol: str, qty: float, side: OrderSide) -> Optional[str]:
    """Use the new better orders execution for all portfolio rebalancing."""
    
    # Use the enhanced execution engine
    if hasattr(self.bot.order_manager, 'place_better_order'):
        return self.bot.order_manager.place_better_order(symbol, qty, side)
    else:
        # Fallback to existing method
        return self.bot.order_manager.place_limit_or_market(symbol, qty, side)
```

### 6. Configuration Integration

**Add to `the_alchemiser/core/config.py`:**

```python
# Better Orders Configuration
better_orders:
  enabled: true
  leveraged_etf_symbols: ["TQQQ", "SPXL", "TECL", "UVXY", "LABU", "LABD", "SOXL"]
  max_slippage_bps: 20
  aggressive_timeout_seconds: 2.5
  max_repegs: 2
  enable_premarket_assessment: true
```

## Testing Strategy

### 1. Unit Tests

**Files to Create:**

- `tests/test_market_timing_utils.py`
- `tests/test_spread_assessment.py`
- `tests/test_better_orders_execution.py`

### 2. Integration Tests

**Enhance existing:**

- `tests/test_progressive_limit_orders.py` - Add better orders flow
- `tests/test_intelligent_sell_orders.py` - Add aggressive marketable limits

### 3. Live Paper Trading Validation

**Test scenarios:**

- Market open execution (9:30-9:35 ET)
- Wide spread handling (>5¢)
- Fast ETF execution (2-3 second timeouts)
- Re-pegging behavior
- Market order fallback

## Rollout Plan

### Phase 1: Infrastructure (Week 1)

1. Create `market_timing_utils.py`
2. Create `spread_assessment.py`
3. Add configuration support
4. Write unit tests

### Phase 2: Core Integration (Week 2)

1. Enhance `SmartExecution` with `place_better_order()`
2. Update `smart_pricing_handler.py`
3. Integration testing

### Phase 3: Portfolio Integration (Week 3)

1. Update `PortfolioRebalancer` to use better orders
2. Add leveraged ETF symbol detection
3. Live paper trading validation

### Phase 4: Production Deployment (Week 4)

1. Final testing and validation
2. Performance monitoring
3. Gradual rollout to live trading

## Expected Benefits

### 1. Execution Quality

- **Faster fills** via 2-3 second timeouts instead of 10+ seconds
- **Better prices** via aggressive marketable limits (ask+1¢/bid-1¢)
- **Reduced slippage** for fast-moving leveraged ETFs

### 2. Market Open Optimization

- **Smart timing** based on spread conditions (≤3¢ vs >5¢)
- **Avoid poor fills** during volatile market open minutes
- **Professional-grade** execution sequence

### 3. Risk Management

- **Maximum re-peg limits** prevent chasing
- **Slippage controls** protect against excessive costs
- **Market order fallback** ensures execution certainty

### 4. Monitoring & Analytics

- **Fill quality tracking** vs NBBO and VWAP
- **Timing analytics** for strategy optimization
- **Spread condition reporting**

## Risk Mitigation

### 1. Fallback Mechanisms

- Market order fallback if all limit attempts fail
- Existing execution engine remains available
- Configuration-based feature toggle

### 2. Validation & Monitoring

- Slippage validation before order placement
- Real-time execution quality monitoring
- Alert system for unusual execution patterns

### 3. Gradual Rollout

- Paper trading validation first
- Symbol-specific enablement
- Performance comparison against existing system

## Conclusion

This implementation plan leverages our existing infrastructure (WebSocket monitoring, real-time pricing, progressive limits) while adding the professional-grade timing and execution logic from the better orders specification. The modular design ensures minimal risk while providing significant execution quality improvements for leveraged ETF trading.

The key insight is that for fast-moving 3x ETFs, **execution certainty often outweighs small slippage costs**, and the proposed aggressive marketable limits with fast timeouts perfectly align with this principle.
