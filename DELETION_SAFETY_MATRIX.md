# Legacy DDD Architecture Deletion Safety Matrix

## Quick Reference Guide

This matrix provides a quick reference for the safety level of deleting each category of legacy files identified in the audit.

## Safety Categories

### 🟢 **SAFE - Immediate Deletion (62 files)**

| Category | Count | Risk Level | Action | Verification |
|----------|-------|------------|--------|--------------|
| Empty `__init__.py` files | 45 | LOW | ✅ Delete immediately | Lint check |
| Orphaned config utilities | 12 | LOW | ✅ Delete immediately | Import test |
| Unused validation helpers | 5 | LOW | ✅ Delete immediately | Basic smoke test |

**Tools Available:**
- `scripts/delete_legacy_safe.py` - Automated safe deletion
- `scripts/rollback_legacy_deletions.py` - Emergency rollback

**Pre-flight Checks:**
- [x] No active imports found
- [x] No external references detected  
- [x] Tested on sample batch (10 files) ✅
- [x] Rollback procedure verified

### 🟡 **CAUTION - Migration Required (68 files)**

| Category | Count | Risk Level | Action | Timeline |
|----------|-------|------------|--------|----------|
| Core execution components | 15 | HIGH | 🔄 Migrate imports first | 2-3 weeks |
| Policy implementations | 20 | MEDIUM | 🔄 Update references | 1-2 weeks |
| Strategy adapters | 18 | MEDIUM | 🔄 Verify equivalents | 1-2 weeks |
| Configuration files | 15 | MEDIUM | 🔄 Check dependencies | 1 week |

**Critical Path Files (Block deletion until migrated):**
1. `application/trading/engine_service.py` - Core trading engine (2 imports)
2. `application/execution/smart_execution.py` - Smart order execution (6 imports)  
3. `application/tracking/strategy_order_tracker.py` - Order tracking (6 imports)

**Migration Process:**
1. Map all importers of legacy file
2. Update imports to new modular equivalents
3. Test functionality with new imports
4. Delete legacy file after verification

### 🔴 **HIGH RISK - Manual Investigation (177 files)**

| Category | Count | Risk Level | Action | Timeline |
|----------|-------|------------|--------|----------|
| Business logic w/o equivalents | 45 | HIGH | 🔍 Manual review | 4-6 weeks |
| Complex DDD infrastructure | 80 | HIGH | 🔍 Architecture review | 4-6 weeks |
| Unknown/unclear files | 52 | HIGH | 🔍 Code analysis | 2-4 weeks |

**Investigation Required:**
- Manual code review for business value
- Determine if logic exists in new modules  
- Extract any missing business logic
- Update architecture documentation

## File-Level Safety Assessment

### Application Layer

| File | Safety | Imports | Action | Notes |
|------|--------|---------|--------|-------|
| `application/__init__.py` | 🟢 SAFE | 0 | DELETE | Already deleted ✅ |
| `application/execution/execution_manager.py` | 🟡 MIGRATE | 3 | Update importers | Legacy shim |
| `application/execution/smart_execution.py` | 🟡 MIGRATE | 6 | Core execution logic | Critical path |
| `application/trading/engine_service.py` | 🟡 MIGRATE | 2 | Core trading engine | Critical path |
| `application/tracking/strategy_order_tracker.py` | 🟡 MIGRATE | 6 | Order tracking | Critical path |

### Domain Layer

| File | Safety | Imports | Action | Notes |
|------|--------|---------|--------|-------|
| `domain/__init__.py` | 🟢 SAFE | 0 | DELETE | Empty module |
| `domain/strategies/__init__.py` | 🟡 MIGRATE | 3 | Legacy shim | Update importers |
| `domain/math/indicators.py` | 🟡 MIGRATE | 5 | Legacy shim | Update importers |
| `domain/strategies_backup/` | 🔴 INVESTIGATE | ? | Manual review | Business logic |

### Infrastructure Layer

| File | Safety | Imports | Action | Notes |
|------|--------|---------|--------|-------|
| `infrastructure/__init__.py` | 🟢 SAFE | 0 | DELETE | Empty module |
| `infrastructure/config/` | 🟡 MIGRATE | Mixed | Review configs | Runtime dependencies |
| `infrastructure/dependency_injection/` | 🔴 INVESTIGATE | High | Architecture review | DDD infrastructure |

