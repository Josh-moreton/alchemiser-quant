# Batch 13 Migration Plan

**Date**: January 2025  
**Batch Size**: 15 files  
**Focus**: Portfolio services, domain interfaces, and domain strategies

## Target Files for Migration

| # | File | Current Location | Target Location | Business Unit | Priority |
|---|------|------------------|-----------------|---------------|----------|
| 1 | `portfolio_pnl_utils.py` | `application/portfolio/` | `portfolio/utils/portfolio_pnl_utils.py` | portfolio | MEDIUM |
| 2 | `rebalancing_orchestrator.py` | `application/portfolio/` | `portfolio/rebalancing/orchestrator.py` | portfolio | MEDIUM |
| 3 | `portfolio_analysis_service.py` | `application/portfolio/services/` | `portfolio/services/analysis_service.py` | portfolio | MEDIUM |
| 4 | `portfolio_rebalancing_service.py` | `application/portfolio/services/` | `portfolio/services/rebalancing_service.py` | portfolio | MEDIUM |
| 5 | `rebalance_execution_service.py` | `application/portfolio/services/` | `portfolio/services/execution_service.py` | portfolio | MEDIUM |
| 6 | `trading_repository.py` | `domain/interfaces/` | `shared/interfaces/trading_repository.py` | shared | MEDIUM |
| 7 | `asset_info.py` | `domain/math/` | `shared/math/asset_info.py` | shared | LOW |
| 8 | `indicator_utils.py` | `domain/math/` | `strategy/indicators/utils.py` | strategy | LOW |
| 9 | `indicators.py` | `domain/math/` | `strategy/indicators/math_indicators.py` | strategy | LOW |
| 10 | `market_timing_utils.py` | `domain/math/` | `strategy/timing/market_timing_utils.py` | strategy | LOW |
| 11 | `math_utils.py` | `domain/math/` | `shared/math/math_utils.py` | shared | LOW |
| 12 | `trading_math.py` | `domain/math/` | `shared/math/trading_math.py` | shared | LOW |
| 13 | `base_policy.py` | `domain/policies/` | `portfolio/policies/base_policy.py` | portfolio | MEDIUM |
| 14 | `buying_power_policy.py` | `domain/policies/` | `portfolio/policies/buying_power_policy.py` | portfolio | MEDIUM |
| 15 | `fractionability_policy.py` | `domain/policies/` | `portfolio/policies/fractionability_policy.py` | portfolio | MEDIUM |

## Migration Strategy

### Phase A: Application Layer Services (Files 1-5)
- Migrate portfolio application services to proper portfolio/ module locations
- Update service registrations and dependency injection

### Phase B: Domain Interfaces & Math (Files 6-12)  
- Move domain interfaces to shared/interfaces/
- Migrate math utilities to appropriate business units (shared/math/ vs strategy/)

### Phase C: Domain Policies (Files 13-15)
- Move policy implementations to portfolio/policies/
- Maintain existing policy interfaces

## Expected Import Updates
- Estimated 10-15 import statements to update
- Focus on application layer consumers and service registrations
- Update module exports in __init__.py files

## Success Criteria
- All 15 files moved to target locations
- Zero syntax errors after import updates
- All import consumers updated to new paths
- Module boundaries respected per business unit guidelines