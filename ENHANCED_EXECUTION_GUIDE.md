# Enhanced Smart Execution Strategy - Implementation Guide

## Overview

The enhanced smart execution strategy implements settlement-aware, multi-symbol execution with bulk pricing subscriptions and proper sell-first, buy-second workflow coordination.

## Key Features

### 1. Multi-Symbol Bulk Subscription
```python
# Automatically extracts all symbols and bulk-subscribes for efficient pricing
all_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
subscription_results = pricing_service.subscribe_symbols_bulk(
    all_symbols, priority=5.0
)
```

### 2. Settlement-Aware Execution
```python
# Monitors sell order settlement and buying power release
settlement_monitor = SettlementMonitor(alpaca_manager, event_bus)
settlement_result = await settlement_monitor.monitor_sell_orders_settlement(
    sell_order_ids, correlation_id, plan_id
)
```

### 3. Async Execution Pipeline
```python
# Execute rebalance plan with settlement monitoring
executor = Executor(alpaca_manager, enable_smart_execution=True)
result = await executor.execute_rebalance_plan(plan)
```

## Execution Flow

1. **Symbol Extraction**: All symbols extracted upfront from RebalancePlanDTO
2. **Bulk Subscription**: Efficient bulk subscription to all symbols simultaneously
3. **Sell Phase**: Execute all sell orders in parallel
4. **Settlement Monitoring**: Monitor sell order completion and buying power release
5. **Buy Phase**: Execute buy orders only after sufficient buying power is available
6. **Cleanup**: Proper cleanup of pricing subscriptions

## Event-Driven Architecture

### Settlement Events
- `OrderSettlementCompleted`: Individual order settlement
- `BulkSettlementCompleted`: Multi-order settlement with buying power calculation
- `ExecutionPhaseCompleted`: Phase completion events

### Event Correlation
- `correlation_id`: Tracks entire execution workflow
- `causation_id`: Links related events
- `source_module`: Identifies event source

## Usage Examples

### Basic Execution
```python
from the_alchemiser.execution_v2.core import ExecutionManager, ExecutionConfig

# Create execution manager
manager = ExecutionManager.create_with_config(
    api_key="your_key",
    secret_key="your_secret",
    paper=True,
    enable_smart_execution=True
)

# Execute rebalance plan
result = manager.execute_rebalance_plan(rebalance_plan)
```

### Advanced Settlement Monitoring
```python
from the_alchemiser.execution_v2.core import SettlementMonitor

# Create settlement monitor with event bus
monitor = SettlementMonitor(
    alpaca_manager=alpaca_manager,
    event_bus=event_bus,
    polling_interval_seconds=0.5,
    max_wait_seconds=60
)

# Monitor settlement and get buying power release
settlement_event = await monitor.monitor_sell_orders_settlement(
    sell_order_ids=["order1", "order2"],
    correlation_id="execution-123",
    plan_id="plan-456"
)

print(f"Released buying power: ${settlement_event.total_buying_power_released}")
```

### Bulk Pricing Subscription
```python
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

# Create pricing service
pricing_service = RealTimePricingService()

# Bulk subscribe to multiple symbols
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
results = pricing_service.subscribe_symbols_bulk(symbols, priority=5.0)

# Check subscription results
for symbol, success in results.items():
    print(f"{symbol}: {'✅' if success else '❌'}")
```

## Configuration

### Execution Config
```python
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

config = ExecutionConfig(
    market_open_delay_minutes=5,
    max_spread_percent=Decimal("0.50"),
    repeg_threshold_percent=Decimal("0.10"),
    max_repegs_per_order=5
)
```

### Settlement Monitor Config
```python
settlement_monitor = SettlementMonitor(
    alpaca_manager=alpaca_manager,
    polling_interval_seconds=0.5,  # How often to check order status
    max_wait_seconds=60            # Maximum time to wait for settlement
)
```

## Error Handling

The enhanced execution strategy includes robust error handling:

- **Fallback to Market Orders**: If smart execution fails, falls back to standard market orders
- **Graceful Degradation**: If pricing service fails, execution continues without real-time pricing
- **Settlement Timeout**: If settlement monitoring times out, execution can proceed with buy orders
- **Partial Settlement**: Handles cases where only some sell orders settle

## Monitoring and Logging

Comprehensive logging provides visibility into execution flow:

```
🚀 Executing rebalance plan test-plan-789 with 4 items (enhanced settlement-aware)
📋 Extracted 4 unique symbols for execution
📡 Bulk subscribing to 4 symbols with priority 5.0
✅ Bulk subscription complete: 4/4 symbols subscribed
📊 Execution plan: 2 SELLs, 2 BUYs, 0 HOLDs
🔄 Phase 1: Executing SELL orders with settlement monitoring...
✅ SELL AAPL completed successfully (ID: order-1)
✅ SELL MSFT completed successfully (ID: order-2)
🔄 Phase 2: Monitoring settlement and executing BUY orders...
👀 Monitoring settlement of 2 sell orders...
✅ Sell order order-1 settled: $10000.0 buying power released
✅ Sell order order-2 settled: $10000.0 buying power released
🎯 Settlement monitoring complete: 2/2 orders settled, $20000.0 buying power released in 0.0s
💰 Settlement complete: $20000.0 buying power released
✅ BUY GOOGL completed successfully (ID: order-3)
✅ BUY TSLA completed successfully (ID: order-4)
🧹 Cleaning up pricing subscriptions for 4 symbols
✅ Rebalance plan test-plan-789 completed: 4/4 orders succeeded
```

## Performance Characteristics

- **Bulk Subscription**: Up to 30 symbols can be subscribed simultaneously
- **Priority Management**: Higher priority symbols replace lower priority ones when limits are reached
- **Settlement Monitoring**: 0.5-second polling interval with 60-second timeout
- **Async Execution**: Non-blocking execution allows for concurrent order processing
- **Memory Efficiency**: Automatic cleanup of subscriptions and completed monitoring tasks

## Integration Points

### With Portfolio Module
```python
# Portfolio generates rebalance plan
rebalance_plan = portfolio_manager.create_rebalance_plan()

# Execution executes with settlement awareness
result = await executor.execute_rebalance_plan(rebalance_plan)
```

### With Event Bus
```python
# Settlement events are emitted to event bus
event_bus.subscribe(BulkSettlementCompleted, handle_settlement_complete)
event_bus.subscribe(ExecutionPhaseCompleted, handle_phase_complete)
```

### With Orchestration Module
```python
# Orchestrator coordinates multi-module workflows
orchestrator.handle_rebalance_plan(plan)
# -> Triggers enhanced execution with settlement monitoring
# -> Emits events for downstream processing
```

This enhanced execution strategy provides a robust, production-ready foundation for sophisticated trading workflows with proper settlement awareness and multi-symbol coordination.