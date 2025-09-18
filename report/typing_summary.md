# Typing Architecture Audit Report

Comprehensive analysis of typing architecture compliance across the codebase.

## Summary

- **Total Violations**: 164
- **Files Analyzed**: 182
- **Lines of Code**: 34,946

## Violations by Severity

- 🔴 **CRITICAL**: 0
- 🟠 **HIGH**: 0
- 🟡 **MEDIUM**: 164
- 🟢 **LOW**: 0

## Violations by Type

- **ANN401_RETURN**: 86
- **ANN401_PARAM**: 32
- **MISSING_DTO_SUFFIX**: 28
- **INCORRECT_NAMING_PATTERN**: 18

## Detailed Violations

### 🟡 MEDIUM Violations

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:295**
- Type: `ANN401_PARAM`
- Message: Unbounded 'Any' usage in parameter 'open_orders'
- Fix: Use Union types or specific interfaces instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/main.py:316**
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

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:166**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:201**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:227**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:263**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:302**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

**/home/runner/work/alchemiser-quant/alchemiser-quant/the_alchemiser/orchestration/portfolio_orchestrator.py:472**
- Type: `ANN401_RETURN`
- Message: Unbounded 'Any' usage in return type
- Fix: Return specific DTO types or Optional[ConcreteType] instead of Any

... and 154 more

