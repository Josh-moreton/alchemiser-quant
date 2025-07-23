Here is a summary of the code and top-level docstrings for each requested file, which will help you review their responsibilities, identify mixed concerns, and spot refactoring opportunities:

---

### 1. `core/nuclear_trading_bot.py`

**Purpose:**  
Implements the full logic for the Nuclear Energy trading strategy:

- Detects market regime (bull/bear) using SPY and technical indicators.
- Generates signals with multi-layered RSI triggers.
- Constructs a dynamic portfolio of nuclear energy stocks in bull markets (top 3 by momentum, inverse volatility weighting).
- Rotates defensively to tech, bonds, and volatility hedges in bear markets.
- Handles portfolio allocation, technical indicator calculation, and alert generation.
- Integrates with S3 logging, alert service, and supports both continuous and one-shot execution.

**Mixed Concerns/Refactoring Opportunities:**  

- Contains both strategy logic and bot orchestration (data fetching, logging, alerting).
- Some configuration and S3 logic is embedded.
- Could be split into: strategy logic, data/indicator calculation, and bot orchestration.

---

### 2. `core/strategy_engine.py`

**Purpose:**  
Defines classes for the main strategy scenarios:

- `BullMarketStrategy`: Recommends nuclear portfolio in bull markets.
- `BearMarketStrategy`: Combines two bear subgroups using inverse volatility weighting.
- `OverboughtStrategy`, `SecondaryOverboughtStrategy`, `VoxOverboughtStrategy`: Handle overbought conditions for various symbols.

**Mixed Concerns/Refactoring Opportunities:**  

- Pure strategy logic, but tightly coupled to indicator structure.
- Could be refactored for more modular scenario handling.

---

### 3. `core/tecl_strategy_engine.py`

**Purpose:**  
Implements the "TECL For The Long Term" strategy:

- Detects market regime (SPY vs 200 MA).
- Uses multiple RSI-based triggers for volatility protection.
- Focuses on TECL as the growth vehicle, with BIL as defensive cash.
- Rotates between technology and materials sectors (XLK vs KMLM).
- Contains logic for mixed allocations (UVXY/BIL) and sector timing.

**Mixed Concerns/Refactoring Opportunities:**  

- Contains both strategy logic and some data/indicator calculation.
- Could be split into: pure strategy logic, indicator calculation, and orchestration.

---

### 4. `core/strategy_manager.py`

**Purpose:**  
Manages multiple trading strategies in parallel:

- Allocates portfolio between strategies (e.g., Nuclear, TECL).
- Tracks positions for each strategy separately.
- Coordinates strategy execution and reporting.

**Mixed Concerns/Refactoring Opportunities:**  

- Handles both strategy orchestration and position tracking.
- Some configuration and logging setup is included.
- Could be split into: strategy orchestration, position tracking, and reporting.

---

### 5. `execution/alpaca_trader.py`

**Purpose:**  
Executes trades based on nuclear trading signals using Alpaca:

- Connects to Alpaca (paper trading).
- Places orders, rebalances portfolio, and logs trades.
- Reads signals from alerts file.

**Mixed Concerns/Refactoring Opportunities:**  

- Contains both Alpaca API logic and signal parsing.
- Some configuration and S3 logic is embedded.
- Could be split into: Alpaca API wrapper, signal parsing, and trade execution.

---

### 6. `execution/improved_rebalance.py`

**Purpose:**  
Provides improved rebalancing logic for Alpaca trading:

- Uses buying power instead of portfolio value for allocation.
- Handles complete portfolio switches and minimizes trades.
- Respects cash constraints.

**Mixed Concerns/Refactoring Opportunities:**  

- Pure rebalancing logic, but depends on bot/account structure.
- Could be made more generic and decoupled from Alpaca-specifics.

---

### 7. `execution/multi_strategy_trader.py`

**Purpose:**  
Enhanced Alpaca trading integration for multi-strategy execution:

- Supports multiple strategies with position tracking and allocation management.
- Consolidates portfolio rebalancing and strategy performance attribution.
- Provides enhanced reporting and logging.

**Mixed Concerns/Refactoring Opportunities:**  

- Contains both multi-strategy orchestration and Alpaca trading logic.
- Some reporting and logging logic is embedded.
- Could be split into: multi-strategy orchestration, Alpaca trading, and reporting.

---

