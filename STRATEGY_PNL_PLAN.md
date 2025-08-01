# Per-Strategy P&L Tracking Plan

This plan outlines how to track profits and losses (P&L) for each trading strategy individually so that the metrics can be included in summary emails and performance reports.

## 1. ✅ Introduce a `StrategyOrderTracker` - COMPLETED

- ✅ Create a dedicated component responsible for recording every executed order along with the originating strategy.
- ✅ For each order, store the strategy identifier, order ID, symbol, side, quantity, price, and timestamp.
- ✅ Persist these records in a durable store (S3) so that order history survives restarts.
- ✅ Implemented comprehensive P&L calculations (realized, unrealized, total)
- ✅ Added S3 persistence with configurable paths
- ✅ Created email summary integration methods
- ✅ Full test coverage with 7 passing tests

## 2. ✅ Tag Orders With Strategy Information - COMPLETED

- ✅ When the `TradingEngine` executes a rebalance, pass the `StrategyType` to the execution layer.
- ✅ Immediately after each order fills, log it in the `StrategyOrderTracker` with its strategy tag.

### Implementation Completed

1. ✅ **Enhanced Portfolio Data Structure**: Modified `MultiStrategyManager.run_all_strategies()` to return portfolio allocation with strategy attribution
2. ✅ **Strategy-Symbol Mapping**: Created a mapping showing which strategy contributes to each symbol
3. ✅ **Order Tracking Integration**: Strategy information is passed through the execution chain to `StrategyOrderTracker.record_order()`
4. ✅ **Execution Layer Updates**: Modified `PortfolioRebalancer` to accept and forward strategy context

### Files Modified

- ✅ `strategy_manager.py`: Returns strategy attribution data in 3-tuple format
- ✅ `trading_engine.py`: Passes strategy info to rebalancer
- ✅ `portfolio_rebalancer.py`: Integrated order tracking with strategy attribution
- ✅ `backtest_engine.py`: Updated to handle new 3-tuple return signature
- ✅ `test_backtest.py`: Updated to handle new 3-tuple return signature
- ✅ `main.py`: Compatible with new return signature
- `portfolio_rebalancer.py`: Track strategy for each order
- Integration with `StrategyOrderTracker.record_order()`

## 3. ✅ Calculate P&L per Strategy - COMPLETED

- ✅ Use the stored order history to maintain positions and average cost on a per-strategy basis.
- ✅ Compute realized P&L when a position is reduced or closed and unrealized P&L from current market prices.
- ✅ The `StrategyOrderTracker` already implements comprehensive P&L calculations via `get_strategy_pnl()` and `get_all_strategy_pnl()` methods

## 4. ✅ Update the Execution Summary - COMPLETED

- ✅ Extended `_create_execution_summary` to include P&L metrics from the tracker.
- ✅ For every strategy, now reports `realized_pnl`, `unrealized_pnl`, `total_pnl`, `allocation_value`, and `positions` alongside the current allocation and trading signal.
- ✅ Added overall P&L summary with totals across all strategies
- ✅ Enhanced TradingEngine with current price fetching utilities for real-time P&L calculations

### Implementation Details

- ✅ **Enhanced Execution Summary**: Modified `TradingEngine._create_execution_summary()` to include comprehensive P&L data
- ✅ **Real-time P&L**: Added current price fetching for accurate unrealized P&L calculations
- ✅ **Strategy Attribution**: Each strategy now reports detailed P&L alongside signals and allocations
- ✅ **Error Handling**: Robust error handling ensures P&L failures don't break execution summary generation

## 5. Persist Historical Strategy P&L

- At the end of each run, append the cumulative P&L for each strategy to a daily or monthly log.
- This history enables long-term performance tracking and dashboard integration.

## 6. Enhance Email Reports

- Modify `build_multi_strategy_email_html` to display per-strategy P&L in addition to allocations and signals.
- Keep the existing "Recent Closed Positions P&L" section for overall account performance.

## 7. Testing

- Add unit tests confirming that orders are logged with the correct strategy identifiers and that P&L calculations are accurate.
- Update email-related tests to verify the new P&L table renders correctly.
