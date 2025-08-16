# TODO Comment Groupings

Total TODO comments: 102.

## Pydantic Migration (7 TODOs)
Convert existing dataclasses and loosely typed structures to `pydantic` models for validation and parsing where appropriate in non-domain layers.
This batch now touches:
- `application/orders/order_validation.py`
- `application/tracking/strategy_order_tracker.py`
- `application/types.py`

## Structured Type Migration (Phase-based) (80 TODOs)
Roll out well-defined types across interfaces and services. Most TODOs reference migration phases (5–15).
Shared work includes:
- Replacing `dict`/`Any` with `AccountInfo`, `ExecutionResult`, `OrderDetails`, etc.
- Updating CLI and email templates to use structured data.
- Adopting typed cache entries in data providers.

## Strategy & KLMDecision Updates (10 TODOs)
Adopt `KLMDecision` and `KLMVariantResult` in strategy modules and remove temporary `type: ignore` markers.
Affected files: `domain/strategies/klm_*` and `strategy_manager.py`.

## Return Type Alignment (9 TODOs)
Standardize return values in trading and tracking code to domain-specific summaries (`StrategyPnLSummary`, `OrderHistoryData`, etc.).
Primary locations: `application/trading/engine_service.py` and `application/tracking/*`.

## Implementation Gaps (3 TODOs)
Actual logic still pending:
- Error rate thresholds and alerting.
- Cache invalidation for position manager.
- RSI filtering logic in base KLM variant.

## Miscellaneous (3 TODOs)
- Add missing imports once data structures stabilize.
- Provide type stubs for third-party libraries (`pyproject.toml`).

## DDD Compliance Review
- Removed Pydantic migration notes from domain models to preserve framework-free domain layer (`domain/models/account.py`, `market_data.py`, `order.py`, `position.py`, `strategy.py`).
- Updated CLI TODO to reference `the_alchemiser.domain.types.AccountInfo` instead of legacy `core.types` (`interface/cli/cli_formatter.py`).
