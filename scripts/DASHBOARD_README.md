# Alchemiser Trading Dashboard

Enhanced multi-page Streamlit dashboard for the Alchemiser quantitative trading system.

## Features

### 🏠 Portfolio Overview
- **Key Metrics**: Current equity, total P&L, cumulative returns
- **Risk Metrics**: Sharpe ratio, max drawdown, volatility, win rate
- **Current Positions**: Real-time position data from Alpaca
- **Performance Charts**: Equity curve, cumulative P&L, daily P&L
- **Monthly Summary**: Monthly returns and deposits breakdown

### 🎯 Last Run Analysis
- **Workflow Selection**: View any recent workflow execution
- **Strategy Signals**: Aggregated signal with target allocations
- **Rebalance Plan**: Detailed breakdown of BUY/SELL/HOLD orders
- **Executed Trades**: Complete trade history for the run
- **Raw Data**: Access to underlying JSON data for debugging

### 📊 Trade History
- **Comprehensive Filters**: Date range, symbol-specific filtering
- **Per-Strategy Performance**: Trade attribution by strategy
- **Per-Symbol Performance**: Trade analytics by symbol
- **Volume Charts**: Daily trade volume visualization
- **Recent Trades**: Last 50 trades with full details

### 📈 Symbol Analytics
- **Current Position**: Real-time position data for any symbol
- **Trading Metrics**: Comprehensive buy/sell statistics
- **P&L Analysis**: Realized and unrealized P&L estimation
- **Strategy Attribution**: Which strategies traded this symbol
- **Trade History**: Complete trade history with price chart
- **Cumulative Position**: Position size over time

## Usage

### Local Development

1. **Install dependencies** (if not already done):
   ```bash
   poetry install
   ```

2. **Run the dashboard**:
   ```bash
   make dashboard
   # or
   poetry run streamlit run scripts/dashboard.py
   ```

3. **Legacy single-page dashboard** (still available):
   ```bash
   make pnl-dashboard
   # or
   poetry run streamlit run scripts/pnl_dashboard.py
   ```

### Environment Variables

The dashboard requires these environment variables (typically in `.env`):

```bash
# Alpaca API credentials
ALPACA_KEY=your_api_key
ALPACA_SECRET=your_secret_key
ALPACA_ENDPOINT=https://api.alpaca.markets  # or paper trading endpoint

# AWS credentials (for DynamoDB access)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Deployment to Streamlit Cloud

1. **Push to GitHub**: The dashboard code is already in the repository

2. **Connect to Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select this repository
   - Set main file: `scripts/dashboard.py`

3. **Configure Secrets**:
   In Streamlit Cloud's app settings, add your secrets:
   ```toml
   [default]
   ALPACA_KEY = "your_api_key"
   ALPACA_SECRET = "your_secret_key"
   ALPACA_ENDPOINT = "https://api.alpaca.markets"
   AWS_ACCESS_KEY_ID = "your_access_key"
   AWS_SECRET_ACCESS_KEY = "your_secret_key"
   AWS_REGION = "us-east-1"
   ```

## Architecture

### Data Sources

1. **Alpaca API** (via `PnLService` and `AlpacaAccountService`)
   - Portfolio equity and P&L history
   - Current positions
   - Account information

2. **DynamoDB** (via boto3)
   - `alchemiser-dev-aggregation-sessions`: Strategy signals and workflow state
   - `alchemiser-dev-rebalance-plans`: Rebalance plan details
   - `alchemiser-dev-trade-ledger`: Trade history with strategy attribution

### Caching Strategy

- **5 minute cache** for portfolio metrics and positions (hot path)
- **1 minute cache** for workflow/run data (semi-hot)
- **5 minute cache** for trade history queries
- Uses Streamlit's `@st.cache_data` decorator

### Page Structure

```
scripts/
├── dashboard.py                          # Main entry point
├── dashboard_pages/
│   ├── __init__.py
│   ├── portfolio_overview.py            # Portfolio & PnL metrics
│   ├── last_run_analysis.py             # Workflow run analysis
│   ├── trade_history.py                 # Trade history & attribution
│   └── symbol_analytics.py              # Per-symbol deep dive
└── pnl_dashboard.py                     # Legacy single-page dashboard
```

## Development

### Adding New Pages

1. Create a new module in `scripts/dashboard_pages/`:
   ```python
   def show() -> None:
       """Display your page content."""
       st.title("My New Page")
       # Your page logic here
   ```

2. Add the page to `scripts/dashboard.py`:
   ```python
   page = st.sidebar.radio(
       "Navigation",
       ["🏠 Portfolio Overview", ..., "🆕 My New Page"],
   )
   
   # In the routing section:
   elif page == "🆕 My New Page":
       from dashboard_pages import my_new_page
       my_new_page.show()
   ```

### Testing Changes

Run the dashboard locally and verify:
- All pages load without errors
- Data displays correctly
- Filters work as expected
- Charts render properly
- No console errors

### Code Style

Follow the project's coding standards:
- Business unit header: `"""Business Unit: scripts | Status: current."""`
- Type hints on all functions
- Docstrings on public functions
- Use `@st.cache_data` for expensive operations
- Handle errors gracefully with `try/except` and user-friendly messages

## Troubleshooting

### "No trading data available"
- Check that Alpaca credentials are correct
- Verify you're using the correct endpoint (live vs paper)
- Ensure the account has trading history

### "No recent workflow runs found"
- Verify DynamoDB table exists and has data
- Check AWS credentials and region
- Ensure the workflow has been executed at least once

### "Error loading trades"
- Check DynamoDB permissions
- Verify table names match your environment (dev/prod)
- Look for boto3 errors in console

### Import Errors
- Run `poetry install` to ensure all dependencies are installed
- Check that `_setup_imports.py` is in the scripts directory
- Verify PYTHONPATH includes `layers/shared`

## Performance Considerations

- **Large trade histories**: Use date filters to limit results
- **Many symbols**: Symbol analytics loads all trades per symbol
- **Frequent refreshes**: Dashboard auto-refreshes based on cache TTL
- **DynamoDB scans**: Trade history uses scans which can be slow for large datasets

## Future Enhancements

Potential improvements:
- [ ] Real-time streaming updates via WebSocket
- [ ] Advanced filtering (multiple symbols, strategy combinations)
- [ ] Export functionality (CSV, Excel)
- [ ] Comparative analysis (compare runs, strategies, time periods)
- [ ] Custom date ranges for all pages
- [ ] Performance attribution analytics
- [ ] Risk monitoring alerts
- [ ] Strategy backtesting integration
- [ ] Mobile-responsive layout improvements

## Support

For issues or questions:
1. Check the logs in Streamlit console
2. Verify environment variables are set correctly
3. Review the error messages for specific issues
4. Consult the main project README for general setup

## License

Part of The Alchemiser trading system. See main repository for license details.
