# Typing Architecture Audit Report

Comprehensive analysis of typing architecture compliance across the codebase.

## Summary

- **Total Violations**: 301
- **Files Analyzed**: 182
- **Lines of Code**: 35,245

## Violations by Severity

- 🔴 **CRITICAL**: 0
- 🟠 **HIGH**: 14
- 🟡 **MEDIUM**: 287
- 🟢 **LOW**: 0

## Violations by Type

- **ANN401_PARAM**: 154
- **ANN401_RETURN**: 87
- **MISSING_DTO_SUFFIX**: 28
- **INCORRECT_NAMING_PATTERN**: 18
- **ANN401_DTO_FIELD**: 13
- **FORBIDDEN_CROSS_MODULE_IMPORT**: 1

## Detailed Violations

### 🟠 HIGH Violations

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/dto/technical_indicators_dto.py:278**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'result'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/dto/execution_dto.py:43**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'metadata'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/dto/rebalance_plan_dto.py:110**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'metadata'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/accounts.py:104**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'details'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/accounts.py:132**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'raw'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/enriched_data.py:28**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'raw'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/enriched_data.py:29**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'domain'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/enriched_data.py:30**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'summary'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/enriched_data.py:55**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'raw'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/shared/schemas/enriched_data.py:56**
- Type: `ANN401_DTO_FIELD`
- Message: Unbounded 'Any' usage in DTO field 'summary'
- Fix: Use concrete types: str | int | bool or dict[str, str] instead of Any

... and 4 more

### 🟡 MEDIUM Violations

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:276**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'result'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:302**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'strategy_signals'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:304**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'account_info'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:305**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'current_positions'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:307**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'open_orders'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:328**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'orders_executed'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/lambda_handler.py:170**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'event'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/lambda_handler.py:191**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:86**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'account_info'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:109**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'current_positions'
- Fix: Use Union types or specific interfaces instead of Any

... and 277 more

