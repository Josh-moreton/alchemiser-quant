# Nuclear Energy Trading Bot - Comprehensive Backtesting Plan

## Executive Summary

The Nuclear Energy Trading Bot is a sophisticated multi-signal, multi-portfolio strategy that requires a specialized backtesting framework to properly evaluate its performance across different execution timings. This document outlines a step-by-step approach to build a robust backtesting system that accurately replicates the bot's complex decision-making process.

## Strategy Analysis

### Core Strategy Components

1. **Market Regime Detection**
   - SPY RSI(10) levels for overbought/oversold conditions
   - Multiple index monitoring (IOO, TQQQ, VTV, XLF, VOX)
   - Bull/Bear market determination via SPY vs 200-day MA

2. **Signal Types & Portfolio Allocations**
   - `NUCLEAR_PORTFOLIO`: Dynamic 3-stock nuclear portfolio with inverse volatility weighting
   - `UVXY_BTAL_PORTFOLIO`: 75% UVXY + 25% BTAL volatility hedge
   - `BEAR_PORTFOLIO`: Dual bear sub-strategies with inverse volatility weighting
   - Single stock signals: TQQQ, UPRO, SQQQ, etc.

3. **Complex Decision Tree**
   - Primary: SPY RSI > 79 → Volatility protection
   - Secondary: Individual index overbought conditions
   - Tertiary: Bull market → Nuclear portfolio
   - Quaternary: Bear market → Dual bear strategies

4. **Technical Indicators Required**
   - RSI (10-day, 20-day windows)
   - Moving Averages (20-day, 200-day)
   - 90-day moving average returns
   - 60-day cumulative returns
   - 90-day volatility for portfolio weighting

## Backtesting Challenges

### Current Issues with Existing Backtest

1. **Incomplete Strategy Replication**: Not using actual bot logic
2. **Missing Portfolio Dynamics**: Not handling complex portfolio signals
3. **Simplified Data Flow**: Not replicating real-time decision making
4. **Timing Assumptions**: Not testing optimal execution windows

### Technical Challenges

1. **Multi-timeframe Data Management**: Daily strategy, hourly execution
2. **Look-ahead Bias Prevention**: Ensuring indicators use only historical data
3. **Portfolio Rebalancing Logic**: Handling partial vs full rebalancing
4. **Signal Change Detection**: Identifying when strategy switches

## Proposed Solution Architecture

### Phase 1: Strategy Integration Framework

#### 1.1 Create Backtesting Data Provider

```python
class BacktestDataProvider:
    """Replaces live DataProvider for historical backtesting"""
    - Historical data management with point-in-time access
    - Multi-timeframe data alignment
    - Timezone handling and trading calendar integration
```

#### 1.2 Strategy Engine Wrapper

```python
class BacktestStrategyEngine:
    """Wraps NuclearStrategyEngine for backtesting"""
    - Point-in-time indicator calculation
    - Historical market data simulation
    - Signal change detection and logging
```

### Phase 2: Multi-Timeframe Execution Engine

#### 2.1 Execution Strategies

1. **Open Execution**: Trade at market open using previous day's signal
2. **Close Execution**: Trade at market close using same day's signal
3. **Hourly Execution**: Trade at specific hour using morning signal
4. **Signal-Change Execution**: Trade immediately when signal changes

#### 2.2 Signal Generation Timeline

```
Daily Timeline:
09:30 - Market Open
10:00 - Generate morning signal
11:00 - Check for signal changes
...
16:00 - Market Close, generate EOD signal
```

### Phase 3: Portfolio Management System

#### 3.1 Position Tracking

```python
class PortfolioManager:
    - Current positions and cash
    - Target portfolio calculation
    - Rebalancing execution with transaction costs
    - Performance tracking
```

#### 3.2 Rebalancing Logic

- **Full Rebalancing**: Complete portfolio restructure on signal change
- **Partial Rebalancing**: Gradual adjustment over multiple days
- **Threshold-Based**: Only rebalance if allocation drift > threshold

## Implementation Plan

