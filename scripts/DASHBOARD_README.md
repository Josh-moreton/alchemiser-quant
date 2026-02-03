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

The dashboard is designed for **production data only** (not dev). It requires:
- AWS credentials (read-only IAM user - created manually)
- Alpaca API credentials (production account)
- User authentication (bcrypt-hashed passwords)

#### Step 1: Create IAM User (Manual - One Time Setup)

The IAM user must be created manually via AWS Console (not CloudFormation) because CI/CD roles lack IAM user management permissions.

1. Go to **AWS IAM Console** → **Users** → **Create user**
2. User name: `alchemiser-dashboard-readonly`
3. Do NOT provide console access (API only)
4. Click **Next** → **Attach policies directly**
5. Click **Create policy** and use this JSON:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBReadProd",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:*:table/alchemiser-prod-*",
                "arn:aws:dynamodb:us-east-1:*:table/alchemiser-prod-*/index/*"
            ]
        },
        {
            "Sid": "CloudWatchLogsReadProd",
            "Effect": "Allow",
            "Action": [
                "logs:FilterLogEvents",
                "logs:GetLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups"
            ],
            "Resource": [
                "arn:aws:logs:us-east-1:*:log-group:/aws/lambda/alchemiser-prod-*:*"
            ]
        }
    ]
}
```

6. Name the policy `AlchemiserDashboardReadOnly`
7. Attach this policy to the user and complete user creation

#### Step 2: Create IAM Access Keys

1. Go to AWS IAM Console → Users → `alchemiser-dashboard-readonly`
2. Click "Security credentials" tab
3. Click "Create access key" → "Application running outside AWS"
4. Copy the Access Key ID and Secret Access Key (you won't see the secret again!)

#### Step 3: Generate Password Hash

Generate a bcrypt hash for your login password:

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password_here', bcrypt.gensalt()).decode())"
```

#### Step 4: Generate Cookie Key

Generate a random key for session cookies:

```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

#### Step 5: Connect to Streamlit Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select this repository
4. Set main file: `scripts/dashboard.py`

#### Step 6: Configure Secrets

In Streamlit Cloud → App Settings → Secrets, add:

```toml
# AWS credentials (from Step 2 - read-only IAM user)
AWS_ACCESS_KEY_ID = "AKIA..."
AWS_SECRET_ACCESS_KEY = "your_secret_key_here"
AWS_REGION = "us-east-1"
STAGE = "prod"

# Alpaca API (production account)
ALPACA_KEY = "your_alpaca_key"
ALPACA_SECRET = "your_alpaca_secret"
ALPACA_ENDPOINT = "https://api.alpaca.markets"

# User authentication credentials
[credentials.usernames.josh]
email = "your@email.com"
name = "Josh Moreton"
password = "$2b$12$..."  # bcrypt hash from Step 3

# Add more users as needed:
# [credentials.usernames.another_user]
# email = "another@email.com"
# name = "Another User"
# password = "$2b$12$..."

# Session cookie configuration
[cookie]
name = "alchemiser_dashboard"
key = "your_random_key_from_step_4"
expiry_days = 30
```

#### Local Development (Skip Auth)

For local development without authentication, set `SKIP_AUTH=true`:

```bash
SKIP_AUTH=true poetry run streamlit run scripts/dashboard.py
```

Or add to your `.env` file:
```
SKIP_AUTH=true
```

#### Security Notes

- **IAM Policy**: The dashboard user has read-only access to prod DynamoDB tables and CloudWatch Logs only
- **Password Storage**: Passwords are bcrypt-hashed, never stored in plaintext
- **Session Cookies**: Encrypted with your cookie key, expire after configured days
- **Access Key Rotation**: Rotate IAM access keys periodically (set a calendar reminder)

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

### "No recent workflow runs found"
- **Table not found**: The DynamoDB table `alchemiser-prod-aggregation-sessions` doesn't exist. Deploy the prod stack with `make deploy`.
- **AWS credentials invalid**: Check that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set correctly in Streamlit secrets.
- **Permissions denied**: The IAM user may be missing the `AlchemiserDashboardReadOnly` policy. Check IAM console.
- **No workflows executed**: The trading system hasn't run any workflows in prod yet.

### "Authentication not configured"
- You're running on Streamlit Cloud but haven't set up the `[credentials]` section in secrets.
- See "Deployment to Streamlit Cloud" above for the full secrets template.

### "No trading data available"
- Check that Alpaca credentials are correct
- Verify you're using the **production** endpoint (`https://api.alpaca.markets`, not paper)
- Ensure the account has trading history

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
