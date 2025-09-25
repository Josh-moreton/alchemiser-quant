# Import Linter Violations Remediation Plan

**Status**: Investigation Complete  
**Created**: 2024-09-25  
**Priority**: Critical  

## Background

Our `poetry run lint-imports` check currently reports **4 broken contracts** and a large number of import violations across the codebase:

- **Shared module isolation** – broken (3 violations)
- **Strategy module isolation** – broken (1 violation)  
- **Portfolio module isolation** – broken (1 violation)
- **Event-driven layered architecture enforcement** – broken (100+ violations)

The violations represent unwanted coupling between modules that undermines the intended architecture and makes the system harder to maintain, test, and extend.

## Investigation Summary

**Files Analyzed**: 193  
**Dependencies**: 453  
**Root Cause**: Shared module importing upward to execution_v2 breaks foundational architecture  

### Key Findings

1. **Critical Violations** (Must Fix): Shared module imports execution_v2 directly
2. **Cascade Violations** (Auto-Fix): Strategy/Portfolio → Execution via shared.config
3. **Architecture Violations** (Refactor Needed): Orchestration direct imports  
4. **False Violations** (Ignore): Business modules importing from shared (allowed by layered architecture)

## Violation Categories

### Priority 1: CRITICAL - Shared → Execution_v2 (Root Cause)
**Impact**: Breaks foundational shared module isolation and cascades to other violations

**Violations**:
- `shared.config.service_providers` → `execution_v2.core.execution_manager` (l.10)
- `shared.config.service_providers` → `execution_v2.core.smart_execution_strategy` (l.11)
- `shared.utils.service_factory` → `execution_v2.core.execution_manager` (l.8)

**Root Cause**: Dependency injection system wires execution services directly in shared module

### Priority 2: CASCADE - Strategy/Portfolio → Execution_v2 (Indirect)
**Impact**: Caused by Priority 1 violations via shared.config.container path

**Violations**:
- `strategy_v2.handlers.signal_generation_handler` → `shared.config.container` → `execution_v2`
- `portfolio_v2.handlers.portfolio_analysis_handler` → `shared.config.container` → `execution_v2`

**Solution**: Automatically resolved when Priority 1 is fixed

### Priority 3: ARCHITECTURE - Orchestration → Business Modules
**Impact**: Violates event-driven architecture by directly importing handlers/models

**Violations**:
- `orchestration.event_driven_orchestrator` → `execution_v2.handlers` (l.87)
- `orchestration.trading_orchestrator` → `execution_v2.models.execution_result` (l.20)
- `orchestration.signal_orchestrator` → `strategy_v2.engines.dsl.strategy_engine` (l.31)
- Plus 3 more orchestration violations

**Solution**: Implement proper event-driven patterns and handler registry

### ~~Priority 4-7: Business → Shared~~ (False Violations - Ignore)
**Analysis**: These are legitimate imports allowed by layered architecture  
**Count**: 100+ reported violations  
**Decision**: NO ACTION NEEDED - business modules should import from shared

## Remediation Strategy

### Phase 1: Emergency Fix (Week 1) - Priority 1
**Goal**: Resolve critical shared → execution_v2 violations

**Approach**: Restructure dependency injection to avoid upward imports
- Move execution service providers to execution_v2 module
- Use factory pattern with late binding in shared module
- Wire services in orchestration layer during startup

**Files to Modify**:
- `shared/config/service_providers.py` - Remove execution imports
- `shared/utils/service_factory.py` - Remove execution imports  
- `execution_v2/config/execution_providers.py` - Create new providers
- `orchestration/system.py` - Update initialization

**Success Criteria**:
- [ ] Zero shared → execution_v2 imports
- [ ] Strategy/Portfolio isolation violations auto-resolved
- [ ] All DI functionality preserved

### Phase 2: Architecture Fix (Weeks 2-3) - Priority 3
**Goal**: Fix orchestration layer violations with proper event-driven patterns

**Approach**: Replace direct imports with handler registry and event bus
- Create handler registry in shared module
- Business modules register handlers at startup
- Orchestration uses registry instead of direct imports
- Replace model imports with shared DTOs

**Files to Modify**:
- `shared/registry/handler_registry.py` - Create new registry
- `orchestration/event_driven_orchestrator.py` - Use registry
- `orchestration/trading_orchestrator.py` - Replace model imports
- `orchestration/signal_orchestrator.py` - Use event bus
- Business module handlers - Register at startup

**Success Criteria**:
- [ ] Zero direct orchestration → business module imports
- [ ] Event-driven patterns properly implemented
- [ ] All orchestration workflows operational

### Phase 3: Documentation (Week 4)
**Goal**: Document intended architecture and resolve configuration confusion

**Tasks**:
- Update architecture documentation
- Clarify that business → shared imports are intended
- Investigate import linter layered rule behavior
- Create architecture decision records

## Resource Requirements

**Development Time**: 2-4 weeks  
**Priority**: Critical (Phase 1), High (Phase 2), Medium (Phase 3)  
**Testing**: Unit, integration, and end-to-end tests required  

## Success Metrics

### Immediate (Post Phase 1)
- [ ] 0 shared → execution_v2 violations  
- [ ] 2 fewer broken contracts
- [ ] All existing functionality preserved

### Short-term (Post Phase 2)
- [ ] Clean orchestration layer architecture
- [ ] Proper event-driven patterns implemented

### Long-term (Post Phase 3)  
- [ ] Clear architecture documentation
- [ ] Team confidence in module boundaries

## Implementation Issues

The following GitHub issues should be created to track implementation:

1. **[CRITICAL] Fix Shared → Execution_v2 Import Violations** (Priority 1)
2. **[ARCHITECTURE] Implement Event-Driven Orchestration Patterns** (Priority 3)  
3. **[DOCS] Document Module Import Architecture and Rules** (Phase 3)

Each issue should include:
- Detailed technical specifications
- File-by-file change requirements
- Testing requirements
- Definition of done

## Conclusion

This remediation plan addresses the root causes of import linter violations while preserving the intended modular architecture. The key insight is that most violations are either caused by a single critical issue (shared → execution_v2) or are false positives (business → shared imports are actually correct).

By focusing on the real violations and implementing proper architectural patterns, we can achieve clean module boundaries while maintaining system functionality and performance.