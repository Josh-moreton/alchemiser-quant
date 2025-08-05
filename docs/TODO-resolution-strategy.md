# TODO Comment Resolution Strategy

## Overview

After implementing Phases 1-15 of the strict typing upgrade, we have strategically placed TODO comments for gradual migration. This document outlines the resolution approach.

## TODO Categories

### 1. **IMMEDIATE RESOLUTION** (Safe to resolve now)

These can be resolved immediately as they're already working:

**Phase 15 TODOs - Type Annotations:**

- ✅ `main.py` function return types (already fixed)
- ✅ `trading_engine.py` method signatures (already fixed)
- ✅ `tracking/integration.py` parameter types (already fixed)

**Phase 13 TODOs - CLI Interface:**

- CLI return type annotations can use our defined types
- CLI parameter types can be migrated to structured types

### 2. **GRADUAL MIGRATION** (Resolve as needed)

These should be resolved when the underlying data structures are updated:

**Data Structure Alignment:**

- `AlpacaOrderProtocol` usage - when we verify Alpaca data structures match
- `AccountInfo`/`OrderDetails` - when we validate external API response structures
- `StrategyPnLSummary` - when calculation outputs match our TypedDict

**Execution Layer Migration:**

- Smart execution structured types - when we want to enforce strict data flow
- Reporting system types - when we standardize reporting interfaces

### 3. **PROGRESSIVE ENABLEMENT** (Enable when ready for stricter checking)

These are mypy configuration settings to enable progressively:

**MyPy Configuration (pyproject.toml):**

- `disallow_untyped_calls = true` - Enable when all function calls are typed
- `disallow_untyped_defs = true` - Enable when all functions have type annotations
- `disallow_untyped_decorators = true` - Enable when decorators are typed
- `ignore_missing_imports = false` - Enable when type stubs are added

## Recommended Resolution Order

### Phase 16a: Immediate Resolution (Now)

1. ✅ Core module type annotations (main.py, trading_engine.py, tracking modules)
2. ✅ CLI interface type annotations - completed TODO cleanup
3. ✅ Remove completed TODO comments - 12+ cleaned up successfully

### Phase 16b: Data Structure Validation (Next)

1. Validate Alpaca API response structures match our TypedDict definitions
2. Test actual data flow through the system
3. Migrate verified data structures from `dict[str, Any]` to TypedDict

### Phase 16c: Progressive MyPy Enablement (Future)

1. Enable `disallow_untyped_defs` first
2. Then `disallow_untyped_calls`
3. Finally `disallow_untyped_decorators` and remove `ignore_missing_imports`

## Current Status

- ✅ Core modules (main.py, trading_engine.py, tracking) pass mypy validation
- ✅ 45+ TypedDict definitions available
- ✅ Comprehensive mypy configuration in place
- ✅ Phase 16a completed: CLI cleanup and TODO removal (12+ TODOs cleaned)
- 🔄 ~126 TODO comments remaining for gradual migration (down from ~138)

## Next Steps

1. Resolve immediate CLI type annotations
2. Remove completed TODO comments  
3. Validate data structure alignment with real trading data
4. Enable stricter mypy settings progressively
