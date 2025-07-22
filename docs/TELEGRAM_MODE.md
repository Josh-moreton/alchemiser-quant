# Telegram Mode Process Flow

This document explains what happens when you execute the Telegram mode of the project with:

```bash
python main.py telegram
```

It covers the main classes and functions involved so a developer can follow the control flow.

## 1. Entry Point

The CLI in `main.py` maps the `telegram` mode to the `run_alpaca_telegram_bot()` function.

```
parser.add_argument('mode', choices=['bot', 'live', 'paper'], ...)
...
elif args.mode == 'live':
    success = run_live_trading_bot()
```

## 2. `run_alpaca_telegram_bot()`

Defined in `main.py`, this function orchestrates signal generation, Alpaca execution and the Telegram update.
Key steps are:

1. **Imports** – `NuclearTradingBot` for signal creation, `send_telegram_message` for messaging and `AlpacaTradingBot` for order execution【F:main.py†L187-L199】.
2. **Generate signals** – instantiate `NuclearTradingBot`, call `run_once()` and abort if it returns `None` (also sending a Telegram failure message)【F:main.py†L202-L212】.
3. **Initialize Alpaca** – create an `AlpacaTradingBot`, retrieve account info and print a summary before trading【F:main.py†L217-L229】.
4. **Execute trades** – monkey‑patch `rebalance_portfolio` to capture executed orders while calling `execute_nuclear_strategy()`【F:main.py†L230-L248】.
5. **Show final status** – fetch account info again, display the summary and mark completion【F:main.py†L255-L269】.
6. **Send Telegram summary** – build a message with positions and orders then call `send_telegram_message`【F:main.py†L271-L306】.

The function returns `True` on success or `False` on any failure.

## 3. Signal Generation

`NuclearTradingBot.run_once()` performs the strategy analysis and logs resulting alerts:

```
alerts = self.run_analysis()
if alerts:
    for alert in alerts:
        self.log_alert(alert)
    ...
else:
    print("❌ Unable to generate nuclear energy signal")
    return None
```

【F:core/nuclear_trading_bot.py†L414-L455】

The first alert object is returned, which `run_alpaca_telegram_bot()` uses to proceed with trading.

## 4. Alpaca Execution

`AlpacaTradingBot.execute_nuclear_strategy()` reads the JSON log of recent alerts, converts them to a target portfolio, rebalances the account and logs all orders:

```
signals = self.read_nuclear_signals()
if not signals:
    ...
orders = self.rebalance_portfolio(target_portfolio)
if orders:
    self.log_trade_execution(target_portfolio, orders, account_info)
```

【F:execution/alpaca_trader.py†L388-L447】

The orders returned by `rebalance_portfolio` are captured in `run_alpaca_telegram_bot()` for inclusion in the Telegram update.

## 5. Telegram Messaging

The helper `send_telegram_message()` (in `core/telegram_utils.py`) posts the message to the Telegram Bot API:

```
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
resp = requests.post(url, data=payload)
```

【F:core/telegram_utils.py†L11-L38】

The message text is assembled by `run_alpaca_telegram_bot()` using account information, open positions and captured orders.

## Summary

When running `python main.py telegram`, the program:

1. Generates nuclear trading signals.
2. Executes the corresponding trades via Alpaca, capturing order details.
3. Reports the outcome, account summary and orders to Telegram.

If any step fails, a Telegram notification is still sent indicating the error, ensuring visibility into the bot's status.
