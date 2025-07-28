# Refactor Plan for `data_provider.py`

## Current Issues
- ~389 lines combining market data fetching, caching and trading client management.
- Uses manual requests for some endpoints and Alpaca SDK for others.
- Cache logic embedded inside the main class; difficult to test.

## Goals
- Provide clear separation between data retrieval and trading actions.
- Move caching logic to a dedicated utility.
- Standardize API interactions via the Alpaca SDK where possible.

## Proposed Modules & Files
- `data/alpaca_client.py` – wrapper around Alpaca SDK providing unified methods.
- `data/cache.py` – simple cache class with expiration handling used by providers.
- `data/provider.py` – high level interface returning market data and account info.

## Step-by-Step Refactor
1. **Implement `data/cache.py`**
   - Generic cache storing JSON-serializable responses with time-based expiration.
   - Methods `get(key)`, `set(key, value)` and `stats()`.

2. **Implement `alpaca_client.py`**
   - Encapsulate API key handling and provide thin wrappers for bars, quotes, orders and account endpoints.
   - Replace direct `requests` usage with this client.

3. **Refactor `UnifiedDataProvider`**
   - Compose `AlpacaClient` and `Cache` instances.
   - Methods like `get_historical_data` delegate to the client and store results in cache.
   - Move trading functions (`get_account_info`, `get_positions`) to a separate `TradingService` if needed.

4. **Add Unit Tests**
   - `tests/data/test_cache.py` verifying expiration behaviour.
   - `tests/data/test_alpaca_client.py` using mocked HTTP responses.

## Rationale
- Decoupling cache and HTTP logic improves readability and facilitates mocking in tests.
- Centralizing Alpaca API interactions reduces duplication across the project and allows easier switching to another broker in the future.

