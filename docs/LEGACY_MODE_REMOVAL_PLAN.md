# Legacy Mode Removal Plan

## 🎯 **Objective: Simplify Codebase by Removing Legacy Mode**

### ✅ **DI Readiness Confirmed**

- Signal mode: ✅ Working perfectly in DI
- Trade mode: ✅ Working perfectly in DI  
- AccountService: ✅ Implements all required protocols
- Container: ✅ Provides all needed services
- Type safety: ✅ Full protocol compliance

### 📋 **Removal Checklist**

#### Phase 1: CLI Interface Cleanup ✅ COMPLETED

- [x] Remove `--legacy` flags from CLI commands
- [x] Remove `use_legacy` parameters from TradingSystem
- [x] Remove `use_legacy` from SignalAnalyzer  
- [x] Remove `use_legacy` from TradingExecutor
- [x] Update help text to remove legacy references

#### Phase 2: Core Component Cleanup ✅ COMPLETED

- [x] Remove legacy fallback logic from main.py
- [x] Remove legacy initialization paths from TradingEngine
- [x] Clean up SignalAnalyzer legacy code paths
- [x] Clean up TradingExecutor legacy code paths

#### Phase 3: Service Layer Cleanup 🚧 IN PROGRESS

- [ ] Remove legacy methods from AccountService
- [ ] Remove TradingServiceManager fallback logic
- [ ] Remove legacy data provider patterns

#### Phase 4: Documentation & Testing 🚧 PENDING

- [ ] Update README.md to remove legacy references
- [ ] Update copilot instructions
- [ ] Remove legacy-related tests
- [ ] Add comprehensive DI-only tests

### 🔥 **Files to Modify**

1. `main.py` - Remove legacy initialization
2. `interface/cli/signal_analyzer.py` - Remove use_legacy
3. `interface/cli/trading_executor.py` - Remove use_legacy  
4. `interface/cli/cli.py` - Remove --legacy flags
5. `application/trading_engine.py` - Remove legacy paths
6. `services/enhanced/account_service.py` - Remove legacy methods

### ⚡ **Benefits After Removal**

- 🎯 **Simplified Architecture**: Single, clean code path
- 🛠️ **Easier Maintenance**: No dual-mode complexity
- 🧪 **Better Testing**: Focus on one implementation  
- 📚 **Clear Documentation**: No confusing mode options
- 🚀 **Production Focus**: DI-first approach aligns with modern practices

### 🚨 **Risk Mitigation**

- All functionality verified working in DI mode
- Changes will be in version control for easy rollback
- Comprehensive testing before deployment

**Status: READY TO PROCEED** ✅
