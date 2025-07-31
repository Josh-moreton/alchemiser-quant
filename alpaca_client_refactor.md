# Refactoring Plan for `the_alchemiser/execution/alpaca_client.py`

`alpaca_client.py` currently implements many unrelated responsibilities in one massive class. The following plan outlines how to split the file into focused modules and simplify maintenance.

## Key Problems

- Monolithic `AlpacaClient` mixes API calls, order management, WebSocket logic, and rebalance operations.
- Over 1100 lines with 20+ methods complicate testing and readability.

## Proposed Modules

1. **`alpaca_client/api.py`** – Low level REST API wrappers for positions and orders.
2. **`alpaca_client/orders.py`** – Helpers for market, limit, and smart limit order execution.
3. **`alpaca_client/websocket.py`** – Manage the WebSocket connection and stream updates.
4. **`alpaca_client/rebalancer.py`** – Encapsulate portfolio rebalance logic.

## Smaller Classes

- `PositionManager` for fetching and validating positions.
- `OrderExecutor` responsible for placing and cancelling orders.
- `WebsocketWatcher` dedicated to streaming order updates.

## Utilities and Helpers

- Extract price rounding and fractionability checks into utility functions.
- Centralize custom error definitions.

## Testing Improvements

- Each module can be unit-tested separately.
- Provide mockable interfaces for the Alpaca SDK to simplify integration tests.

## Documentation and Type Hints

- Keep concise docstrings and add type hints across modules to clarify interfaces.
