# Refactoring to config.yaml: Step-by-Step Guide

## 1. Expand config.yaml

Add the following sections and keys to your config.yaml:

```yaml
# Logging configuration
logging:
  level: "INFO"
  multi_strategy_log: "s3://the-alchemiser-s3/multi_strategy_execution.log"
  alpaca_log: "s3://the-alchemiser-s3/alpaca_trader.log"
  trading_bot_log: "the_alchemiser/data/logs/trading_bot.log"
  alpaca_trades_json: "/tmp/alpaca_trades.json"
  nuclear_alerts_json: "/tmp/nuclear_alerts.json"

# Alpaca configuration
alpaca:
  endpoint: "https://api.alpaca.markets"
  paper_endpoint: "https://paper-api.alpaca.markets/v2"
  cash_reserve_pct: 0.05
  slippage_bps: 5

# AWS/Lambda deployment
aws:
  account_id: "211125653762"
  region: "eu-west-2"
  repo_name: "the-alchemiser"
  lambda_arn: "arn:aws:lambda:eu-west-2:211125653762:function:the-alchemiser"
  image_tag: "latest"

# Alert settings
alerts:
  alert_config_s3: "s3://the-alchemiser-s3/alert_config.json"
  cooldown_minutes: 30

# Secrets Manager
secrets_manager:
  region_name: "eu-west-2"
  secret_name: "the-alchemiser-secrets"

# Strategy defaults
strategy:
  default_strategy_allocations:
    nuclear: 0.5
    tecl: 0.5
  poll_timeout: 30
  poll_interval: 2.0
```

---

## 2. Update the Config Loader

- In config.py, update the loader to read all new sections.
- Provide sensible defaults if keys are missing, e.g.:

  ```python
  config['aws'].get('region', 'eu-west-2')
  ```

---

## 3. Refactor Modules

- **Replace hardcoded values** with config lookups:
  - main.py: Use `config['logging']['trading_bot_log']`.
  - `MultiStrategyAlpacaTrader`: Use `config['logging']['multi_strategy_log']`.
  - `AlpacaTradingBot`: Use log paths and slippage from `config['logging']` and `config['alpaca']`.
  - `SecretsManager`, `telegram_utils.py`, `data_provider.py`: Use `config['aws']['region']`.
  - nuclear_trading_bot.py, tecl_trading_bot.py: Use `config['alerts']['alert_config_s3']` and `config['alerts']['cooldown_minutes']`.
  - `StrategyManager`: Use `config['strategy']['default_strategy_allocations']`.

---

## 4. Refactor Shell Script

- In build_and_push_lambda.sh, read AWS parameters from environment variables or parse them from config.yaml using a helper Python script:

  ```bash
  export AWS_ACCOUNT_ID=$(python -c "import yaml; print(yaml.safe_load(open('config.yaml'))['aws']['account_id'])")
  ```

---

## 5. Document the Configuration

- **Update README.md**:
  - Add a section describing all config options and their meanings.
  - Provide an example config.yaml.
  - List required environment variables (API keys, Telegram credentials).

---

## 6. Testing

- Run `pytest` and basic bot commands (`alchemiser bot`, `alchemiser trade`, etc.).
- Verify:
  - Log files are created at the configured paths.
  - AWS/Lambda operations use the correct region/account.
  - Alerts and strategies use the correct config values.

---

## 7. Benefits

- **Centralized configuration** for all environments.
- **Easier deployment** and environment switching.
- **No more scattered constants**—all environment-specific values are in one place.

---

By following these steps, your project will be easier to configure, maintain, and deploy across different environments.
