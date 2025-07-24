# Refactoring CLI and Telegram Output

This document outlines an approach to separate the user interface (UI) concerns from the core trading logic. Currently, functions in `main.py` mix signal generation with `print` statements and Telegram message construction.

## Why Refactor?

- **Maintainability** – printing and message formatting are scattered across functions, making updates hard.
- **Testability** – logic that returns data is easier to unit test than code that prints directly.
- **Extensibility** – having a single layer that handles all user-facing output lets us add other channels (email, dashboards) without touching trading code.

## Proposed Structure

```
core/
    ui/
        cli_formatter.py     # Handles console display
        telegram_formatter.py  # Builds Telegram messages
```

- **`cli_formatter.py`**: functions to render tables of indicators, strategy summaries and execution results. The caller passes in structured data and receives formatted strings. The main program simply prints the returned strings.
- **`telegram_formatter.py`**: functions like `build_multi_strategy_message(result)` that accept execution results and return text ready for sending.

Both modules have no side effects besides returning strings.

## Refactoring Steps

1. **Extract formatting logic**
   - Move `display_technical_indicators` from `main.py` to `cli_formatter.py` and change it to return a string rather than printing directly.
   - Move `_build_single_strategy_telegram_message` and `_build_multi_strategy_telegram_message` to `telegram_formatter.py`.
2. **Update callers**
   - In `main.py`, call the formatter functions and print the returned string.
   - `core/telegram_utils.send_telegram_message` should only send text; message composition happens in `telegram_formatter.py`.
3. **Add unit tests**
   - Because formatting functions are pure, they can be easily tested. Tests can verify that given indicator data, the expected strings are produced.
4. **Future extensions**
   - Additional output channels (e.g. web dashboard, log files) can import the same formatting modules or implement their own.

## Example Usage

```python
from core.ui.cli_formatter import render_technical_indicators
from core.ui.telegram_formatter import build_multi_strategy_message

# Generate signals
manager, signals, portfolio = generate_multi_strategy_signals()

# CLI
print(render_technical_indicators(signals))

# Telegram
message = build_multi_strategy_message(result)
send_telegram_message(message)
```

Separating the UI layer keeps the trading logic focused on data and execution, while presentation and messaging live in dedicated modules.
