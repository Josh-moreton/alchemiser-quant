# Code Review Findings

This document expands on the earlier summary that "a large portion of the code mixes business logic with I/O, has duplicated routines and relies heavily on global configuration files." The goal is to highlight concrete examples and outline steps to improve the architecture.

## 1. Mixing Business Logic with I/O

Several modules load secrets, read configuration files, print to the console or write logs while performing trading logic. Examples:

- `nuclear_trading_bot.py` initializes logging and the configuration at import time. The global configuration object is created in lines 30–32 which makes unit testing difficult because importing the module immediately reads `config.yaml` and configures logging.
- The method `run_once` in `NuclearTradingBot` fetches data, evaluates strategies and prints results and logs alerts in one place. See lines 422—463 where alerts are logged and console output is printed alongside business decisions.
- `telegram_utils.py` fetches secrets from AWS as soon as the module is imported (lines 5–7). This mixes network I/O with the simple utility of sending a Telegram message.

## 2. Duplicate Routines

- Two separate classes, `DataProvider` and `AlpacaDataProvider`, both implement `get_current_price` with nearly identical logic. Compare lines 133–166 with lines 195–213 in `core/data_provider.py`.

## 3. Heavy Use of Global Configuration

Most modules instantiate `Config()` directly instead of accepting configuration via dependency injection. For example:

```python
config = Config()
logging_config = config['logging']
```

occurs at the top of `core/nuclear_trading_bot.py` (lines 30–32). This makes testing or changing configuration at runtime difficult.

## Step-by-Step Plan to Resolve

1. **Introduce Dependency Injection**
   - Pass configuration objects, secrets manager instances and data providers into classes instead of creating them globally. This allows tests to supply mocks and prevents side effects at import time.
2. **Separate I/O from Business Logic**
   - Move console output and file logging out of strategy classes. Strategy evaluation should return plain data structures; a separate orchestrator can handle printing and persistence.
   - Lazy-load secrets only when needed, or inject the values from the orchestrator layer.
3. **Consolidate Data Provider Classes**
   - Merge `DataProvider` and `AlpacaDataProvider` or extract a common base class to eliminate duplicated code for price retrieval.
4. **Centralize Configuration Management**
   - Load `config.yaml` once in the CLI layer (`main.py`) and pass the resulting configuration object into lower-level classes. Avoid global Config instances in modules.
5. **Improve Testing Strategy**
   - Provide test fixtures that mock external services (AWS, Alpaca, Telegram). With dependency injection in place, tests can run without network access or secrets.

Following these steps will reduce coupling, improve testability and make the architecture easier to maintain.
