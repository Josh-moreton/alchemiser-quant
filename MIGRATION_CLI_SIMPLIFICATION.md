# CLI Simplification Migration Guide

## Overview

As part of reducing maintenance burden and streamlining the user experience, the following CLI commands have been removed:

- `alchemiser signal` - Signal analysis mode
- `alchemiser dsl-count` - DSL strategy parsing
- `alchemiser validate-indicators` - Technical indicator validation

## Migration Path

### Signal Analysis → Trade Command

**Before:**
```bash
# Separate signal analysis
alchemiser signal
```

**After:**
```bash
# Trading execution includes integrated signal analysis
alchemiser trade
```

**What changed:**
- Signal analysis is now integrated into the trading workflow
- The standalone `signal` command has been removed
- All signal generation functionality remains available through `trade` command
- Use `alchemiser trade --show-tracking` for enhanced performance data

### DSL Functionality → Removed

**Before:**
```bash
# DSL strategy parsing
alchemiser dsl-count strategy.clj
```

**After:**
DSL functionality has been completely removed as part of the migration to `strategy_v2` architecture. 

**What changed:**
- DSL (Domain Specific Language) support has been fully removed
- All strategies now use the modern `strategy_v2` Python-based system
- No migration path available - strategies must be rewritten using the new system

### Indicator Validation → Standard Testing

**Before:**
```bash
# Live API validation
alchemiser validate-indicators --mode core
```

**After:**
Technical indicators are now validated through standard unit tests in the codebase.

**What changed:**
- Live API validation against TwelveData has been removed
- Indicator accuracy is now verified through comprehensive unit tests
- No manual validation command needed

## Updated Commands

The streamlined CLI now supports:

```bash
# Core trading functionality
alchemiser trade              # Execute trading with integrated signal analysis
alchemiser status            # Show account status and positions

# System management  
alchemiser deploy            # Deploy to AWS Lambda
alchemiser version           # Show version information
```

## Updated Make Commands

**Before:**
```bash
make run-signals             # Show strategy signals (removed)
make run-trade              # Execute trading
```

**After:**
```bash
make run-trade              # Execute trading (includes signal analysis)
```

## Breaking Changes

1. **CLI Commands Removed:**
   - `alchemiser signal` - returns "No such command 'signal'"
   - `alchemiser dsl-count` - returns "No such command 'dsl-count'"  
   - `alchemiser validate-indicators` - returns "No such command 'validate-indicators'"

2. **Make Targets Removed:**
   - `make run-signals` - returns "No rule to make target 'run-signals'"

3. **Main Entry Point:**
   - `main.py` no longer accepts `signal` mode
   - Only `trade` mode is supported

## Benefits

- **Reduced Surface Area:** Fewer commands to maintain and document
- **Streamlined Workflow:** Single `trade` command handles all functionality  
- **Lower Cognitive Load:** Clearer, more focused CLI interface
- **Faster Onboarding:** Fewer concepts for new users to learn

## Support

If you have scripts or automation that used the removed commands:

1. **For signal analysis:** Replace `alchemiser signal` with `alchemiser trade`
2. **For DSL strategies:** Migrate to the new `strategy_v2` Python system
3. **For indicator validation:** Rely on the comprehensive unit test suite

For questions or assistance with migration, please refer to the main documentation or open an issue.