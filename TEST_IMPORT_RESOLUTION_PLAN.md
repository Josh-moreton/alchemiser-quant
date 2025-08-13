# Test Import Error Resolution Plan

## Current Status (August 13, 2025)

### Progress Summary

- **Original Problem**: 130+ import errors across test suite
- **Current Status**: Successfully fixed major domain model tests and infrastructure tests
- **Key Achievement**: Replaced broken test files with working versions that match actual codebase structure

### Files Successfully Fixed ✅

1. **tests/unit/test_domain_models.py**
   - **Issue**: Testing non-existent classes (OrderRequest, PositionSide, TimeInForce, etc.)
   - **Solution**: Completely rewrote to test actual domain models (AccountModel, PositionModel, OrderModel)
   - **Result**: Clean imports, tests actual codebase structure
   - **Backup**: Original saved as `test_domain_models_broken.py`

2. **tests/unit/test_infrastructure_layer.py**
   - **Issue**: Testing non-existent infrastructure classes (AlpacaDataProvider, NewsDataProvider, EmailService, AWSClient)
   - **Solution**: Rewrote to test actual infrastructure components (SecretsManager, AlertService, DataProvider interface)
   - **Result**: Tests real infrastructure with proper mocking
   - **Backup**: Original saved as `test_infrastructure_layer_broken.py`

3. **tests/integration/test_end_to_end_workflows.py**
   - **Issue**: Missing imports for `time` and `APIError`
   - **Solution**: Added proper imports and organized import section
   - **Result**: All import errors resolved

### Files Partially Fixed 🔄

1. **tests/unit/test_interface_layer.py** - Manual edits made
2. **tests/property/test_property_based.py** - Manual edits made
3. **tests/unit/test_services_comprehensive.py** - Manual edits made
4. **tests/unit/test_trading_math.py** - Previously improved (43% coverage gain)

### Remaining Files to Address 📋

Based on last error count analysis:

1. **tests/regression/test_regression_suite.py** (5 errors)
2. **tests/unit/test_interface_layer.py** (3 errors remaining)
3. **tests/property/test_property_based.py** (some errors remaining)

## Root Cause Analysis

### Primary Issues Identified

1. **Architecture Mismatch**: Tests written for idealized domain models that don't exist in actual codebase
2. **Missing Enums**: Tests expect domain enums but actual enums are in `application.order_validation`
3. **Import Organization**: Inconsistent import patterns across test files
4. **Non-existent Classes**: Many tests import classes that were never implemented

### Actual vs Expected Domain Structure

- **Expected**: `domain.models.OrderRequest`, `domain.enums.OrderSide`
- **Actual**: `domain.models.OrderModel`, `application.order_validation.ValidatedOrderSide`
- **Pattern**: Domain models exist but with different names and locations

## Systematic Fix Strategy

### Phase 1: Import Error Resolution (IN PROGRESS)

- [x] Identify all F401, F403, F811, F821 errors using Ruff
- [x] Fix major files (domain_models, infrastructure_layer, end_to_end_workflows)
- [ ] Complete remaining files (regression_suite, interface_layer, property_based)
- [ ] Run comprehensive import validation

### Phase 2: Test Quality Enhancement

- [ ] Run test collection to ensure all tests can be imported
- [ ] Fix test failures due to architectural mismatches
- [ ] Ensure proper mocking of external dependencies
- [ ] Validate test coverage for actual domain models

### Phase 3: Test Hardening

- [ ] Add missing test cases for edge conditions
- [ ] Improve assertion quality and error messages
- [ ] Add performance tests for critical paths
- [ ] Validate test isolation and independence

## Technical Patterns Established

### Import Pattern for Domain Models

```python
# Import actual domain models
from the_alchemiser.domain.models import (
    AccountModel,
    PositionModel,
    OrderModel,
)

# Import actual enums from order validation
from the_alchemiser.application.order_validation import (
    ValidatedOrderSide as OrderSide,
    ValidatedOrderType as OrderType,
    OrderStatus,
)
```

### Test Structure Pattern

```python
class TestDomainModel:
    """Test actual domain model with real methods."""
    
    def test_model_creation_from_dict(self):
        """Test creation using actual TypedDict structures."""
        data = {...}  # Use actual TypedDict format
        model = DomainModel.from_dict(data)
        assert model.property == expected_value
```

### Infrastructure Test Pattern

```python
@patch('external.dependency')
def test_with_mocked_external(self, mock_dependency):
    """Test infrastructure with proper external mocking."""
    mock_dependency.return_value = expected_result
    # Test actual infrastructure classes
```

## Commands for Quick Resume

### Check Current Import Error Status

```bash
cd /Users/joshmoreton/GitHub/alchemiser-quant
poetry run ruff check tests/ --select F401,F403,F811,F821 --quiet | grep -v "^$" | grep -v "|" | cut -d: -f1 | sort | uniq -c | sort -nr
```

### Test Specific File

```bash
poetry run pytest tests/unit/test_domain_models.py -v
poetry run python -c "from tests.unit.test_domain_models import TestAccountModel; print('Import successful!')"
```

### Format and Lint

```bash
poetry run ruff format tests/
poetry run ruff check tests/ --fix
```

## Next Immediate Steps

1. **Fix Remaining Import Errors**
   - tests/regression/test_regression_suite.py (5 errors)
   - tests/property/test_property_based.py (property testing issues)
   - Any remaining undefined name errors

2. **Validate Test Collection**

   ```bash
   poetry run pytest --collect-only tests/
   ```

3. **Run Test Suite Validation**

   ```bash
   poetry run pytest tests/unit/test_domain_models.py -v
   poetry run pytest tests/unit/test_infrastructure_layer.py -v
   ```

4. **Continue to Next Test File**
   - After import resolution, return to systematic test improvement
   - Focus on test quality and coverage
   - Add missing test cases for edge conditions

## Key Files and Backups

### Working Files

- `tests/unit/test_domain_models.py` - ✅ Fixed
- `tests/unit/test_infrastructure_layer.py` - ✅ Fixed
- `tests/integration/test_end_to_end_workflows.py` - ✅ Fixed

### Backup Files (for reference)

- `tests/unit/test_domain_models_broken.py` - Original broken version
- `tests/unit/test_infrastructure_layer_broken.py` - Original broken version

### Branch Status

- **Current Branch**: `building-test-suite`
- **Pull Request**: #60 (Building-test-suite)
- **Base Branch**: `main`

## Notes for Return

- Trading error takes priority - handle that first
- Import error resolution is ~70% complete
- Foundation is solid - new test patterns work well
- Next phase should be quick once imports are clean
- Consider running full test suite after import resolution to identify functional test issues
