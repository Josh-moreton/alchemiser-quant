# To-Do List

1. **Refactor strategy modules (`strategy_engine.py`, `tecl_strategy_engine.py`):**
   - Move logging, NumPy, pandas, and warnings usage out of the domain layer.
   - Replace raw `dict` and `Any` usage with explicit value objects, `TypedDict`, or dataclasses.
   - Split the large modules into smaller, type-safe components that respect domain purity.

2. **Strengthen application layer typing (`trading_engine.py`, `alpaca_client.py`):**
   - Replace `Any` dependency injection parameters and attributes with well-defined `Protocol`s or domain types.
   - Ensure `get_order_by_id` returns a domain-specific structure instead of `Any`.

3. **Improve shared-kernel value objects:**
   - Update `Percentage.from_percent` to accept (and normalize to) `Decimal` rather than `float`.

4. **Align repository protocols with domain contracts:**
   - Refactor `TradingRepository.get_account_portfolio_value` to return a `Money` or `Decimal` object instead of a stringified decimal.
   - Expand repository protocol definitions to cover all required operations using precise types.

5. **Enforce domain boundaries:**
   - Ensure domain files avoid direct logging and third-party imports; inject such concerns from outer layers.

6. **Testing and type-checking:**
   - Add unit tests for strategy modules post-refactor.
   - Expand mypy checks to cover the refactored modules and enforce strict typing across the project.

7. **Future maintenance:**
   - Adopt the documented patterns and architectural principles for any new typing-related code to keep the system scalable and maintainable.

