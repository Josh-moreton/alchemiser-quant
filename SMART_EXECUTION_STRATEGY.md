# Smart Execution Strategy

## Overview

The smart execution strategy implements canonical order placement for swing trading with intelligent limit orders. It focuses on liquidity-aware anchoring, market timing, and spread validation to achieve better fills without aggressive liquidity consumption.

## Key Features

### 1. Liquidity-Aware Anchoring
- **Buy orders**: Placed just inside the best bid ($bid + $0.01) for queue priority
- **Sell orders**: Placed just inside the best ask ($ask - $0.01) for queue priority  
- Avoids crossing spreads unnecessarily while maintaining execution probability

### 2. Market Timing Rules
- **Avoids 9:30-9:35am ET placement**: Spreads are widest at market open
- Configurable delay period (default: 5 minutes)
- Prevents poor execution during high volatility periods

### 3. Spread and Volume Validation
- **Maximum spread tolerance**: 0.25% by default
- **Minimum volume requirements**: $100 at bid/ask levels
- **Quote freshness**: Requires quotes within 5 seconds
- Orders rejected if conditions not met

### 4. Re-pegging Logic
- **Movement threshold**: Re-peg if market moves >0.1%
- **Maximum re-pegs**: 5 attempts per order
- **Escalation**: Falls back to market orders after max re-pegs for urgent orders

### 5. Async Integration
- Leverages existing real-time pricing service
- Non-blocking execution for multiple concurrent orders
- Event-driven architecture compatible

## Quick Start

### Default Behavior (Smart Execution Enabled)

Smart execution is enabled by default. When you run:

```bash
alchemiser trade
```

The system will automatically use the new liquidity-aware smart execution strategy with volume analysis.

### Checking Current Configuration

To verify that smart execution is enabled, check your logs. You should see messages like:
- "🧠 Using smart execution with liquidity analysis"
- "📊 Volume analysis: [details about bid/ask sizes]"
- "💡 Price adjustment based on volume: [pricing decisions]"

If you see messages like "Using legacy market order execution", then smart execution is disabled.

### Temporarily Disabling Smart Execution

If you need to disable smart execution for troubleshooting, set the environment variable:

```bash
export EXECUTION__ENABLE_SMART_EXECUTION=false
alchemiser trade
```

### Configuration

### Enabling/Disabling Smart Execution

Smart execution is enabled by default. To control this behavior:

**Using Configuration File (.env or environment variable):**
```bash
# Enable smart execution (default)
EXECUTION__ENABLE_SMART_EXECUTION=true

# Disable smart execution (fallback to market orders)
EXECUTION__ENABLE_SMART_EXECUTION=false
```

**Programmatically:**
```python
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

# With smart execution enabled (default)
manager = ExecutionManager.create_with_config(
    api_key="your_key",
    secret_key="your_secret",
    enable_smart_execution=True  # Default
)

# Disable smart execution (legacy market orders)
manager = ExecutionManager.create_with_config(
    api_key="your_key", 
    secret_key="your_secret",
    enable_smart_execution=False
)
```

### Smart Execution Parameters

```python
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

config = ExecutionConfig(
    market_open_delay_minutes=5,           # Wait after 9:30am ET
    max_spread_percent=Decimal("0.25"),    # 0.25% max spread
    repeg_threshold_percent=Decimal("0.10"), # Re-peg trigger
    max_repegs_per_order=5,                # Max re-pegs per order
    min_bid_ask_size=Decimal("100"),       # Min volume at levels
    quote_freshness_seconds=5,             # Quote age limit
    bid_anchor_offset_cents=Decimal("0.01"), # Buy offset
    ask_anchor_offset_cents=Decimal("0.01"), # Sell offset
)
```

## Usage

### Basic Usage
```python
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

# Create with smart execution enabled (default)
manager = ExecutionManager.create_with_config(
    api_key="your_api_key",
    secret_key="your_secret_key",
    paper=True,
    enable_smart_execution=True,
    execution_config=ExecutionConfig()
)

# Execute rebalance plan - automatically uses smart execution
result = manager.execute_rebalance_plan(rebalance_plan)
```

### Legacy Mode
```python
# Disable smart execution for legacy market order behavior
manager = ExecutionManager.create_with_config(
    api_key="your_api_key", 
    secret_key="your_secret_key",
    enable_smart_execution=False
)
```

## Execution Strategies by Urgency

### Low Urgency
- Uses smart limit orders exclusively
- Fails gracefully if quote validation fails
- No market order fallback

### Normal Urgency  
- Prefers smart limit orders
- Falls back to market orders if smart execution fails
- Balanced approach for typical trades

### High Urgency
- Uses smart limit orders when possible
- Immediate market order fallback if quote validation fails
- Prioritizes execution over price optimization

## Architecture Integration

The smart execution strategy integrates seamlessly with existing components:

- **AlpacaManager**: Provides broker connectivity and order placement
- **RealTimePricingService**: Supplies real-time bid/ask quotes and volume data
- **Executor**: Orchestrates execution with both smart and legacy strategies
- **ExecutionManager**: High-level interface with configuration options

## Benefits

1. **Better Fill Prices**: Anchoring to liquidity improves execution quality
2. **Reduced Market Impact**: Avoids crossing spreads unnecessarily  
3. **Market Timing Awareness**: Prevents poor execution during volatile periods
4. **Risk Management**: Validates spread and volume before placement
5. **Flexibility**: Configurable parameters for different trading styles
6. **Backward Compatibility**: Legacy market order execution still available

## Performance Considerations

- **Real-time Data Dependency**: Requires active pricing service for optimal performance
- **Async Execution**: Uses asyncio for non-blocking order placement
- **Memory Efficient**: Automatic cleanup of stale quotes and completed orders
- **Latency Optimized**: Minimal delay between quote validation and order placement

## Monitoring

The execution strategy provides detailed logging and metadata:

- Order placement decisions and reasoning
- Quote validation results
- Market timing restrictions
- Fallback strategy usage
- Re-pegging activity

All execution results include metadata about the strategy used for analysis and optimization.