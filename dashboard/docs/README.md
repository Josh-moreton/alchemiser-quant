# Alchemiser Trading Dashboard

Enhanced multi-page Streamlit dashboard for the Alchemiser quantitative trading system.

## Features

### Portfolio Overview
- **Key Metrics**: Current equity, total P&L, cumulative returns
- **Risk Metrics**: Sharpe ratio, max drawdown, volatility, win rate
- **Current Positions**: Real-time position data from Alpaca
- **Performance Charts**: Equity curve, cumulative P&L, daily P&L
- **Monthly Summary**: Monthly returns and deposits breakdown

### Forward Projection
- **Growth Scenarios**: Model future equity growth under different assumptions
- **Drawdown Analysis**: Simulate potential drawdown impact

### Last Run Analysis
- **Workflow Selection**: View any recent workflow execution
- **Strategy Signals**: Aggregated signal with target allocations
- **Rebalance Plan**: Detailed breakdown of BUY/SELL/HOLD orders
- **Executed Trades**: Complete trade history for the run

### Trade History
- **Comprehensive Filters**: Date range, symbol-specific filtering
- **Per-Strategy Performance**: Trade attribution by strategy
- **Per-Symbol Performance**: Trade analytics by symbol
- **Volume Charts**: Daily trade volume visualization

### Strategy Performance
- **Per-Strategy P&L**: Realized P&L, win rate, Sharpe ratio per strategy
- **Lot-Level Detail**: Open and closed lots with cost basis tracking
- **Risk Metrics**: Drawdown, volatility, profit factor per strategy
- **Data Quality**: Attribution coverage audit

### Execution Quality (TCA)
- **Slippage Analysis**: Bid-ask spread capture, slippage in bps
- **Timing Analysis**: Fill time metrics
- **Walk-the-Book**: Step execution analysis

### Symbol Analytics
- **Current Position**: Real-time position data for any symbol
- **Trading Metrics**: Comprehensive buy/sell statistics
- **Strategy Attribution**: Which strategies traded this symbol

### Options Hedging
- **Active Positions**: Current hedge positions with DTE
- **Roll Schedule**: Upcoming roll dates forecast
- **Premium Spend**: Budget utilization vs NAV cap
- **Decision History**: Hedge open/roll/close history

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
   poetry run streamlit run dashboard/app.py
   ```

### Environment Variables

The dashboard requires these environment variables (typically in `.env`):

```bash
# AWS credentials (for DynamoDB access)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Deployment to Streamlit Cloud

The dashboard is designed for **production data only** (not dev). It requires:
- AWS credentials (read-only IAM user - created manually)
- User authentication (bcrypt-hashed passwords)

#### Step 1: Create IAM User

Run the included script or create manually via AWS Console:

```bash
./dashboard/scripts/create_dashboard_iam_user.sh
```

#### Step 2: Generate Password Hash

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password_here', bcrypt.gensalt()).decode())"
```

#### Step 3: Generate Cookie Key

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

#### Step 4: Connect to Streamlit Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select this repository
4. Set main file: `dashboard/app.py`

#### Step 5: Configure Secrets

In Streamlit Cloud -> App Settings -> Secrets, add:

```toml
# AWS credentials (read-only IAM user)
AWS_ACCESS_KEY_ID = "AKIA..."
AWS_SECRET_ACCESS_KEY = "your_secret_key_here"
AWS_REGION = "us-east-1"
STAGE = "prod"

# User authentication credentials
[credentials.usernames.josh]
email = "your@email.com"
name = "Josh Moreton"
password = "$2b$12$..."  # bcrypt hash

# Session cookie configuration
[cookie]
name = "alchemiser_dashboard"
key = "your_random_key"
expiry_days = 30
```

#### Local Development (Skip Auth)

```bash
SKIP_AUTH=true poetry run streamlit run dashboard/app.py
```

Or add `SKIP_AUTH=true` to your `.env` file.

## Architecture

### Data Sources

1. **DynamoDB** (via boto3)
   - Account snapshots, positions, P&L history
   - Strategy signals and workflow state
   - Trade ledger with strategy attribution
   - Strategy performance snapshots
   - Hedge positions and history

### Directory Structure

```
dashboard/
├── app.py                    # Main Streamlit entry point
├── settings.py               # DashboardSettings (Pydantic config)
├── _setup_imports.py          # sys.path setup for shared layer
├── .streamlit/
│   └── config.toml            # Streamlit theme & server config
├── components/
│   ├── __init__.py
│   ├── styles.py              # Theme colors, CSS injection, formatters
│   └── ui.py                  # Reusable UI widgets (metrics, tables)
├── data/
│   ├── __init__.py
│   ├── account.py             # Account/position/PnL data access
│   └── strategy.py            # Strategy performance data access
├── pages/
│   ├── __init__.py
│   ├── portfolio_overview.py  # Portfolio & PnL metrics
│   ├── forward_projection.py  # Growth scenario modelling
│   ├── last_run_analysis.py   # Workflow run analysis
│   ├── trade_history.py       # Trade history & attribution
│   ├── strategy_performance.py# Per-strategy analytics
│   ├── execution_quality.py   # TCA / slippage analysis
│   ├── symbol_analytics.py    # Per-symbol deep dive
│   └── options_hedging.py     # Hedge positions & budget
├── docs/
│   ├── README.md              # This file
│   └── USAGE.md               # Usage guide
├── scripts/
│   └── create_dashboard_iam_user.sh
└── tests/
    └── test_dashboard.py
```

### Caching Strategy

- **5 minute cache** for portfolio metrics and positions
- **1 minute cache** for workflow/run data
- **5 minute cache** for trade history queries
- **2 minute cache** for hedge positions

Uses Streamlit's `@st.cache_data` decorator.

## Troubleshooting

### Dashboard won't start
```bash
poetry install
poetry run python --version
ls -la .env
```

### "No trading data available"
- Check AWS credentials in `.env` or Streamlit secrets
- Verify DynamoDB tables exist for your stage

### Import Errors
- Run `poetry install` to ensure all dependencies are installed
- The dashboard uses `_setup_imports.py` to add `shared_layer/python` to sys.path

## License

Part of The Alchemiser trading system. See main repository for license details.
