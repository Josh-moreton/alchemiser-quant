Here’s an exhaustive list of tests you should cover for your trading bot, including market conditions, order placement scenarios, error handling, and edge cases:

---

## 1. **Market Conditions**

- **Market Open:** Orders placed and filled as expected.
- **Market Closed:** Orders are not placed, or handled via ignore_market_hours logic.
- **Pre-market / After-hours:** Attempt orders outside regular hours, verify correct handling.
- **High Volatility:** Large bid/ask spreads, rapid price changes.
- **Low Liquidity:** Thinly traded assets, large spreads, partial fills.

---

## 2. **Order Placement Scenarios**

- **Market Orders:**
  - Buy and sell market orders for all supported symbols.
  - Market order with insufficient buying power (should scale down or fail gracefully).
- **Limit Orders:**
  - Limit order placed and filled.
  - Limit order placed, not filled, then canceled and retried.
  - Limit order with price far from market (should not fill).
  - Limit order with dynamic pegging (test all retry steps).
- **Partial Fills:**
  - Order partially filled, then completed.
  - Order partially filled, then canceled.
- **Failed Orders:**
  - Insufficient buying power (buy and sell).
  - Attempt to sell more than owned (should not short).
  - API/network errors (simulate Alpaca downtime).
  - Symbol not tradable or delisted.
- **Position Liquidation:**
  - Full liquidation using API.
  - Attempt liquidation with zero position.
  - Liquidation with fractional shares.

---

## 3. **Portfolio Rebalancing**

- **Full Rebalance:** Sell all current positions, buy new target portfolio.
- **Partial Rebalance:** Adjust weights, sell/buy only as needed.
- **No Trades Needed:** Portfolio already matches target, no orders placed.
- **Edge Case:** Target allocation sums to <100% or >100% (should warn or correct).

---

## 4. **Cash and Buying Power**

- **Sufficient Cash:** All buys succeed.
- **Insufficient Cash:** Buys scaled down, warning shown.
- **Zero Cash:** No buys possible, handled gracefully.
- **Unexpected Cash Movement:** Cash changes mid-rebalance (simulate external withdrawal).

---

## 5. **Error Handling & Recovery**

- **API Errors:** Handle and log all Alpaca API errors.
- **Network Failures:** Retry logic, fallback to market order.
- **Order Status Polling:** Orders stuck in pending/canceled/rejected.
- **Settlement Waiting:** Sell orders not settled in time, timeout logic.

---

## 6. **Strategy Signal Handling**

- **Conflicting Signals:** Two strategies recommend opposite actions.
- **No Signal:** Strategy returns HOLD or no actionable signal.
- **Multi-Asset Signals:** Portfolio signals with multiple assets and weights.

---

## 7. **Edge Cases & Miscellaneous**

- **Fractional Shares:** Buy/sell fractional quantities.
- **Delisted/Untradable Symbol:** Attempt to trade a symbol that is not available.
- **Duplicate Orders:** Same order placed twice (should not double trade).
- **OrderManager/Adapter Fallbacks:** Adapter delegates all calls correctly.

---

## 8. **Integration & Regression**

- **End-to-End Paper Trade:** Simulate a full trading day with all features.
- **End-to-End Live Trade (if safe):** Run in live mode with small amounts.
- **Backtest Mode:** Run historical data through the bot, verify order logic.

---

## 9. **Reporting & Logging**

- **Order Execution Logging:** All orders logged with status, price, qty.
- **Error Logging:** All errors and warnings logged.
- **Portfolio State Reporting:** Final allocations match expected results.

---

**Tip:**  
Automate as many of these as possible with mocks and fixtures. For market conditions, use Alpaca’s paper trading and time manipulation features. For error scenarios, mock API responses and exceptions.

Let me know if you want example test code for any specific scenario!
