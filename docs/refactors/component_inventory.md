# Component Inventory

## Reused Components
- `application/execution/smart_execution.py` – order placement strategy.
- `application/alpaca_client.py` – brokerage adapter.
- `domain/strategies/strategy_manager.py` – multi‑strategy orchestration.
- `execution/account_service.py` – account and position access.
- `services/repository/alpaca_manager.py` – low level Alpaca client.

## New/Refactored Components
- `ports` package defining `MarketData`, `OrderExecution`, `RiskChecks`,
  `PositionStore`, `Clock`, and `Notifier` protocols.
- `domain/services/rebalancing_policy.py` – pure portfolio policy placeholder.
- `application/trading/engine_service.py` – relocated legacy `TradingEngine`
  awaiting further decomposition.

## Candidates for Deletion / Consolidation
- `LegacyPortfolioRebalancerStub` once new rebalancing service is implemented.
- Redundant error handling paths inside `engine_service.py` after extraction of
  domain services.
