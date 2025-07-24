
# 1. **main.py** (Refactored)

- **Lines 80-169**: `display_technical_indicators()` CLI formatting is now fully extracted to `core/ui/cli_formatter.py`.
- **Lines 171-231**: `generate_multi_strategy_signals()` now returns structured data only; all printing/formatting is handled in the orchestration layer.
- **Lines 264-317**: `run_multi_strategy_trading()` orchestration is separated from formatting and notification logic. Telegram and CLI formatting are delegated to their respective modules.

**Status:** All step 1 refactors for `main.py` are complete. CLI and Telegram formatting are separated, signal generation is pure, and orchestration is clean.

---

### 2. **core/nuclear_trading_bot.py**

- **Lines 217-232**: `_ensure_scalar_price` returns `None` on errors without logging. Should log failures and consider raising exceptions on invalid data.
- **Lines 266-272**: `handle_nuclear_portfolio_signal()` imports alert services at runtime. Should use dependency injection.
- **General**: This file mixes orchestration, data management, and execution with some business logic. Consider further splitting pure strategy logic, data access, and alerting.

---

### 3. **core/tecl_trading_bot.py**

- **General**: This file handles both orchestration/execution and some business logic. Pure strategy logic should reside in `tecl_strategy_engine.py`. Ensure all technical indicator calculation and alert generation are separated from execution/orchestration.

---

### 4. **core/strategy_engine.py**

- **General**: This file is mostly pure business logic, but ensure no data fetching or execution code is present. If any logging, data access, or UI code is found here, it should be moved out.

---

### 5. **core/telegram_utils.py**

- **Lines 5-7, 20-28**: Credentials are loaded at import time and errors are printed. Should be lazy-loaded from environment or secrets manager and log failures.

---

### 6. **core/s3_utils.py**

- **Lines 195-202**: `S3FileHandler.emit()` prints errors instead of logging. Should use `logging.error` and consider retries.

---

### 7. **core/data_provider.py**

- **Lines 92-106, 190-235**: Broad `except Exception` hides API errors when fetching data. Should handle Alpaca errors explicitly with retry/backoff and propagate/log errors.

---

### 8. **execution/alpaca_trader.py**

- **Lines 373-379**: Bot waits a fixed 10 seconds after sells. Should poll order status with exponential backoff instead.
- **General**: This file mixes trading logic, data access, and user feedback (print/logging). Consider extracting user feedback and reporting to a separate module.

---

### 9. **execution/multi_strategy_trader.py**

- **Lines 164-179**: When no strategy matches an order, `_determine_order_strategy` attributes it to all strategies. Should mark attribution as "unknown" or improve the signal-to-order matching.

---

### 10. **UI/Formatting**

- **main.py** and other files: Printing and message formatting are scattered across functions. Should be centralized in `core/ui/cli_formatter.py` and `core/ui/telegram_formatter.py` as per `docs/refactor_ui.md`.

---

### 11. **General Patterns**

- **Print statements**: Found throughout core and execution modules for user feedback. Should be replaced with logging or moved to UI/formatter modules.
- **Logging setup**: Sometimes duplicated or mixed with business logic. Should be centralized.
- **Exception handling**: Broad `except Exception` blocks are used in many places, sometimes swallowing errors or returning `None`. Should be replaced with explicit error handling and logging.

---

### 12. **Tests**

- Some test files (e.g., `test_multi_strategy.py`) mix test logic with print statements for reporting. Should use assertions and logging instead.

---

**References for refactoring and best practices:**

- `docs/CODE_REVIEW.md` (detailed line-by-line review and recommendations)
- `docs/refactor_ui.md` (proposed structure for UI separation)
- `docs/TEST_REVIEW.md` (test coverage and structure recommendations)

---

**Summary:**  
The most critical areas for refactoring are in `main.py`, `core/nuclear_trading_bot.py`, `core/tecl_trading_bot.py`, and the execution modules. Focus on extracting UI/formatting, centralizing logging, separating data access from business logic, and improving error handling. The documentation in `docs/CODE_REVIEW.md` and `docs/refactor_ui.md` provides detailed guidance for these changes.Here’s a focused review of your codebase with respect to **separation of concerns** and where business logic is intermixed with other responsibilities. This is based on your code, tests, and the code review/refactor docs you provided.

