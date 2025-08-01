# Simplify Configuration Handling Action Plan

## Objective
Replace the current singleton configuration loader with a clearer, type-safe approach.

## Key Tasks
1. **Adopt Typed Settings**
   - Create a `Settings` dataclass or pydantic model representing configuration sections (`alpaca`, `trading`, etc.).
   - Provide default values within the model for easier validation.
2. **Remove Globals**
   - Eliminate the module-level `_global_config` variable.
   - Initialize a `Settings` instance in the CLI entry point and pass it to modules that require configuration.
3. **YAML Parsing Cleanup**
   - Simplify YAML parsing using `pydantic-settings` or `dataclasses-json` to load environment variables and files seamlessly.
4. **Testing**
   - Add unit tests for configuration parsing, ensuring environment overrides work correctly.
   - Mock environment variables in tests to validate precedence rules.
5. **Documentation**
   - Document the new configuration approach in `docs/configuration.md` with examples for local and production setups.

## Deliverables
- New `Settings` model and loader implementation.
- Updated modules to accept configuration objects explicitly.
- Comprehensive tests for configuration behavior.
- Documentation describing usage and migration steps.
