# Import Linter Violations - Sub-Issues Breakdown

This document outlines the specific GitHub issues that should be created to implement the Import Linter Violations Remediation Plan.

## Issue 1: [CRITICAL] Fix Shared → Execution_v2 Import Violations

**Priority**: Critical  
**Labels**: `priority: critical`, `type: architecture`, `module: shared`, `module: execution_v2`, `import-linter`  
**Estimated Points**: 8  
**Dependencies**: None (blocks all other issues)

### Description
Root cause violation where shared module imports upward to execution_v2, breaking foundational architecture and causing cascade violations.

### Violations
- `shared.config.service_providers` → `execution_v2.core.execution_manager` (l.10)
- `shared.config.service_providers` → `execution_v2.core.smart_execution_strategy` (l.11)
- `shared.utils.service_factory` → `execution_v2.core.execution_manager` (l.8)

### Solution
Restructure dependency injection to move execution service providers to execution_v2 module and use late binding in shared.

### Files to Modify
- `shared/config/service_providers.py`
- `shared/utils/service_factory.py`
- `execution_v2/config/execution_providers.py` (new)
- `shared/config/container.py`
- `orchestration/system.py`

### Success Criteria
- Zero shared → execution_v2 imports
- Strategy/Portfolio cascade violations auto-resolved
- Import linter broken contracts: 4 → 1-2

---

## Issue 2: [ARCHITECTURE] Implement Event-Driven Orchestration Patterns

**Priority**: High  
**Labels**: `type: architecture`, `module: orchestration`, `event-driven`, `import-linter`  
**Estimated Points**: 13  
**Dependencies**: Issue 1 (shared → execution_v2 fix)

### Description
Orchestration layer violates event-driven architecture by directly importing handlers and models from business modules instead of using proper event patterns.

### Violations
**Orchestration → Execution_v2:**
- `orchestration.event_driven_orchestrator` → `execution_v2.handlers` (l.87)
- `orchestration.trading_orchestrator` → `execution_v2.models.execution_result` (l.20)

**Orchestration → Strategy_v2:**
- `orchestration.signal_orchestrator` → `strategy_v2.engines.dsl.strategy_engine` (l.31)
- `orchestration.event_driven_orchestrator` → `strategy_v2.handlers` (l.89)

**Orchestration → Portfolio_v2:**
- `orchestration.event_driven_orchestrator` → `portfolio_v2.handlers` (l.88)
- `orchestration.portfolio_orchestrator` → `portfolio_v2` (l.21, l.270)

### Solution
- Create handler registry system in shared module
- Replace direct handler imports with registry pattern
- Replace model imports with shared DTOs
- Implement proper event-driven coordination

### Files to Modify
- `shared/registry/handler_registry.py` (new)
- `orchestration/event_driven_orchestrator.py`
- `orchestration/trading_orchestrator.py`
- `orchestration/signal_orchestrator.py`
- `orchestration/portfolio_orchestrator.py`
- Business module handlers (register at startup)

### Success Criteria
- Zero direct orchestration → business module imports
- Handler registry functional
- Event-driven patterns implemented
- All orchestration workflows operational

---

## Issue 3: [DOCS] Document Module Import Architecture and Rules

**Priority**: Medium  
**Labels**: `type: documentation`, `architecture`, `import-linter`  
**Estimated Points**: 3  
**Dependencies**: Issues 1 & 2 (implementation complete)

### Description
Create comprehensive documentation of intended module import architecture and resolve confusion about legitimate vs. violating imports.

### Key Documentation Needs
1. **Architecture Decision Record**: Document that business → shared imports are intended
2. **Import Rules Guide**: Clear guidelines for developers on allowed import patterns
3. **Module Boundaries**: Update README files in each module
4. **Import Linter Configuration**: Document current rules and any adjustments needed

### Deliverables
- `docs/architecture/module_import_rules.md`
- `docs/architecture/adr_business_shared_imports.md`
- Updated module README files
- Import linter configuration documentation
- Developer onboarding guide updates

### Success Criteria
- Clear documentation of intended architecture
- Team understanding of proper import patterns
- Reduced confusion about import violations

---

## Issue 4: [INVESTIGATION] Analyze Import Linter Layered Rule Behavior

**Priority**: Low  
**Labels**: `type: investigation`, `import-linter`, `configuration`  
**Estimated Points**: 2  
**Dependencies**: None (can run in parallel)

### Description
The import linter reports business → shared imports as violations under the "Event-driven layered architecture enforcement" contract, but these imports are explicitly allowed by the layered architecture rule. This needs investigation.

### Investigation Questions
1. Is the layered architecture rule correctly configured?
2. Why are allowed imports reported as violations?
3. Should the rule configuration be adjusted?
4. Is this an import linter bug or misunderstanding?

### Approach
1. Review import linter documentation for layered rules
2. Test simplified configurations to isolate behavior
3. Check if verbose output reveals rule conflicts
4. Consider alternative rule configurations

### Deliverables
- Investigation report with findings
- Recommendation for rule configuration changes (if any)
- Updated import linter configuration (if needed)

### Success Criteria
- Understanding of import linter behavior
- Correctly configured rules
- No false positive violations

---

## Implementation Sequence

### Phase 1: Critical Fix (Week 1)
- **Issue 1**: Fix shared → execution_v2 violations
- **Issue 4**: Investigate import linter rules (parallel)

### Phase 2: Architecture (Weeks 2-3)  
- **Issue 2**: Implement event-driven orchestration patterns

### Phase 3: Documentation (Week 4)
- **Issue 3**: Document architecture and rules
- Complete import linter configuration updates

## Resource Allocation

**Total Estimated Points**: 26  
**Total Time**: 3-4 weeks  
**Team Size**: 2-3 developers  

### Assignments (Suggested)
- **Senior Developer**: Issues 1 & 2 (critical architecture work)
- **Mid-Level Developer**: Issue 3 & 4 (documentation and investigation)
- **Code Review**: All developers review each other's work

## Success Metrics

### Immediate (Post Issue 1)
- Import linter broken contracts: 4 → 1-2
- Zero shared → execution_v2 violations
- Cascade violations auto-resolved

### Short-term (Post Issue 2)
- Clean orchestration architecture
- Event-driven patterns implemented
- Zero direct orchestration → business imports

### Long-term (Post Issues 3 & 4)
- Clear team understanding
- Properly configured import linter
- Comprehensive architecture documentation

## Communication Plan

1. **Kickoff Meeting**: Present full remediation plan to team
2. **Daily Standups**: Track progress on critical Issue 1
3. **Mid-Point Review**: Assess after Issue 1 completion
4. **Architecture Review**: Present new patterns after Issue 2
5. **Final Review**: Validate complete solution and documentation