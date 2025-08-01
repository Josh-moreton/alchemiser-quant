# Modularization and Separation of Concerns Action Plan

## Objective
Break down monolithic modules and reduce coupling to improve maintainability and testability.

## Key Tasks
1. **Refactor `trading_engine.py`**
   - Extract account management functions into `account_service.py`.
   - Move reporting logic into a dedicated `reporting` module.
   - Isolate execution orchestration in a new `execution_manager.py`.
2. **Entry Point Cleanup**
   - Ensure logging configuration and side effects occur only under `if __name__ == '__main__':` in the CLI module.
   - Split large functions in `main.py` into smaller commands or helper classes.
3. **Decouple Imports**
   - Replace dynamic imports with explicit dependencies to avoid circular references.
   - Pass services as parameters instead of accessing globals.
4. **Document New Architecture**
   - Provide diagrams and a short README in the `execution` package explaining new module responsibilities.
5. **Regression Testing**
   - After each refactor step, run unit tests and perform manual smoke tests using `alchemiser bot` and `alchemiser trade` in paper mode.

## Deliverables
- New smaller modules under `the_alchemiser/execution/` and updated imports.
- Simplified `main.py` with reduced side effects.
- Updated documentation reflecting the module structure.
- Passing test suite demonstrating functional parity.