### Step 1: Data Infrastructure Setup (Week 1)

#### 1.1 Enhanced Data Provider

- [ ] Create `BacktestDataProvider` class
- [ ] Implement point-in-time data access
- [ ] Add multi-timeframe data alignment
- [ ] Handle timezone and trading calendar issues

#### 1.2 Data Validation

- [ ] Verify data completeness for all symbols
- [ ] Check for corporate actions and splits
- [ ] Validate price consistency across timeframes

### Step 2: Strategy Engine Integration (Week 1-2)

#### 2.1 Strategy Wrapper Development

```python
# Key components to implement
class BacktestNuclearStrategy:
    def __init__(self, original_strategy):
        self.strategy = original_strategy
        self.data_provider = BacktestDataProvider()
    
    def evaluate_at_time(self, timestamp, market_data):
        """Evaluate strategy at specific point in time"""
        # Calculate indicators using only historical data
        # Run original strategy logic
        # Return signal and portfolio allocation
```

#### 2.2 Signal Detection System

- [ ] Implement signal change detection
- [ ] Log all signal transitions with timestamps
- [ ] Track portfolio allocation changes

### Step 3: Execution Engine Development (Week 2)

#### 3.1 Multi-Timeframe Execution

```python
class ExecutionEngine:
    def execute_open_strategy(self):
        """Trade at market open using previous day signal"""
    
    def execute_close_strategy(self):
        """Trade at market close using same day signal"""
    
    def execute_hourly_strategy(self, hour):
        """Trade at specific hour using morning signal"""
    
    def execute_signal_change_strategy(self):
        """Trade immediately when signal changes"""
```

#### 3.2 Portfolio Rebalancing

- [ ] Implement position sizing logic
- [ ] Add transaction cost modeling
- [ ] Handle partial fills and liquidity constraints

### Step 4: Performance Analytics (Week 3)

#### 4.1 Metrics Calculation

- [ ] Returns (total, annual, risk-adjusted)
- [ ] Risk metrics (Sharpe, Sortino, max drawdown)
- [ ] Trading metrics (frequency, win rate, turnover)
- [ ] Timing analysis (signal vs execution performance)

#### 4.2 Comparative Analysis

- [ ] Strategy vs benchmark comparison
- [ ] Execution timing impact analysis
- [ ] Portfolio allocation efficiency analysis

### Step 5: Validation and Testing (Week 3-4)

#### 5.1 Strategy Validation

- [ ] Compare backtest signals to live bot signals
- [ ] Verify indicator calculations match exactly
- [ ] Validate portfolio allocation logic

#### 5.2 Execution Testing

- [ ] Test all execution strategies
- [ ] Verify signal timing accuracy
- [ ] Check portfolio rebalancing logic

## Technical Implementation Details

### Data Requirements

#### Daily Data (All Symbols)

```python
symbols = [
    # Market indices
    'SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX',
    # Volatility
    'UVXY', 'BTAL',
    # Tech
    'QQQ', 'SQQQ', 'PSQ', 'UPRO',
    # Bonds
    'TLT', 'IEF',
    # Nuclear
    'SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO'
]

timeframes = ['1d', '1h']  # Daily for strategy, hourly for execution
```

#### Indicator Calculations

```python
required_indicators = {
    'rsi_10': 'RSI with 10-day window',
    'rsi_20': 'RSI with 20-day window', 
    'ma_200': '200-day moving average',
    'ma_20': '20-day moving average',
    'ma_return_90': '90-day moving average return',
    'cum_return_60': '60-day cumulative return',
    'volatility_90': '90-day volatility for portfolio weighting'
}
```

### Signal Processing Pipeline

#### 1. Data Preparation

```python
def prepare_market_data(date, symbols, data_provider):
    """Prepare market data as of specific date"""
    market_data = {}
    for symbol in symbols:
        # Get historical data up to (but not including) future dates
        hist_data = data_provider.get_data_up_to_date(symbol, date)
        market_data[symbol] = hist_data
    return market_data
```

#### 2. Strategy Evaluation

