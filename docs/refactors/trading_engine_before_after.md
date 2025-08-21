# Trading Engine Before ➝ After Mapping

| Responsibility (Before) | New Location (After) |
| --- | --- |
| Initialisation modes and orchestration | `application/trading/engine_service.py` |
| Account/position access | future `domain/services` & `ports.PositionStore` |
| Order execution & settlement | `ports.OrderExecution` with adapter implementations |
| Portfolio rebalancing policy | `domain/services/rebalancing_policy.py` |
| Strategy execution | `application/trading/engine_service.py` delegating to strategy managers |
| Reporting helpers | `application/trading/engine_service.py` ➝ future reporting service |

## Call Graph (current)
```
TradingEngine.__init__
 ├─ _init_with_container/_service_manager/_traditional
 │   └─ _init_common_components
 │       ├─ SmartExecution
 │       ├─ LegacyPortfolioRebalancerAdapter
 │       └─ MultiStrategyManager
 ├─ get_account_info ➝ AccountService
 ├─ rebalance_portfolio ➝ portfolio_rebalancer
 └─ execute_multi_strategy ➝ ExecutionManager
```

## Call Graph (target)
```
EngineService.execute
 ├─ PositionStore.get_account_info
 ├─ Strategy orchestrators (per strategy)
 ├─ RebalancingPolicy.calculate_rebalance_orders
 ├─ OrderExecution.place_order
 └─ Notifier.send / ReportingService
```
