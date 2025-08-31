# AUDIT: Complete Legacy Code Migration to DDD Bounded Context Architecture

## Overview
This issue addresses the need to audit the existing codebase in the repository **Josh-moreton/alchemiser-quant** for legacy folders and migrate everything to a new **Domain-Driven Design (DDD)** bounded context structure.

## Scope of Audit
1. **Legacy Folders to Review**:
   - `application`
   - `domain`
   - `infrastructure`
   - `interfaces`

2. **New Bounded Context Structure**:
   - `strategy`
   - `portfolio`
   - `execution`
   - `shared_kernel`
   - `anti_corruption`

## Migration Strategy
The migration will involve:
- Scanning for legacy imports
- Identifying orphaned code
- Validating architecture compliance

## Specific Shell Commands
Below are the shell commands that will be useful during the audit and migration process:

### 1. Scan for Legacy Imports
```bash
grep -r 'legacy_import' ./the_alchemiser/
```

### 2. Identify Orphaned Code
```bash
find ./the_alchemiser -type f -name '*.js' ! -exec grep -q 'used_function' {} \; -print
```

### 3. Validate Architecture Compliance
```bash
# Assuming we have a script that checks for DDD compliance
./validate_dd_architecture.sh
```

## Success Criteria
To consider the DDD migration complete, the following criteria must be met:
1. All legacy code has been reviewed and either migrated or marked for deprecation.
2. The new bounded context structure is fully implemented and all components are functioning as intended.
3. Documentation is updated to reflect the changes made during the migration process.
4. All tests pass successfully, ensuring that the new architecture does not introduce regressions.

## Related Epic
This task is part of epic #375. Please refer to this epic for broader context and additional tasks related to the DDD migration.