---

## 1. **main.py**

- **Problem:** Functions like `display_technical_indicators`, `generate_multi_strategy_signals`, and `run_multi_strategy_trading` mix CLI formatting, signal generation, trading execution, and notification logic.
- **Refactor:**  
  - Move all CLI/print formatting to cli_formatter.py.
  - Move Telegram message construction to telegram_formatter.py.
  - Keep main.py as a thin orchestration layer that only calls service/logic modules and prints their output.

---

## 2. **nuclear_trading_bot.py**

- **Problem:**  
  - `_ensure_scalar_price` swallows conversion errors and does not log or raise, mixing error handling with business logic.
  - `handle_nuclear_portfolio_signal` imports alert services at runtime, mixing dependency management with business logic.
- **Refactor:**  
  - Move error handling to a utility or decorator.
  - Use dependency injection for alert/logging services.

---

## 3. **strategy_manager.py**

- **Problem:**  
  - `_get_nuclear_portfolio_allocation` returns hard-coded values, mixing configuration with logic.
- **Refactor:**  
  - Move allocations to config files or a dedicated configuration module.

---

## 4. **data_provider.py**

- **Problem:**  
  - Broad `except Exception` blocks in `_fetch_historical_data` and `get_current_price` mix error handling, logging, and business logic.
- **Refactor:**  
  - Use explicit exception handling and move retry/backoff logic to a utility or decorator.

---

## 5. **s3_utils.py**

- **Problem:**  
  - `S3FileHandler.emit()` prints errors instead of logging, and does not retry or propagate.
- **Refactor:**  
  - Use the logging module for errors and consider a retry utility.

---

## 6. **telegram_utils.py**

- **Problem:**  
  - Credentials are loaded at import time and errors are printed, mixing secrets management, error handling, and business logic.
- **Refactor:**  
  - Lazy-load credentials and use logging for errors. Move secrets management to a dedicated module.

---

## 7. **alpaca_trader.py**

- **Problem:**  
  - Fixed sleep after sells (e.g., `time.sleep(10)`) mixes timing logic with trading logic.
- **Refactor:**  
  - Replace with a polling function or backoff utility.

---

## 8. **lambda_handler.py**

- **Problem:**  
  - Invokes live trading unconditionally, mixing deployment logic with trading logic.
- **Refactor:**  
  - Read mode from config and enforce safeguards in a dedicated deployment handler.

---

## 9. **Tests**

- **Problem:**  
  - Many test files mix test logic with print/debug output.
- **Refactor:**  
  - Use assertions only; move scenario/parameterization to fixtures or parameterized tests.

---

## 10. **General Patterns**

- **Hard-coded values** (allocations, file paths, etc.) are scattered throughout business logic.
  - **Refactor:** Move to config files or a config module.
- **Print statements** are used for logging in several places.
  - **Refactor:** Use the logging module everywhere.
- **Dependency management** (e.g., runtime imports, global state) is mixed with business logic.
  - **Refactor:** Use dependency injection and pass services as arguments.

---

## **Summary Table**

| File/Module                  | Problem Area                        | Refactor To...                        |
|------------------------------|-------------------------------------|---------------------------------------|
| main.py                      | CLI/print, business logic mixed     | ui/cli_formatter, telegram_formatter  |
| nuclear_trading_bot.py  | Error handling, runtime imports     | utils, dependency injection           |
| strategy_manager.py     | Hard-coded config                   | config module/file                    |
| data_provider.py        | Error handling, retry logic         | utils/decorators                      |
| s3_utils.py             | Logging, retry                      | logging module, retry utility         |
| telegram_utils.py       | Secrets, error handling             | secrets module, logging               |
| alpaca_trader.py   | Timing logic                        | polling/backoff utility               |
| lambda_handler.py            | Deployment logic                    | deployment handler                    |
| tests/                       | Print/debug in tests                | assertions, fixtures                  |

---

**Next Steps:**  

- Extract all formatting and messaging to UI modules.
- Move config, error handling, and retry logic to dedicated modules/utilities.
- Use dependency injection for all services (data, alerts, logging).
- Remove all print statements from business logic and tests.

Let me know if you want a concrete refactor plan or code examples for any of these!
