# Refactoring Plan for `UnifiedDataProvider`

1. **Split responsibilities into dedicated services**  
   The current `__init__` sets up config loading, caching, secrets, Alpaca clients, and real-time pricing, making the class hard to test or reuse.  
   - Introduce separate modules/classes for configuration, secrets, market-data client, trading client, and real-time streaming.  
   - Use dependency injection so tests can supply mock clients without network calls.

2. **Introduce typed domain models**  
   The provider still relies on untyped DataFrames with TODOs for stronger types.  
   - Define dataclasses or Pydantic models for bars, quotes, positions, and account info.  
   - Return these models instead of loose dicts/`pd.DataFrame` to improve clarity and safety.

3. **Refactor caching into a reusable component**  
   Caching is implemented manually inside `get_data` with a plain dictionary and timestamp checks.  
   - Extract caching logic into its own `CacheManager` (e.g., using `cachetools.TTLCache`).  
   - Allow other services to reuse cache logic and make cache duration configurable.

4. **Modernize price-fetching flow**  
   `get_current_price` mixes subscription management, sleeps, and REST fallbacks in one method.  
   - Move subscription orchestration into the real-time pricing service.  
   - Provide asynchronous or callback-based interfaces to avoid blocking sleeps and to better handle timeouts.

5. **Separate trading/account operations**  
   Account and position queries live alongside market-data logic.  
   - Extract an `AccountService` (account info, positions, portfolio history) distinct from market-data retrieval.  
   - Expose narrow interfaces so components needing only account data don’t pull in full market-data dependencies.

6. **Centralize error handling and logging**  
   Many methods repeat large try/except blocks with `log_error_with_context`.  
   - Create a decorator or context manager that wraps service methods, logging exceptions consistently.  
   - Standardize custom exception types to reduce duplication and improve traceability.

7. **Improve testability and modularity**  
   - After refactoring, write unit tests for each service with mocked Alpaca responses.  
   - Provide integration tests verifying interaction among services (caching, real-time fallback, trading).

8. **Gradually migrate call sites**  
   - Update all modules importing `UnifiedDataProvider` (e.g., execution engines, strategy managers) to consume the new services via interfaces.  
   - Maintain a thin compatibility layer temporarily to avoid breaking existing code during migration.

### Testing
No tests were executed; this is a design plan only.

### Notes
This plan assumes further investigation of real-time components (`RealTimePricingManager`) and utilities (`price_fetching_utils`) for consistent interfaces and naming conventions.
