# Plan to refactor trading bot

## 1. **Separation of Concerns: Modularize the Bot**

### **A. Data Acquisition Service**

- **Responsibility:** Fetch and cache all market data.
- **Implementation:**  
  - Move `DataProvider` to its own file (e.g., `core/data_provider.py`).
  - All data fetching, caching, and price retrieval logic lives here.
  - Expose a clean API: `get_data(symbol, period)`, `get_current_price(symbol)`.

### **B. Strategy Evaluation Service**

- **Responsibility:** Purely evaluate signals based on data and indicators.
- **Implementation:**  
  - Refactor `NuclearStrategyEngine` into its own file (e.g., `core/strategy_engine.py`).
  - Remove any direct data fetching or logging from this class.
  - Accept data/indicators as arguments, return signals/portfolio recommendations.

### **C. Alert Generation Service**

- **Responsibility:** Convert strategy output into alert objects.
- **Implementation:**  
  - Move `Alert` and alert creation logic to `core/alert_service.py`.
  - Accepts strategy output and generates alert(s) with all required info.

### **D. User Interface / Runner**

- **Responsibility:** Orchestrate the workflow, handle CLI, logging, and console output.
- **Implementation:**  
  - main.py becomes a thin runner:  
    - Calls data provider → strategy engine → alert service.
    - Handles all console I/O and logging.
    - No business logic here.

---

## 2. **Refactor Strategy Engine: Extract Scenario Logic**

### **A. Extract Market Scenario Handlers**

- **Responsibility:** Each scenario (bull, bear, overbought, etc.) is a separate class or function.
- **Implementation:**  
  - In `core/strategy_engine.py`, create classes like:
    - `BullMarketStrategy`
    - `BearMarketStrategy`
    - `OverboughtStrategy`
    - etc.
  - Each class/function implements a `recommend()` method that takes indicators and returns a signal.
  - `NuclearStrategyEngine` becomes a coordinator that delegates to these scenario handlers.

### **B. Use a Strategy Pattern or Rule Engine**

- **Responsibility:** Make it easy to add/modify scenarios.
- **Implementation:**  
  - Maintain a list of scenario handlers.
  - Iterate through them in order of priority; the first to return a valid signal is used.
  - Example:

    ```python
    for handler in self.handlers:
        signal = handler.recommend(indicators)
        if signal:
            return signal
    ```

---

## 3. **Example New Structure**

```
core/
├── __init__.py
├── data_provider.py         # Data acquisition
├── strategy_engine.py       # Strategy coordination and scenario handlers
├── alert_service.py         # Alert creation and formatting
├── indicators.py            # Technical indicators
├── nuclear_trading_bot.py   # (Thin) Orchestrator class
```

- main.py only handles CLI and orchestration.

---

## 4. **Benefits**

- **Testability:** Each service/class can be unit tested in isolation.
- **Extensibility:** Add new strategies/scenarios by adding new handler classes.
- **Maintainability:** Each file/class has a single responsibility.
- **Readability:** Business logic is not mixed with I/O or logging.

---

## 5. **Step-by-Step Refactor Plan**

1. **Extract `DataProvider` to `data_provider.py`.** - DONE
2. **Extract `Alert` and alert creation logic to `alert_service.py`.** - DONE
3. **Move all scenario-specific methods from `NuclearStrategyEngine` to their own classes in `strategy_engine.py`.**
4. **Refactor `NuclearStrategyEngine` to coordinate scenario handlers.**
5. **Update `NuclearTradingBot` to only orchestrate:**
    - Fetch data → calculate indicators → evaluate strategy → generate alerts → log/output.
6. **Update main.py to only handle CLI and call the orchestrator.**
7. **Write unit tests for each new service/class.**

## Configuration management

Hard-coded email addresses, log paths, and credentials appear throughout. A configuration file or environment-based settings object would centralize these parameters.
