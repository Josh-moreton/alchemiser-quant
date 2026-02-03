# Dashboard Usage Guide

## Quick Start

```bash
# Run the dashboard
make dashboard

# Or directly with Streamlit
poetry run streamlit run scripts/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Navigation

Use the sidebar to switch between pages:

```
📊 Octarine Capital
─────────────────────
Navigation
○ 🏠 Portfolio Overview
○ 🎯 Last Run Analysis
○ 📊 Trade History
○ 📈 Symbol Analytics
─────────────────────
```

## Page Features

### 🏠 Portfolio Overview

**Purpose**: High-level portfolio health and performance metrics

**Key Sections**:
1. **Key Metrics Bar**
   - Current Equity
   - Total P&L (with cumulative return %)
   - Total Deposits
   - Latest Day P&L
   - Trading Days count

2. **Risk Metrics Bar**
   - Sharpe Ratio (risk-adjusted returns)
   - Max Drawdown (largest peak-to-trough decline)
   - Annualized Volatility
   - Win Rate (% of profitable days)
   - Average Win/Loss per day

3. **Current Positions Table**
   - Symbol, Quantity, Entry Price
   - Current Price, Market Value
   - Unrealized P&L ($ and %)
   - Sorted by market value

4. **Performance Charts**
   - Equity Curve: Portfolio value over time
   - Cumulative P&L: Running profit/loss
   - Daily P&L: Bar chart of daily returns

5. **Monthly Summary Table**
   - Monthly P&L, End Equity, Deposits
   - Monthly Return %
   - Historical performance breakdown

**Use Cases**:
- Daily portfolio health check
- Performance monitoring
- Risk assessment
- Position sizing verification

---

### 🎯 Last Run Analysis

**Purpose**: Deep dive into workflow executions to understand trading decisions

**Key Sections**:
1. **Workflow Selector**
   - Dropdown to choose from recent runs
   - Shows correlation ID, status, timestamp

2. **Workflow Summary**
   - Status (COMPLETED/FAILED/etc.)
   - Strategy count (completed/total)
   - Created timestamp
   - Correlation ID for tracing

3. **Aggregated Signal**
   - Total symbols in signal
   - Target allocations (weight %)
   - Warning if over/under-allocated
   - Bar chart of allocation distribution

4. **Rebalance Plan**
   - Portfolio value and cash balance
   - Total trade value
   - BUY orders table (sorted by value)
   - SELL orders table (sorted by value)
   - HOLD positions (expandable)

5. **Executed Trades**
   - Total trades count
   - BUY vs SELL breakdown
   - Total value traded
   - Full trades table with timestamps

**Use Cases**:
- Post-mortem analysis: "Why didn't we buy X?"
- Signal verification: "What did each strategy recommend?"
- Trade reconciliation: "Were all planned trades executed?"
- Debugging workflow issues

**Example Workflow**:
```
1. Select yesterday's run from dropdown
2. Check signal: Did strategies agree on top picks?
3. Review rebalance plan: Were buys/sells appropriate?
4. Verify trades: Did execution match plan?
5. Spot anomalies: Any unexpected behavior?
```

---

### 📊 Trade History

**Purpose**: Comprehensive trade analytics with strategy attribution

**Key Sections**:
1. **Filters**
   - Date Range: Last 7/30/90 days, All Time, Custom
   - Symbol Filter: Search for specific ticker
   - Apply button to refresh data

2. **Summary Metrics**
   - Total trades count
   - BUY vs SELL counts
   - Total value traded
   - Unique symbols count

3. **Per-Strategy Performance**
   - Table: Strategy name, trade count, total value, BUY/SELL counts, symbol count
   - Chart: Bar chart of strategy trade volume

4. **Per-Symbol Performance**
   - Table: Symbol, trade count, net quantity, total value, buy/sell counts, avg prices
   - Chart: Top 10 symbols by trade value

5. **Recent Trades Table**
   - Last 50 trades with full details
   - Symbol, direction, quantity, price, value
   - Timestamp and strategy attribution

6. **Daily Trade Volume Chart**
   - Line chart showing trades per day
   - Identify busy vs quiet periods

**Use Cases**:
- Strategy performance comparison
- Symbol concentration analysis
- Trade frequency patterns
- Historical trade lookup

**Example Queries**:
- "How many times did we trade AAPL last month?"
- "Which strategy generates the most trades?"
- "What's our average buy price for QQQ?"
- "Show all trades from the last week"

---

### 📈 Symbol Analytics

**Purpose**: Deep dive into individual symbol performance

**Key Sections**:
1. **Symbol Selector**
   - Dropdown with all traded symbols
   - Automatically sorted alphabetically

2. **Current Position**
   - Quantity held
   - Market value
   - Average entry price
   - Current price
   - Unrealized P&L ($ and %)

3. **Trading Metrics**
   - Total trades, BUY/SELL counts
   - Net quantity (current holdings)
   - Average buy/sell prices

4. **P&L Analysis**
   - Total buy value (capital deployed)
   - Total sell value (capital returned)
   - Estimated realized P&L

5. **Strategy Attribution**
   - Which strategies traded this symbol
   - Trade count per strategy

6. **Trade History Table**
   - Complete trade log for symbol
   - Date, time, direction, quantity, price
   - Strategy attribution

7. **Price History Chart**
   - Line chart of trade prices over time
   - Separate lines for BUY and SELL

8. **Cumulative Position Chart**
   - Shows position size evolution
   - Visualize build-up and exit

**Use Cases**:
- Single-stock analysis
- Entry/exit price verification
- Position sizing history
- Strategy overlap detection

**Example Analysis**:
```
Select symbol: TQQQ
→ See we've traded it 45 times
→ Current position: 150 shares @ $45.23
→ Nuclear Strategy accounts for 80% of trades
→ Average buy price: $42.10
→ Current price: $47.50
→ Unrealized gain: +12.8%
```

---

## Data Refresh

- **Portfolio Overview**: Refreshes every 5 minutes
- **Last Run Analysis**: Refreshes every 1 minute
- **Trade History**: Refreshes every 5 minutes
- **Symbol Analytics**: Refreshes every 1 minute

Manual refresh: Use browser refresh or Streamlit's rerun button (⟳)

---

## Tips & Tricks

### Finding Specific Information

**"Why didn't we buy X?"**
→ Last Run Analysis → Check signal allocations → Review rebalance plan

**"How is strategy Y performing?"**
→ Trade History → Per-Strategy Performance table

**"What's our P&L on AAPL?"**
→ Symbol Analytics → Select AAPL → Check P&L Analysis

**"Show me yesterday's trades"**
→ Trade History → Date Range: Custom → Set dates

### Understanding Warnings

**"⚠️ Over-allocated" in Last Run**
- Signal weights sum to > 100%
- Usually due to strategy configuration
- Check strategy allocations

**"No current position" in Symbol Analytics**
- Symbol was traded but position closed
- Check trade history to see exit trades

### Performance Tips

- Use date filters to narrow large datasets
- Trade History page can be slow with "All Time" + many trades
- Symbol selector only shows traded symbols (not all available)

---

## Troubleshooting

### Dashboard won't start
```bash
# Check dependencies
poetry install

