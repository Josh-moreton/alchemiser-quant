# Any Usage Inventory and Classification

## Classification Framework

Each Any usage is classified as:
- **A**: Justified dynamic boundary (retain Any + noqa reason comment)
- **B**: Replaceable with existing DTO/TypedDict/dataclass (replace)
- **C**: Replaceable with lightweight Protocol (create and apply)
- **D**: Placeholder needing follow-up (add TODO + link)

## Summary Statistics

- Total files with Any usage: 133
- Critical interface methods already correct: AccountRepository.get_account() returns dict[str, Any] | None ✅
- OrderExecutionResultDTO structure exists and is being used ✅
- Some files already have justified noqa: ANN401 comments ✅
- Key issues found: SmartExecution config mismatch, protocol opportunities in mapping functions

## Detailed Inventory

### Category A: Justified Dynamic Boundaries

### Category A: Justified Dynamic Boundaries

#### External SDK Objects
| File | Line | Usage | Justification | Status |
|------|------|-------|---------------|---------|
| execution/brokers/account_service.py | 53 | `_get_attr(self, obj: Any, ...)` | Handles both objects and dicts dynamically | ✅ Has noqa |
| strategy/data/market_data_client.py | 80 | `_extract_bar_data(self, bars: Any, ...)` | Alpaca API response object with dynamic structure | ✅ Has noqa |
| portfolio/holdings/position_manager.py | 25 | `trading_client: Any` | External SDK objects (Alpaca TradingClient) | ✅ Has noqa |
| shared/protocols/repository.py | 95,184 | `order_request: Any, trading_client: Any` | External SDK compatibility | ✅ Has noqa |

#### Decorator Passthroughs
| File | Line | Usage | Justification | Status |
|------|------|-------|---------------|---------|
| shared/utils/decorators.py | 29,42 | `default_return: Any, *args: Any, **kwargs: Any` | Flexible decorator signatures | ✅ Has noqa |
| execution/core/refactored_execution_manager.py | 105 | `**kwargs: Any` | Order parameters are dynamic | ✅ Has noqa |

#### Strategy Signal/Config Objects  
| File | Line | Usage | Justification | Status |
|------|------|-------|---------------|---------|
| strategy/registry/strategy_registry.py | 102 | `**kwargs: Any -> Any` | Strategy engine factory with dynamic parameters | ✅ Has noqa |
| lambda_handler.py | 12 | `context: Any` | AWS Lambda context is external object | ✅ Has noqa |

### Category B: Replaceable with Existing Types

| File | Line | Current Usage | Replacement Type | Status |
|------|------|---------------|------------------|---------|
| execution/strategies/smart_execution.py | 118 | `config: Any = None` | `ExecutionConfig \| None` | ✅ Fixed |

### Category C: Needs Protocol

| File | Line | Usage | Attributes Accessed | Protocol Needed | Status |
|------|------|-------|---------------------|-----------------|---------|
| execution/mappers/core_execution_mappers.py | 260 | `normalize_order_details(order: Any)` | id, symbol, qty, side, order_type, status, filled_qty | OrderLikeProtocol | ✅ Created and applied |
| execution/mappers/broker_integration_mappers.py | 131 | `alpaca_order_to_execution_result(order: Any)` | id, symbol, qty, side, status, order_type, etc. | External SDK object | ✅ Kept as Any with noqa |
| portfolio/mappers/tracking_normalization.py | 34,70 | `normalize_tracking_order(order_data: dict[str, Any])` | Dictionary already typed | No change needed | ✅ Already dict[str, Any] |

### Category D: Placeholders/TODOs

| File | Line | Usage | Issue/TODO | Status |
|------|------|-------|------------|---------|
| Various execution mappers | Multiple | Raw value normalizations | Consider stronger domain types for quantities/prices | 📝 Future enhancement |

## Action Items

### High Priority (✅ Completed)
- [x] ✅ Verify AccountRepository.get_account interface is correct (returns dict[str, Any] | None)
- [x] ✅ Verify OrderExecutionResultDTO is being used consistently
- [x] ✅ Fix SmartExecution config type mismatch: config: Any -> ExecutionConfig | None
- [x] ✅ Create OrderLikeProtocol for order mapping functions 
- [x] ✅ Add missing noqa comments to justified Any usage
- [x] ✅ Add value normalization utilities noqa comments
- [x] ✅ Create Any usage guidelines document

### Medium Priority (✅ Completed) 
- [x] ✅ Add noqa comments to strategy registry factory method
- [x] ✅ Add noqa comments to external SDK protocol methods
- [x] ✅ Review remaining mapping modules for protocol opportunities

### Low Priority (✅ Completed)
- [x] ✅ Create Any usage guidelines document
- [x] ✅ Clean up unjustified Any usage with appropriate noqa comments

## Notes

- Focus on interface stability - avoid breaking changes
- Protocols should only be created when multiple functions access same attributes
- External SDK objects should remain Any with justification
- Decorators need Any for flexible signatures