# Dashboard Usage Guide

## Quick Start

```bash
# Run the dashboard
make dashboard

# Or directly with Streamlit
poetry run streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Navigation

Use the sidebar to switch between pages:

- Portfolio Overview
- Forward Projection
- Last Run Analysis
- Trade History
- Strategy Performance
- Execution Quality
- Symbol Analytics
- Options Hedging

## Page Features

### Portfolio Overview

**Purpose**: High-level portfolio health and performance metrics

**Key Sections**:
1. **Key Metrics Bar** - Current equity, total P&L, cumulative returns
2. **Risk Metrics Bar** - Sharpe ratio, max drawdown, volatility, win rate
3. **Current Positions Table** - Real-time positions
4. **Performance Charts** - Equity curve, cumulative P&L, daily P&L
5. **Monthly Summary Table** - Monthly returns breakdown

### Last Run Analysis

**Purpose**: Deep dive into workflow executions

**Key Sections**:
1. **Workflow Selector** - Choose from recent runs
2. **Workflow Summary** - Status, strategy count, timestamps
3. **Aggregated Signal** - Target allocations
4. **Rebalance Plan** - BUY/SELL/HOLD breakdown
5. **Executed Trades** - Complete trade log

### Trade History

**Purpose**: Comprehensive trade analytics with strategy attribution

**Key Sections**:
1. **Filters** - Date range, symbol filter
2. **Summary Metrics** - Trade counts, total value
3. **Per-Strategy Performance** - Strategy trade volume
4. **Per-Symbol Performance** - Symbol trade analytics
5. **Recent Trades Table** - Full trade details

### Strategy Performance

**Purpose**: Per-strategy P&L, risk metrics, lot-level drill-down

**Key Sections**:
1. **Summary Grid** - All strategies at a glance
2. **Data Quality** - Attribution coverage audit
3. **Strategy Detail** - Individual strategy with tabs (P&L, risk, lots, trades)
4. **Strategy Comparison** - Overlay multiple strategies

### Execution Quality (TCA)

**Purpose**: Transaction cost analysis and fill quality monitoring

**Key Sections**:
1. **Slippage Analysis** - Distribution, by symbol, by direction
2. **Spread Analysis** - Bid-ask spread capture
3. **Timing Analysis** - Fill time metrics, walk-the-book steps
4. **Trade Details** - Per-trade TCA data

### Symbol Analytics

**Purpose**: Deep dive into individual symbol performance

**Key Sections**:
1. **Current Position** - Real-time position data
2. **Trading Metrics** - Buy/sell statistics
3. **P&L Analysis** - Realized and unrealized
4. **Strategy Attribution** - Which strategies trade this symbol
5. **Price & Position Charts** - Historical visualization

### Options Hedging

**Purpose**: Hedge position management and budget monitoring

**Key Sections**:
1. **Active Positions** - Current hedges with DTE and roll status
2. **Roll Schedule** - Forecast of upcoming rolls
3. **Premium Spend** - Budget utilization vs 5% NAV cap
4. **Decision History** - Hedge open/roll/close timeline
5. **Position Details** - Expandable contract details

## Data Refresh

- **Portfolio Overview**: 5-minute cache
- **Last Run Analysis**: 1-minute cache
- **Trade History**: 5-minute cache
- **Strategy Performance**: 5-minute cache
- **Execution Quality**: 5-minute cache
- **Symbol Analytics**: 1-minute cache
- **Options Hedging**: 2-minute cache

Manual refresh: Browser refresh or Streamlit rerun button.

## Tips

### Finding Specific Information

- **"Why didn't we buy X?"** - Last Run Analysis -> Check signal allocations
- **"How is strategy Y performing?"** - Strategy Performance -> Select strategy
- **"What's our P&L on AAPL?"** - Symbol Analytics -> Select AAPL
- **"Show me yesterday's trades"** - Trade History -> Set date range

### Performance Tips

- Use date filters to narrow large datasets
- Trade History can be slow with "All Time" on large accounts
- Symbol selector only shows symbols with trade history

## Deployment

### Streamlit Cloud

1. Push to GitHub
2. Connect at https://share.streamlit.io
3. Set main file: `dashboard/app.py`
4. Add secrets (see `dashboard/docs/README.md`)

### Local Network

```bash
# Run on specific port
poetry run streamlit run dashboard/app.py --server.port 8080

# Allow external connections
poetry run streamlit run dashboard/app.py --server.address 0.0.0.0
```

## Support

For issues:
1. Check console logs for error messages
2. Verify environment variables are set correctly
3. See [dashboard/docs/README.md](README.md) for technical details
4. See main [README](../../README.md) for system architecture