# Verify environment
poetry run python --version

# Check .env file exists
ls -la .env
```

### "No trading data available"
- Check Alpaca credentials in `.env`
- Verify correct endpoint (live vs paper)
- Ensure account has trading history

### "No recent workflow runs found"
- Check DynamoDB table exists
- Verify AWS credentials
- Confirm orchestrator has run at least once

### Slow performance
- Reduce date range in filters
- Clear Streamlit cache: Settings → Clear cache
- Check network connection to AWS

---

## Deployment

### Streamlit Cloud (Free)

1. **Push to GitHub** (already done)

2. **Connect to Streamlit Cloud**
   - Visit https://share.streamlit.io
   - Sign in with GitHub
   - Deploy `scripts/dashboard.py`

3. **Add Secrets**
   ```toml
   # In Streamlit Cloud settings
   ALPACA_KEY = "your_key"
   ALPACA_SECRET = "your_secret"
   ALPACA_ENDPOINT = "https://api.alpaca.markets"
   AWS_ACCESS_KEY_ID = "your_key"
   AWS_SECRET_ACCESS_KEY = "your_secret"
   AWS_REGION = "us-east-1"
   ```

4. **Share URL**
   - Get public URL from Streamlit Cloud
   - Share with team

### Local Network

```bash
# Run on specific port
poetry run streamlit run scripts/dashboard.py --server.port 8080

# Allow external connections
poetry run streamlit run scripts/dashboard.py --server.address 0.0.0.0
```

---

## Future Enhancements

Ideas for expansion:
- [ ] Real-time WebSocket updates
- [ ] Export data to CSV/Excel
- [ ] Comparative analysis (compare runs side-by-side)
- [ ] Custom alerts and notifications
- [ ] Strategy backtesting integration
- [ ] Mobile-responsive improvements
- [ ] Dark mode support

---

## Support

Issues or questions? Check:
1. [Dashboard README](DASHBOARD_README.md) for technical details
2. Console logs for error messages
3. AWS CloudWatch for backend issues
4. Main [README](../README.md) for system architecture

Happy trading! 📈
