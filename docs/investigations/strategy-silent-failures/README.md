# Strategy Module Silent Failure Investigation

**Status:** In Progress  
**Date Started:** 2025-12-15  
**Investigator:** GitHub Copilot  

## Objective

Investigate and document all error handling patterns in the strategy evaluation pipeline to ensure:
- No silent failures that could produce incorrect signals
- No logic changes due to unhandled edge cases or missing data
- Complete visibility into data quality issues affecting strategy evaluation
- Robust error propagation from data fetching through signal generation

## Executive Summary

This investigation identified **20+ silent failure patterns** across the Strategy module where errors are caught but execution continues with fallback values that could mask data quality issues or produce misleading trading signals.

### Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 5 | Directly affects trading decisions |
| **High** | 5 | Data quality issues that propagate |
| **Medium** | 6 | Partial functionality loss |
| **Low** | 4+ | Acceptable design decisions |

## Investigation Phases

| Phase | Status | Deliverable |
|-------|--------|-------------|
| Phase 1: Silent Fallback Audit | ✅ Complete | [01-silent-fallback-audit.md](./01-silent-fallback-audit.md) |
| Phase 2: Validation Gap Analysis | ✅ Complete | [02-validation-gap-matrix.md](./02-validation-gap-matrix.md) |
| Phase 3: Error Propagation Analysis | ✅ Complete | [03-error-propagation-flowchart.md](./03-error-propagation-flowchart.md) |
| Phase 4: Testing Gap Identification | ✅ Complete | [04-testing-gap-report.md](./04-testing-gap-report.md) |
| Phase 5: Monitoring & Alerting Review | ✅ Complete | [05-monitoring-coverage-matrix.md](./05-monitoring-coverage-matrix.md) |
| Phase 6: Recommendations | ✅ Complete | [06-remediation-backlog.md](./06-remediation-backlog.md) |

## Critical Files Reviewed

| Component | File Path | Focus Area |
|-----------|-----------|------------|
| Signal Generation | `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py` | Indicator fallback (L476-506) |
| Feature Pipeline | `the_alchemiser/strategy_v2/adapters/feature_pipeline.py` | Exception swallowing (L285-312) |
| Market Data Service | `the_alchemiser/shared/services/market_data_service.py` | Quote fallback (L255-273) |
| Market Data Adapter | `the_alchemiser/strategy_v2/adapters/market_data_adapter.py` | Partial failures (L196-310) |
| Indicator Service | `the_alchemiser/strategy_v2/indicators/indicator_service.py` | RSI/MA fallback (L65-104) |
| DSL Evaluator | `the_alchemiser/strategy_v2/engines/dsl/dsl_evaluator.py` | Symbol exclusion (L100-180) |
| Aggregator | `the_alchemiser/aggregator_v2/lambda_handler.py` | Timeout handling |

## Quick Reference: Top 5 Critical Issues

1. **Technical indicators fallback to 0.0** - RSI=0.0 triggers wrong buy signals
2. **Feature pipeline swallows all exceptions** - Returns neutral defaults masking failures
3. **Quote one-sided fallback** - Artificial zero spread affects pricing
4. **RSI neutral fallback (50.0)** - Indistinguishable from real neutral signal
5. **No aggregation timeout detection** - Workers can die without notification

## Next Steps

See [06-remediation-backlog.md](./06-remediation-backlog.md) for prioritized fixes.
