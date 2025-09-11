# Business Units Report

This document tracks files by business unit as defined in the modular architecture.

## Business Unit: execution

### Status: current

**New execution_v2 module (recommended):**
- `the_alchemiser/execution_v2/__init__.py` - Main module exports
- `the_alchemiser/execution_v2/core/__init__.py` - Core components exports  
- `the_alchemiser/execution_v2/core/execution_manager.py` - Simple execution manager with factory
- `the_alchemiser/execution_v2/core/simple_executor.py` - Core DTO-driven executor
- `the_alchemiser/execution_v2/core/execution_tracker.py` - Execution logging and monitoring
- `the_alchemiser/execution_v2/models/__init__.py` - Models exports
- `the_alchemiser/execution_v2/models/execution_result.py` - Execution result DTOs

**Legacy execution module (deprecated):**
- `the_alchemiser/execution/README_DEPRECATED.md` - Deprecation notice and migration guide
- `the_alchemiser/execution/...` - Legacy execution files (see README_DEPRECATED.md)

## Business Unit: portfolio

### Status: current
- Portfolio module files (to be documented)

## Business Unit: strategy  

### Status: current
- Strategy module files (to be documented)

## Business Unit: shared

### Status: current
- Shared module files (to be documented)

---

**Note**: This report should be updated when adding/removing files to maintain consistency with the modular architecture. New execution_v2 module follows strict DTO consumption principles and clean module boundaries.