### Services Layer

| File | Safety | Imports | Action | Notes |
|------|--------|---------|--------|-------|
| `services/__init__.py` | 🟢 SAFE | 0 | DELETE | Empty module |
| `services/trading/trading_service_manager.py` | 🟡 MIGRATE | 2 | Legacy shim | Update importers |
| `services/repository/alpaca_manager.py` | 🟡 MIGRATE | 1 | Legacy shim | Update importers |

## Deletion Sequence

### Phase 1: Immediate Safe Deletions ✅
**Status**: 10/62 files deleted  
**Remaining**: 52 files  
**Risk**: LOW  
**Tool**: `scripts/delete_legacy_safe.py`

```bash
# Execute remaining safe deletions
python scripts/delete_legacy_safe.py --verify
```

### Phase 2: Import Migration (Priority Order)

1. **Week 1-2: Core Components**
   - CLI and main execution paths
   - Critical trading components
   - Order tracking systems

2. **Week 3-4: Supporting Components**  
   - Policy implementations
   - Strategy adapters
   - Configuration files

3. **Week 5-6: Legacy Shims**
   - Update all remaining import redirections
   - Remove compatibility shims
   - Clean up module aliases

### Phase 3: Manual Investigation

1. **Week 7-8: Business Logic Review**
   - Analyze `domain/strategies_backup/`
   - Extract missing calculations
   - Verify complete migration

2. **Week 9-10: Infrastructure Review**
   - DDD dependency injection
   - Complex adapter patterns
   - Protocol definitions

3. **Week 11-12: Final Cleanup**
   - Remove any remaining legacy files
   - Update documentation
   - Verify architectural boundaries

## Risk Mitigation Strategies

### Immediate Safeguards
- ✅ Comprehensive import analysis completed
- ✅ Automated safe deletion script tested  
- ✅ Rollback procedure verified
- ✅ Version control safety net in place

### Migration Safeguards
- 🔄 Branch-based development for all migrations
- 🔄 Incremental testing after each change
- 🔄 Automated verification scripts
- 🔄 Staged rollout with verification points

### Emergency Procedures
```bash
# Emergency rollback of safe deletions
python scripts/rollback_legacy_deletions.py

# Emergency rollback of specific migration
git checkout HEAD~1 -- path/to/file

# Complete emergency rollback
git reset --hard <baseline_commit>
```

## Success Metrics

### Quantitative Targets
- [x] 62 safe files identified for immediate deletion (20% of legacy)
- [ ] 52 remaining safe files deleted  
- [ ] 68 migration files processed (22% of legacy)
- [ ] <50 total legacy files remaining (83% reduction)

### Quality Gates
- [ ] Zero new test failures introduced
- [ ] Lint error count stable (±50 tolerance)
- [ ] CLI functionality maintained
- [ ] Core trading functionality verified

## Tools and Scripts

| Tool | Purpose | Status | Usage |
|------|---------|--------|-------|
| `enhanced_audit.py` | Comprehensive analysis | ✅ Complete | One-time analysis |
| `delete_legacy_safe.py` | Safe file deletion | ✅ Ready | Ongoing cleanup |
| `rollback_legacy_deletions.py` | Emergency rollback | ✅ Ready | Emergency use |
| `LEGACY_AUDIT_REPORT.md` | Detailed findings | ✅ Complete | Reference document |
| `deletion_plan.md` | Step-by-step plan | ✅ Complete | Implementation guide |

## Team Responsibilities

### Immediate Actions (Team Lead)
- [ ] Review and approve Phase 1 completion
- [ ] Assign migration tasks for Phase 2
- [ ] Set up monitoring for system health

### Development Team  
- [ ] Execute Phase 1 remaining deletions
- [ ] Begin systematic import migration
- [ ] Update team documentation

### Architecture Review
- [ ] Validate business logic preservation
- [ ] Review complex DDD infrastructure
- [ ] Approve final architectural boundaries

---

**Last Updated**: January 2025  
**Next Review**: After Phase 1 completion  
**Owner**: Architecture Team  
**Status**: Active Implementation