```python
def evaluate_strategy_at_time(timestamp, strategy_engine, market_data):
    """Run strategy evaluation at specific timestamp"""
    indicators = strategy_engine.calculate_indicators(market_data)
    signal, action, reason = strategy_engine.evaluate_nuclear_strategy(indicators, market_data)
    return signal, action, reason, indicators
```

#### 3. Portfolio Construction

```python
def build_target_portfolio(signal, action, reason, indicators, portfolio_value):
    """Convert strategy signal to target portfolio allocation"""
    if signal == 'NUCLEAR_PORTFOLIO':
        return build_nuclear_portfolio(indicators, portfolio_value)
    elif signal == 'UVXY_BTAL_PORTFOLIO':
        return build_volatility_portfolio(portfolio_value)
    elif signal == 'BEAR_PORTFOLIO':
        return build_bear_portfolio(reason, indicators, portfolio_value)
    else:
        return build_single_asset_portfolio(signal, action, portfolio_value)
```

### Execution Strategies Comparison

#### Strategy 1: Previous Day Close Signal → Open Execution

```
Day N-1: 16:00 - Generate signal using Day N-1 data
Day N:   09:30 - Execute trades at market open
```

#### Strategy 2: Same Day Signal → Close Execution  

```
Day N: 09:30-15:30 - Generate signal using Day N data
Day N: 16:00       - Execute trades at market close
```

#### Strategy 3: Morning Signal → Hourly Execution

```
Day N: 10:00 - Generate signal using available Day N data
Day N: HH:00 - Execute trades at specified hour
```

#### Strategy 4: Real-time Signal Change → Immediate Execution

```
Continuous: Monitor for signal changes
On Change:  Execute trades immediately at current prices
```

## Expected Outcomes

### Performance Insights

1. **Timing Impact**: Quantify how execution timing affects returns
2. **Signal Persistence**: Understand how long signals remain valid
3. **Portfolio Efficiency**: Measure allocation effectiveness
4. **Risk Management**: Evaluate volatility protection strategies

### Optimization Opportunities

1. **Optimal Execution Hour**: Find best intraday timing
2. **Rebalancing Frequency**: Daily vs signal-change based
3. **Portfolio Allocation**: Fine-tune weightings
4. **Signal Thresholds**: Optimize RSI and MA parameters

## Risk Considerations

### Backtesting Risks

1. **Look-ahead Bias**: Using future data in historical decisions
2. **Survivorship Bias**: Only testing currently available symbols
3. **Liquidity Assumptions**: Assuming perfect execution at quoted prices
4. **Transaction Cost Impact**: Underestimating trading costs

### Mitigation Strategies

1. **Strict Point-in-Time Data**: Only use data available at decision time
2. **Conservative Execution**: Add slippage and transaction cost models
3. **Validation Framework**: Compare backtest to live trading results
4. **Sensitivity Analysis**: Test across different market conditions

## Success Metrics

### Primary Objectives

- [ ] Accurate replication of live bot strategy logic
- [ ] Comprehensive execution timing analysis
- [ ] Robust performance measurement framework
- [ ] Clear optimization recommendations

### Deliverables

1. **Backtesting Framework**: Complete, reusable system
2. **Performance Report**: Detailed analysis across execution strategies
3. **Optimization Guide**: Recommendations for strategy improvements
4. **Documentation**: Full implementation and usage guide

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 | Week 1 | Data infrastructure, Strategy integration |
| 2 | Week 1-2 | Execution engine, Signal detection |
| 3 | Week 2-3 | Performance analytics, Portfolio management |
| 4 | Week 3-4 | Testing, Validation, Documentation |

## Next Steps

1. **Immediate**: Review and approve this plan
2. **Week 1**: Begin data infrastructure development
3. **Week 2**: Implement strategy integration layer
4. **Week 3**: Build execution and analytics engines
5. **Week 4**: Complete testing and generate final report

---

*This plan provides a comprehensive roadmap for building a professional-grade backtesting system that will accurately evaluate your Nuclear Energy Trading Bot's performance across multiple execution strategies and timeframes.*
