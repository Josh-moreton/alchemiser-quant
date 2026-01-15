# Order Handling Guide

**Business Unit: execution | Status: current**

This guide describes how the unified order placement system handles each type of order situation.

## Table of Contents

1. [Order Types Overview](#order-types-overview)
2. [Buy Orders](#buy-orders)
3. [Sell Orders (Partial)](#sell-orders-partial)
4. [Sell Orders (Full Close)](#sell-orders-full-close)
5. [Quote Handling](#quote-handling)
6. [Walk-the-Book Execution](#walk-the-book-execution)
7. [Error Scenarios](#error-scenarios)
8. [Special Cases](#special-cases)

---

## Order Types Overview

### Order Intent Structure

Every order is expressed as an `OrderIntent` with these components:

```python
OrderIntent(
    side: OrderSide,        # BUY or SELL
    close_type: CloseType,  # NONE, PARTIAL, or FULL
    symbol: str,            # Stock symbol (e.g., "AAPL")
    quantity: Decimal,      # Number of shares
    urgency: Urgency,       # HIGH, MEDIUM, or LOW
    correlation_id: str,    # Tracking ID (optional)
)
```

### Valid Combinations

| Side | CloseType | Use Case |
|------|-----------|----------|
| `BUY` | `NONE` | Open new position or add to existing |
| `SELL` | `NONE` | Reduce position (same as PARTIAL) |
| `SELL` | `PARTIAL` | Explicitly reduce position |
| `SELL` | `FULL` | Close entire position |

**Invalid**: `BUY` + `PARTIAL` or `BUY` + `FULL` (raises `ValueError`)

### Urgency Routing

| Urgency | Execution Strategy |
|---------|-------------------|
| `HIGH` | Market order immediately (fastest, worst price) |
| `MEDIUM` | Walk-the-book with standard waits (balanced) |
| `LOW` | Walk-the-book with extended waits (best price, slowest) |

---

## Buy Orders

### Scenario: Open New Position

```python
intent = OrderIntent(
    side=OrderSide.BUY,
    close_type=CloseType.NONE,
    symbol="AAPL",
    quantity=Decimal("100"),
    urgency=Urgency.MEDIUM,
)

result = await service.place_order(intent)
```

**Execution Flow:**

1. **Preflight validation**: Check quantity > 0, symbol is tradable
2. **Get current position**: Record starting position (may be 0)
3. **Get quote**: Streaming first, REST fallback
4. **Walk-the-book** (MEDIUM urgency):
   - Step 1: Limit order at `bid + 0.75 * (ask - bid)` = 75% toward ask
   - Wait 30 seconds for fill
   - Step 2: Replace at 85% toward ask (if not filled)
   - Wait 30 seconds
   - Step 3: Replace at 95% toward ask (if not filled)
   - Wait 30 seconds
   - Step 4: Market order (if still not filled)
5. **Validate**: Confirm position increased by filled quantity

**Example with prices:**
- Bid: $149.50, Ask: $150.50 (spread = $1.00)
- Step 1 limit price: $149.50 + 0.75 * $1.00 = **$150.25**
- Step 2 limit price: $149.50 + 0.85 * $1.00 = **$150.35**
- Step 3 limit price: $149.50 + 0.95 * $1.00 = **$150.45**

### Scenario: Add to Existing Position

Same as opening - the system doesn't differentiate. Validation confirms:
- Before: 50 shares
- Order: BUY 100 shares
- Expected after: 150 shares

---

## Sell Orders (Partial)

### Scenario: Reduce Position Size

```python
intent = OrderIntent(
    side=OrderSide.SELL,
    close_type=CloseType.PARTIAL,  # or CloseType.NONE
    symbol="AAPL",
    quantity=Decimal("50"),  # Sell 50 out of 150 shares
    urgency=Urgency.MEDIUM,
)

result = await service.place_order(intent)
```

**Execution Flow:**

1. **Preflight validation**: Check quantity > 0, symbol is tradable
2. **Get current position**: Must have at least `quantity` shares
3. **Get quote**: Streaming first, REST fallback
4. **Walk-the-book** (MEDIUM urgency):
   - Step 1: Limit order at `ask - 0.75 * (ask - bid)` = 75% toward bid
   - Wait 30 seconds for fill
   - Step 2: Replace at 85% toward bid
   - Step 3: Replace at 95% toward bid
   - Step 4: Market order
5. **Validate**: Confirm position decreased by filled quantity

**Example with prices:**
- Bid: $149.50, Ask: $150.50 (spread = $1.00)
- Step 1 limit price: $150.50 - 0.75 * $1.00 = **$149.75**
- Step 2 limit price: $150.50 - 0.85 * $1.00 = **$149.65**
- Step 3 limit price: $150.50 - 0.95 * $1.00 = **$149.55**

---

## Sell Orders (Full Close)

### Scenario: Close Entire Position

```python
intent = OrderIntent(
    side=OrderSide.SELL,
    close_type=CloseType.FULL,
    symbol="AAPL",
    quantity=Decimal("150"),  # Close all 150 shares
    urgency=Urgency.HIGH,     # Often HIGH for exits
)

result = await service.place_order(intent)
```

**Execution Flow:**

1. **Preflight validation**: Check quantity > 0
2. **Get current position**: Record exact position (may differ from `quantity`)
3. **Get quote**: Streaming first, REST fallback
4. **Execute** (HIGH urgency = market order):
   - Place market order immediately
   - Use Alpaca's "close position" semantics for exact quantity
5. **Validate**: Confirm position is now **exactly 0**
   - Full close validation is stricter
   - Logs warning if any shares remain

**Special Handling for Full Close:**
- Uses Alpaca's `close_position` endpoint when available
- Handles fractional shares automatically
- Ensures no dust positions remain

### Why HIGH Urgency for Exits?

Full closes often happen when:
- Strategy signals exit urgently
- Risk management triggers stop-loss
- End-of-day position flattening

Market orders guarantee execution, accepting worse price for certainty.

---

## Quote Handling

### Quote Acquisition Priority

```
1. Streaming (WebSocket) → Lowest latency, real-time
2. REST API → Reliable fallback
3. Unusable → Error or market order
```

### Handling 0 Bid/Ask (Common Alpaca Issue)

Alpaca sometimes returns 0 for bid or ask prices. The system handles this explicitly:

| Condition | Handling | Example |
|-----------|----------|---------|
| `bid=0, ask=$150.50` | Use ask for both | bid=$150.50, ask=$150.50 |
| `bid=$149.50, ask=0` | Use bid for both | bid=$149.50, ask=$149.50 |
| `bid=0, ask=0` | Quote unusable | Try REST fallback |

**Code:**
```python
quote = await quote_service.get_best_quote("AAPL")

if quote.zero_bid_substituted:
    logger.warning(f"Bid was 0, using ask: {quote.bid}")
if quote.zero_ask_substituted:
    logger.warning(f"Ask was 0, using bid: {quote.ask}")
if not quote.success:
    logger.error("No usable quote available")
```

### Quote Freshness

Quotes older than 10 seconds are considered stale:
- Streaming quotes: Usually < 100ms old
- REST quotes: May be 1-5 seconds old
- If quote is stale, system refreshes before order

---

## Walk-the-Book Execution

### Price Progression

The walk-the-book strategy uses progressive price improvement:

```
BUY ORDER:
  Start: Midpoint (50% of spread)
  Progress: Toward ask (more aggressive)

  50% → 75% → 95% → 100% (market)

SELL ORDER:
  Start: Midpoint (50% of spread)
  Progress: Toward bid (more aggressive)

  50% → 75% → 95% → 100% (market)
```

### Step Timing

| Step | Price Level | Wait Time | Cumulative |
|------|-------------|-----------|------------|
| 1 | 50% midpoint | 10s | 10s |
| 2 | 75% toward aggressive | 10s | 20s |
| 3 | 95% toward aggressive | 10s | 30s |
| 4 | Market order | Immediate | ~30s total |

### Why This Strategy?

1. **Better fills**: Most orders fill at steps 1-2, getting better prices
2. **Guaranteed execution**: Market order at step 4 ensures completion
3. **Predictable timing**: ~90 seconds max for any order
4. **Audit trail**: Every step recorded in `WalkResult`

### Customizing Steps

```python
from the_alchemiser.execution_v2.unified import WalkTheBookStrategy

# More aggressive progression
strategy = WalkTheBookStrategy(
    alpaca_manager=alpaca_manager,
    price_steps=[0.80, 0.90, 0.95],  # Start closer to market
    step_wait_seconds=20,             # Shorter waits
)

# More conservative progression
strategy = WalkTheBookStrategy(
    alpaca_manager=alpaca_manager,
    price_steps=[0.60, 0.70, 0.80, 0.90, 0.95],  # More steps
    step_wait_seconds=45,                          # Longer waits
)
```

---

## Error Scenarios

### Insufficient Quantity

```python
# Trying to sell more than owned
intent = OrderIntent(
    side=OrderSide.SELL,
    close_type=CloseType.PARTIAL,
    symbol="AAPL",
    quantity=Decimal("200"),  # Only own 150
    urgency=Urgency.MEDIUM,
)

result = await service.place_order(intent)
# result.success = False
# result.error_message = "Insufficient shares: have 150, need 200"
```

### Market Closed

```python
# Order placed outside market hours
result = await service.place_order(intent)
# result.success = False
# result.error_message = "Market is closed"
```

### No Usable Quote

```python
# Both streaming and REST return unusable quotes
result = await service.place_order(intent)

if intent.urgency == Urgency.HIGH:
    # Proceeds with market order anyway
    # result.success depends on market order
else:
    # Fails with no quote
    # result.success = False
    # result.error_message = "No usable quote available"
```

### Broker Rejection

```python
# Alpaca rejects order (insufficient funds, restricted symbol, etc.)
result = await service.place_order(intent)
# result.success = False
# result.error_message = "Order rejected: insufficient buying power"
```

### Partial Fill Timeout

```python
# Order partially filled after all steps
result = await service.place_order(intent)
# result.success = True (partial is still success)
# result.total_filled = Decimal("75")  # Only 75 of 100 filled
# result.walk_result.partial_fill = True
```

---

## Special Cases

### Fractional Shares

Alpaca supports fractional trading. The system handles this automatically:

```python
intent = OrderIntent(
    side=OrderSide.BUY,
    symbol="AAPL",
    quantity=Decimal("10.5"),  # Fractional quantity
    ...
)
```

- Limit orders: Rounded to 2 decimal places
- Full closes: Exact fractional quantity from position

### Minimum Trade Threshold

Orders below minimum notional value ($1 for Alpaca) are rejected:

```python
# If AAPL is $150, minimum quantity is ~0.007 shares
intent = OrderIntent(
    side=OrderSide.BUY,
    symbol="AAPL",
    quantity=Decimal("0.001"),  # $0.15 notional
    ...
)
# Rejected: below minimum notional
```

### Volatile Markets

During high volatility, quotes may change rapidly:

1. **Wide spreads**: Walk-the-book helps by starting conservative
2. **Fast price movement**: System refreshes quotes between steps
3. **Partial fills**: Common during volatility; system handles gracefully

### Pre-Market / After-Hours

Currently, the system only supports regular market hours (9:30 AM - 4:00 PM ET):

- Orders placed outside hours will fail
- Future enhancement: extended hours trading support

### Corporate Actions

If a stock undergoes a split or other corporate action:

1. Position quantities may change unexpectedly
2. Validation may show discrepancy
3. System logs warning but doesn't fail
4. Manual verification recommended

---

## Quick Reference

### Order Decision Tree

```
What type of order?
│
├─ BUY shares
│   └─ Create: OrderIntent(side=BUY, close_type=NONE, ...)
│
└─ SELL shares
    │
    ├─ Reduce position (keep some)
    │   └─ Create: OrderIntent(side=SELL, close_type=PARTIAL, ...)
    │
    └─ Close entire position
        └─ Create: OrderIntent(side=SELL, close_type=FULL, ...)

How urgent?
│
├─ Must execute NOW (risk management, EOD)
│   └─ urgency=Urgency.HIGH → Market order
│
├─ Want good price, ~90s acceptable
│   └─ urgency=Urgency.MEDIUM → Walk-the-book (default)
│
└─ Price sensitive, time flexible
    └─ urgency=Urgency.LOW → Walk-the-book (extended)
```

### Result Interpretation

```python
result = await service.place_order(intent)

# Success check
if result.success:
    print(f"Filled {result.total_filled} shares @ ${result.avg_fill_price}")
    print(f"Strategy: {result.execution_strategy}")
    print(f"Steps used: {len(result.walk_result.order_attempts)}")

    # Validation check
    if result.validation_result.success:
        print("Position validated correctly")
    else:
        print(f"Warning: {result.validation_result.discrepancy}")
else:
    print(f"Failed: {result.error_message}")
```

### Common Patterns

```python
# Pattern 1: Buy with default settings
result = await service.place_order(
    OrderIntent(side=OrderSide.BUY, close_type=CloseType.NONE,
                symbol="AAPL", quantity=Decimal("10"), urgency=Urgency.MEDIUM)
)

# Pattern 2: Urgent full close
result = await service.place_order(
    OrderIntent(side=OrderSide.SELL, close_type=CloseType.FULL,
                symbol="AAPL", quantity=current_position, urgency=Urgency.HIGH)
)

# Pattern 3: Partial sell for rebalancing
result = await service.place_order(
    OrderIntent(side=OrderSide.SELL, close_type=CloseType.PARTIAL,
                symbol="AAPL", quantity=Decimal("25"), urgency=Urgency.MEDIUM)
)
```

---

## See Also

- [Unified Order Placement Service](./README.md) - Architecture and configuration
- [Execution_v2 Module](../README.md) - Module overview