**Next Steps for Refactoring:**

- Separate strategy logic from orchestration and data/indicator calculation.
- Move configuration, logging, and S3 logic to dedicated modules/utilities.
- Decouple Alpaca API logic from strategy execution and signal parsing.
- Modularize position tracking and reporting.

If you need deeper code-level details or want to see specific function/class implementations for any file, let me know!Here’s a concise explanation of what each main file does, based on your current codebase and comments:

---

### nuclear_trading_bot.py

Implements the full logic for the Nuclear Energy trading strategy:

- Detects market regime (bull/bear) using SPY and technical indicators.
- Generates signals using hierarchical, multi-layered RSI triggers.
- Constructs a dynamic portfolio of nuclear energy stocks in bull markets (top 3 by momentum, inverse volatility weighting).
- Rotates defensively to tech, bonds, and volatility hedges in bear markets.
- Handles technical indicator calculation, alert generation, S3 logging, and both continuous and one-shot execution.
- Contains both the strategy engine and the bot runner.

---

### strategy_engine.py

Contains scenario classes for the nuclear strategy:

- Implements the logic for bull and bear market signal generation.
- Handles overbought/oversold detection and portfolio construction.
- Used by `nuclear_trading_bot` for hierarchical decision-making.
- Focused on signal logic, not execution or data management.

---

### tecl_strategy_engine.py

Implements the TECL (technology leverage) strategy:

- Translates the Composer.trade “TECL For The Long Term (v7)” logic to Python.
- Detects market regime, applies RSI-based triggers, and manages sector rotation (XLK vs KMLM).
- Allocates between TECL, BIL, UVXY, SQQQ, and BSV based on market conditions.
- Handles technical indicator calculation and strategy evaluation.
- Focused on technology sector timing and volatility protection.

---

### strategy_manager.py

Manages multiple strategies and portfolio allocation:

- Runs Nuclear and TECL strategies in parallel.
- Tracks positions for each strategy separately.
- Consolidates signals into a unified portfolio allocation.
- Handles reporting, position tracking, and coordination.
- Centralizes multi-strategy logic, but may have mixed concerns (data, execution, reporting).

---

### alpaca_trader.py

Executes trades via Alpaca based on strategy signals:

- Connects to Alpaca API (paper/live trading).
- Places orders, manages positions, and rebalances portfolio.
- Reads signals from the nuclear strategy and executes trades accordingly.
- Handles account info, logging, and order management.
- Contains both trading logic and some portfolio management.

---

### improved_rebalance.py

Provides an improved portfolio rebalancing function for Alpaca:

- Rebalances using buying power (not portfolio value).
- Handles complete portfolio switches and minimizes trades.
- Prioritizes high-weight positions and respects cash constraints.
- Intended to replace or supplement the rebalance logic in alpaca_trader.py.
- Standalone function, not a full bot.

---

### multi_strategy_trader.py

Enhanced Alpaca trading bot for multi-strategy execution:

- Integrates with `strategy_manager` to execute multiple strategies.
- Tracks and attributes trades to specific strategies.
- Handles consolidated portfolio rebalancing, reporting, and logging.
- Provides advanced features like performance attribution and order tracking.
- Centralizes multi-strategy execution, but may duplicate logic from other modules.

---

## Refactoring Opportunities & Mixed Concerns

- **Separation of Concerns:**  
  Many files mix strategy logic, data management, execution, and reporting. For example, nuclear_trading_bot.py contains both the strategy engine and bot runner; alpaca_trader.py mixes trading and portfolio logic.
- **Redundant/Legacy Code:**  
  Some scenario classes and functions may be legacy or duplicated (e.g., overbought/oversold logic in both strategy_engine.py and nuclear_trading_bot.py).
- **Modularization:**  
  Consider splitting strategy logic, data access, execution, and reporting into separate modules/classes.
- **Unified Data Provider:**  
  You already use a shared data provider—ensure all strategies and bots use it consistently.
- **Portfolio Management:**  
  Centralize portfolio construction and rebalancing logic to avoid duplication between alpaca_trader.py, `improved_rebalance.py`, and multi_strategy_trader.py.
- **Alerting & Logging:**  
  Move alert generation and logging to dedicated services/utilities.

---

If you want a refactoring plan or specific recommendations, let me know your priorities (e.g., modularization, testability, performance, etc.).
